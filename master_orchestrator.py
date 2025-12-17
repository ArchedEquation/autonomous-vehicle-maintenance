"""
Master Orchestrator for Vehicle Maintenance Multi-Agent System
Manages workflow state machines, task queuing, and agent coordination
"""

import logging
import json
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from queue import PriorityQueue
from collections import defaultdict
import threading
import time


# Configure logging for UEBA monitoring
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orchestrator_audit.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('MasterOrchestrator')


class WorkflowState(Enum):
    """Vehicle maintenance workflow states"""
    PENDING = "pending"
    DATA_ANALYSIS = "data_analysis"
    DIAGNOSIS = "diagnosis"
    URGENCY_ASSESSMENT = "urgency_assessment"
    CUSTOMER_ENGAGEMENT = "customer_engagement"
    SCHEDULING = "scheduling"
    SCHEDULED = "scheduled"
    IN_SERVICE = "in_service"
    FEEDBACK = "feedback"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


class TaskPriority(Enum):
    """Task priority levels"""
    URGENT = 1      # Critical safety issues
    HIGH = 2        # Imminent failures
    SCHEDULED = 3   # Planned maintenance
    ROUTINE = 4     # Regular checks


class AgentType(Enum):
    """Available worker agents"""
    DATA_ANALYSIS = "data_analysis_agent"
    DIAGNOSIS = "diagnosis_agent"
    CUSTOMER_ENGAGEMENT = "customer_engagement_agent"
    SCHEDULING = "scheduling_agent"
    FEEDBACK = "feedback_agent"
    MANUFACTURING_QUALITY = "manufacturing_quality_agent"


@dataclass
class VehicleWorkflow:
    """Represents a single vehicle's maintenance workflow"""
    workflow_id: str
    vehicle_id: str
    state: WorkflowState
    priority: TaskPriority
    created_at: datetime
    updated_at: datetime
    telemetry_data: Dict[str, Any]
    analysis_results: Optional[Dict[str, Any]] = None
    diagnosis_results: Optional[Dict[str, Any]] = None
    urgency_score: Optional[float] = None
    customer_engagement_status: Optional[str] = None
    appointment_details: Optional[Dict[str, Any]] = None
    feedback_data: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    max_retries: int = 3
    error_log: List[str] = field(default_factory=list)
    agent_interactions: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary for logging"""
        data = asdict(self)
        data['state'] = self.state.value
        data['priority'] = self.priority.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data


@dataclass
class Task:
    """Represents a task in the queue"""
    priority: int
    workflow_id: str
    agent_type: AgentType
    payload: Dict[str, Any]
    created_at: datetime
    
    def __lt__(self, other):
        """Priority queue comparison"""
        return self.priority < other.priority


class MasterOrchestrator:
    """
    Master Orchestrator for Vehicle Maintenance Multi-Agent System
    
    Responsibilities:
    - Maintain state machines for vehicle workflows
    - Route telemetry data to appropriate agents
    - Manage prioritized task queues
    - Track workflow status
    - Implement retry logic and error handling
    - Log all interactions for UEBA monitoring
    - Make final scheduling decisions
    """
    
    def __init__(self, max_workers: int = 10):
        self.workflows: Dict[str, VehicleWorkflow] = {}
        self.task_queue = PriorityQueue()
        self.max_workers = max_workers
        self.active_tasks = 0
        self.lock = threading.Lock()
        
        # Agent registry - maps agent types to handler functions
        self.agent_handlers: Dict[AgentType, Callable] = {}
        
        # Workflow statistics
        self.stats = {
            'total_workflows': 0,
            'completed': 0,
            'failed': 0,
            'urgent_handled': 0,
            'average_completion_time': 0
        }
        
        # State transition rules
        self.state_transitions = {
            WorkflowState.PENDING: [WorkflowState.DATA_ANALYSIS],
            WorkflowState.DATA_ANALYSIS: [WorkflowState.DIAGNOSIS, WorkflowState.FAILED],
            WorkflowState.DIAGNOSIS: [WorkflowState.URGENCY_ASSESSMENT, WorkflowState.FAILED],
            WorkflowState.URGENCY_ASSESSMENT: [WorkflowState.CUSTOMER_ENGAGEMENT, WorkflowState.FAILED],
            WorkflowState.CUSTOMER_ENGAGEMENT: [WorkflowState.SCHEDULING, WorkflowState.FAILED],
            WorkflowState.SCHEDULING: [WorkflowState.SCHEDULED, WorkflowState.FAILED],
            WorkflowState.SCHEDULED: [WorkflowState.IN_SERVICE],
            WorkflowState.IN_SERVICE: [WorkflowState.FEEDBACK],
            WorkflowState.FEEDBACK: [WorkflowState.COMPLETED, WorkflowState.FAILED],
            WorkflowState.FAILED: [WorkflowState.RETRY, WorkflowState.COMPLETED],
            WorkflowState.RETRY: [WorkflowState.DATA_ANALYSIS]
        }
        
        logger.info("Master Orchestrator initialized")
    
    def register_agent(self, agent_type: AgentType, handler: Callable):
        """Register a worker agent handler"""
        self.agent_handlers[agent_type] = handler
        logger.info(f"Registered agent: {agent_type.value}")
    
    def receive_vehicle_telemetry(self, vehicle_id: str, telemetry_data: Dict[str, Any]) -> str:
        """
        Entry point: Receive vehicle telemetry and initiate workflow
        
        Args:
            vehicle_id: Unique vehicle identifier
            telemetry_data: Raw sensor and diagnostic data
            
        Returns:
            workflow_id: Unique workflow identifier
        """
        workflow_id = str(uuid.uuid4())
        
        # Determine initial priority based on telemetry indicators
        priority = self._assess_initial_priority(telemetry_data)
        
        # Create workflow
        workflow = VehicleWorkflow(
            workflow_id=workflow_id,
            vehicle_id=vehicle_id,
            state=WorkflowState.PENDING,
            priority=priority,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            telemetry_data=telemetry_data
        )
        
        with self.lock:
            self.workflows[workflow_id] = workflow
            self.stats['total_workflows'] += 1
        
        # Log workflow creation
        self._log_interaction(workflow_id, "WORKFLOW_CREATED", {
            'vehicle_id': vehicle_id,
            'priority': priority.value,
            'telemetry_summary': self._summarize_telemetry(telemetry_data)
        })
        
        # Route to Data Analysis Agent
        self._route_to_data_analysis(workflow_id)
        
        logger.info(f"Created workflow {workflow_id} for vehicle {vehicle_id} with priority {priority.value}")
        
        return workflow_id
    
    def _assess_initial_priority(self, telemetry_data: Dict[str, Any]) -> TaskPriority:
        """Assess initial priority from telemetry data"""
        # Check for critical indicators
        critical_indicators = [
            telemetry_data.get('brake_failure', False),
            telemetry_data.get('engine_critical', False),
            telemetry_data.get('safety_system_fault', False)
        ]
        
        if any(critical_indicators):
            return TaskPriority.URGENT
        
        # Check for warning indicators
        warning_indicators = [
            telemetry_data.get('check_engine_light', False),
            telemetry_data.get('battery_low', False),
            telemetry_data.get('tire_pressure_low', False)
        ]
        
        if any(warning_indicators):
            return TaskPriority.HIGH
        
        # Check if scheduled maintenance is due
        if telemetry_data.get('maintenance_due', False):
            return TaskPriority.SCHEDULED
        
        return TaskPriority.ROUTINE
    
    def _summarize_telemetry(self, telemetry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of telemetry for logging"""
        return {
            'sensor_count': len(telemetry_data),
            'has_errors': any(k.endswith('_error') for k in telemetry_data.keys()),
            'timestamp': telemetry_data.get('timestamp', 'unknown')
        }
    
    def _route_to_data_analysis(self, workflow_id: str):
        """Route workflow to Data Analysis Agent"""
        workflow = self.workflows[workflow_id]
        
        # Transition state
        self._transition_state(workflow_id, WorkflowState.DATA_ANALYSIS)
        
        # Create task
        task = Task(
            priority=workflow.priority.value,
            workflow_id=workflow_id,
            agent_type=AgentType.DATA_ANALYSIS,
            payload={
                'vehicle_id': workflow.vehicle_id,
                'telemetry_data': workflow.telemetry_data
            },
            created_at=datetime.now()
        )
        
        self.task_queue.put(task)
        logger.info(f"Routed workflow {workflow_id} to Data Analysis Agent")
    
    def process_data_analysis_results(self, workflow_id: str, analysis_results: Dict[str, Any]):
        """
        Handle results from Data Analysis Agent
        Route to Diagnosis Agent
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            logger.error(f"Workflow {workflow_id} not found")
            return
        
        workflow.analysis_results = analysis_results
        workflow.updated_at = datetime.now()
        
        self._log_interaction(workflow_id, "DATA_ANALYSIS_COMPLETED", {
            'anomalies_detected': analysis_results.get('anomalies_detected', 0),
            'confidence_score': analysis_results.get('confidence_score', 0)
        })
        
        # Route to Diagnosis Agent
        self._route_to_diagnosis(workflow_id)
    
    def _route_to_diagnosis(self, workflow_id: str):
        """Route workflow to Diagnosis Agent"""
        workflow = self.workflows[workflow_id]
        
        self._transition_state(workflow_id, WorkflowState.DIAGNOSIS)
        
        task = Task(
            priority=workflow.priority.value,
            workflow_id=workflow_id,
            agent_type=AgentType.DIAGNOSIS,
            payload={
                'vehicle_id': workflow.vehicle_id,
                'analysis_results': workflow.analysis_results,
                'telemetry_data': workflow.telemetry_data
            },
            created_at=datetime.now()
        )
        
        self.task_queue.put(task)
        logger.info(f"Routed workflow {workflow_id} to Diagnosis Agent")
    
    def process_diagnosis_results(self, workflow_id: str, diagnosis_results: Dict[str, Any]):
        """
        Handle results from Diagnosis Agent
        Assess urgency and trigger appropriate actions
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            logger.error(f"Workflow {workflow_id} not found")
            return
        
        workflow.diagnosis_results = diagnosis_results
        workflow.updated_at = datetime.now()
        
        self._log_interaction(workflow_id, "DIAGNOSIS_COMPLETED", {
            'predicted_failures': diagnosis_results.get('predicted_failures', []),
            'failure_probability': diagnosis_results.get('failure_probability', 0)
        })
        
        # Assess urgency
        self._assess_urgency(workflow_id)
    
    def _assess_urgency(self, workflow_id: str):
        """
        Assess urgency and determine next action
        Critical: Immediate customer engagement
        Non-urgent: Queue for batch processing
        """
        workflow = self.workflows[workflow_id]
        
        self._transition_state(workflow_id, WorkflowState.URGENCY_ASSESSMENT)
        
        # Calculate urgency score
        diagnosis = workflow.diagnosis_results or {}
        failure_prob = diagnosis.get('failure_probability', 0)
        severity = diagnosis.get('severity_score', 0)
        time_to_failure = diagnosis.get('estimated_days_to_failure', 999)
        
        urgency_score = (failure_prob * 0.4 + severity * 0.4 + (1 / max(time_to_failure, 1)) * 0.2)
        workflow.urgency_score = urgency_score
        
        self._log_interaction(workflow_id, "URGENCY_ASSESSED", {
            'urgency_score': urgency_score,
            'failure_probability': failure_prob,
            'time_to_failure_days': time_to_failure
        })
        
        # Decision logic
        if urgency_score > 0.7 or workflow.priority == TaskPriority.URGENT:
            # Critical: Immediate action
            logger.warning(f"CRITICAL: Workflow {workflow_id} requires immediate attention")
            workflow.priority = TaskPriority.URGENT
            self.stats['urgent_handled'] += 1
            self._activate_customer_engagement_immediate(workflow_id)
        elif urgency_score > 0.4:
            # High priority: Fast track
            workflow.priority = TaskPriority.HIGH
            self._activate_customer_engagement_immediate(workflow_id)
        else:
            # Non-urgent: Queue for batch processing
            self._queue_for_batch_processing(workflow_id)
    
    def _activate_customer_engagement_immediate(self, workflow_id: str):
        """Activate Customer Engagement Agent immediately for critical/high priority"""
        workflow = self.workflows[workflow_id]
        
        self._transition_state(workflow_id, WorkflowState.CUSTOMER_ENGAGEMENT)
        
        task = Task(
            priority=workflow.priority.value,
            workflow_id=workflow_id,
            agent_type=AgentType.CUSTOMER_ENGAGEMENT,
            payload={
                'vehicle_id': workflow.vehicle_id,
                'diagnosis_results': workflow.diagnosis_results,
                'urgency_score': workflow.urgency_score,
                'immediate': True
            },
            created_at=datetime.now()
        )
        
        self.task_queue.put(task)
        logger.info(f"Activated immediate customer engagement for workflow {workflow_id}")
    
    def _queue_for_batch_processing(self, workflow_id: str):
        """Queue non-urgent workflows for batch processing"""
        workflow = self.workflows[workflow_id]
        
        # Schedule for batch processing (e.g., daily batch)
        task = Task(
            priority=TaskPriority.ROUTINE.value,
            workflow_id=workflow_id,
            agent_type=AgentType.CUSTOMER_ENGAGEMENT,
            payload={
                'vehicle_id': workflow.vehicle_id,
                'diagnosis_results': workflow.diagnosis_results,
                'urgency_score': workflow.urgency_score,
                'batch_mode': True
            },
            created_at=datetime.now()
        )
        
        self.task_queue.put(task)
        logger.info(f"Queued workflow {workflow_id} for batch processing")
    
    def process_customer_engagement_results(self, workflow_id: str, engagement_results: Dict[str, Any]):
        """
        Handle results from Customer Engagement Agent
        Route to Scheduling Agent
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            logger.error(f"Workflow {workflow_id} not found")
            return
        
        workflow.customer_engagement_status = engagement_results.get('status', 'unknown')
        workflow.updated_at = datetime.now()
        
        self._log_interaction(workflow_id, "CUSTOMER_ENGAGEMENT_COMPLETED", {
            'status': engagement_results.get('status'),
            'customer_response': engagement_results.get('customer_response'),
            'preferred_date': engagement_results.get('preferred_date')
        })
        
        # Route to Scheduling Agent
        self._activate_scheduling_agent(workflow_id, engagement_results)
    
    def _activate_scheduling_agent(self, workflow_id: str, engagement_results: Dict[str, Any]):
        """Activate Scheduling Agent"""
        workflow = self.workflows[workflow_id]
        
        self._transition_state(workflow_id, WorkflowState.SCHEDULING)
        
        task = Task(
            priority=workflow.priority.value,
            workflow_id=workflow_id,
            agent_type=AgentType.SCHEDULING,
            payload={
                'vehicle_id': workflow.vehicle_id,
                'diagnosis_results': workflow.diagnosis_results,
                'customer_preferences': engagement_results.get('customer_preferences', {}),
                'urgency_score': workflow.urgency_score
            },
            created_at=datetime.now()
        )
        
        self.task_queue.put(task)
        logger.info(f"Activated scheduling agent for workflow {workflow_id}")

    def make_scheduling_decision(self, workflow_id: str, scheduling_options: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Make final decision on service scheduling based on agent recommendations
        
        Args:
            workflow_id: Workflow identifier
            scheduling_options: List of scheduling options from Scheduling Agent
            
        Returns:
            Final scheduling decision
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            logger.error(f"Workflow {workflow_id} not found")
            return {}
        
        # Decision criteria
        urgency = workflow.urgency_score or 0
        priority = workflow.priority
        
        # Select best option based on urgency and availability
        best_option = None
        
        if priority == TaskPriority.URGENT:
            # For urgent: earliest available slot
            best_option = min(scheduling_options, key=lambda x: x.get('datetime', datetime.max))
        else:
            # For non-urgent: balance customer preference and service center load
            best_option = max(scheduling_options, key=lambda x: (
                x.get('customer_preference_score', 0) * 0.6 +
                (1 - x.get('service_center_load', 1)) * 0.4
            ))
        
        # Finalize appointment
        appointment = {
            'workflow_id': workflow_id,
            'vehicle_id': workflow.vehicle_id,
            'scheduled_datetime': best_option.get('datetime'),
            'service_center': best_option.get('service_center'),
            'estimated_duration': best_option.get('estimated_duration'),
            'services_required': workflow.diagnosis_results.get('recommended_services', []),
            'priority': priority.value,
            'urgency_score': urgency
        }
        
        workflow.appointment_details = appointment
        workflow.updated_at = datetime.now()
        
        self._transition_state(workflow_id, WorkflowState.SCHEDULED)
        
        self._log_interaction(workflow_id, "SCHEDULING_DECISION_MADE", appointment)
        
        logger.info(f"Scheduled appointment for workflow {workflow_id}: {appointment['scheduled_datetime']}")
        
        # Send to Manufacturing Quality Module for pattern analysis
        self._send_to_manufacturing_quality(workflow_id)
        
        return appointment
    
    def mark_service_in_progress(self, workflow_id: str):
        """Mark workflow as in service"""
        self._transition_state(workflow_id, WorkflowState.IN_SERVICE)
        self._log_interaction(workflow_id, "SERVICE_STARTED", {
            'timestamp': datetime.now().isoformat()
        })
    
    def mark_service_completed(self, workflow_id: str, service_results: Dict[str, Any]):
        """
        Mark service as completed and trigger Feedback Agent
        
        Args:
            workflow_id: Workflow identifier
            service_results: Results from service completion
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            logger.error(f"Workflow {workflow_id} not found")
            return
        
        workflow.updated_at = datetime.now()
        
        self._log_interaction(workflow_id, "SERVICE_COMPLETED", service_results)
        
        # Trigger Feedback Agent
        self._activate_feedback_agent(workflow_id, service_results)
    
    def _activate_feedback_agent(self, workflow_id: str, service_results: Dict[str, Any]):
        """Activate Feedback Agent post-service"""
        workflow = self.workflows[workflow_id]
        
        self._transition_state(workflow_id, WorkflowState.FEEDBACK)
        
        task = Task(
            priority=TaskPriority.ROUTINE.value,
            workflow_id=workflow_id,
            agent_type=AgentType.FEEDBACK,
            payload={
                'vehicle_id': workflow.vehicle_id,
                'service_results': service_results,
                'appointment_details': workflow.appointment_details
            },
            created_at=datetime.now()
        )
        
        self.task_queue.put(task)
        logger.info(f"Activated feedback agent for workflow {workflow_id}")
    
    def process_feedback_results(self, workflow_id: str, feedback_data: Dict[str, Any]):
        """
        Handle results from Feedback Agent
        Complete workflow
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            logger.error(f"Workflow {workflow_id} not found")
            return
        
        workflow.feedback_data = feedback_data
        workflow.updated_at = datetime.now()
        
        self._log_interaction(workflow_id, "FEEDBACK_COLLECTED", {
            'satisfaction_score': feedback_data.get('satisfaction_score'),
            'comments': feedback_data.get('comments', '')[:100]  # Truncate for logging
        })
        
        # Complete workflow
        self._complete_workflow(workflow_id)
    
    def _complete_workflow(self, workflow_id: str):
        """Mark workflow as completed"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return
        
        self._transition_state(workflow_id, WorkflowState.COMPLETED)
        
        # Calculate completion time
        completion_time = (workflow.updated_at - workflow.created_at).total_seconds() / 3600  # hours
        
        with self.lock:
            self.stats['completed'] += 1
            # Update average completion time
            total = self.stats['completed']
            current_avg = self.stats['average_completion_time']
            self.stats['average_completion_time'] = (current_avg * (total - 1) + completion_time) / total
        
        self._log_interaction(workflow_id, "WORKFLOW_COMPLETED", {
            'completion_time_hours': completion_time,
            'total_retries': workflow.retry_count
        })
        
        logger.info(f"Workflow {workflow_id} completed in {completion_time:.2f} hours")
    
    def _send_to_manufacturing_quality(self, workflow_id: str):
        """
        Continuously feed data to Manufacturing Quality Module
        for pattern analysis and quality improvement
        """
        workflow = self.workflows[workflow_id]
        
        task = Task(
            priority=TaskPriority.ROUTINE.value,
            workflow_id=workflow_id,
            agent_type=AgentType.MANUFACTURING_QUALITY,
            payload={
                'vehicle_id': workflow.vehicle_id,
                'telemetry_data': workflow.telemetry_data,
                'diagnosis_results': workflow.diagnosis_results,
                'analysis_results': workflow.analysis_results
            },
            created_at=datetime.now()
        )
        
        self.task_queue.put(task)
        logger.info(f"Sent workflow {workflow_id} data to Manufacturing Quality Module")
    
    def handle_agent_failure(self, workflow_id: str, agent_type: AgentType, error: Exception):
        """
        Handle agent failures with retry logic
        
        Args:
            workflow_id: Workflow identifier
            agent_type: Failed agent type
            error: Exception that occurred
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            logger.error(f"Workflow {workflow_id} not found")
            return
        
        error_msg = f"{agent_type.value} failed: {str(error)}"
        workflow.error_log.append(error_msg)
        workflow.retry_count += 1
        workflow.updated_at = datetime.now()
        
        self._log_interaction(workflow_id, "AGENT_FAILURE", {
            'agent_type': agent_type.value,
            'error': str(error),
            'retry_count': workflow.retry_count
        })
        
        logger.error(f"Agent failure in workflow {workflow_id}: {error_msg}")
        
        # Retry logic
        if workflow.retry_count < workflow.max_retries:
            # Transition to retry state
            self._transition_state(workflow_id, WorkflowState.RETRY)
            
            # Re-queue task with exponential backoff
            backoff_delay = 2 ** workflow.retry_count  # 2, 4, 8 seconds
            
            def retry_task():
                time.sleep(backoff_delay)
                self._retry_from_failure(workflow_id, agent_type)
            
            retry_thread = threading.Thread(target=retry_task)
            retry_thread.daemon = True
            retry_thread.start()
            
            logger.info(f"Scheduled retry {workflow.retry_count} for workflow {workflow_id} after {backoff_delay}s")
        else:
            # Max retries exceeded - mark as failed
            self._fail_workflow(workflow_id, f"Max retries exceeded for {agent_type.value}")
    
    def _retry_from_failure(self, workflow_id: str, failed_agent: AgentType):
        """Retry workflow from the point of failure"""
        workflow = self.workflows[workflow_id]
        
        # Determine retry strategy based on failed agent
        if failed_agent == AgentType.DATA_ANALYSIS:
            self._route_to_data_analysis(workflow_id)
        elif failed_agent == AgentType.DIAGNOSIS:
            self._route_to_diagnosis(workflow_id)
        elif failed_agent == AgentType.CUSTOMER_ENGAGEMENT:
            self._activate_customer_engagement_immediate(workflow_id)
        elif failed_agent == AgentType.SCHEDULING:
            self._activate_scheduling_agent(workflow_id, {})
        elif failed_agent == AgentType.FEEDBACK:
            self._activate_feedback_agent(workflow_id, {})
        
        logger.info(f"Retrying workflow {workflow_id} from {failed_agent.value}")
    
    def _fail_workflow(self, workflow_id: str, reason: str):
        """Mark workflow as permanently failed"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return
        
        self._transition_state(workflow_id, WorkflowState.FAILED)
        
        workflow.error_log.append(f"PERMANENT FAILURE: {reason}")
        
        with self.lock:
            self.stats['failed'] += 1
        
        self._log_interaction(workflow_id, "WORKFLOW_FAILED", {
            'reason': reason,
            'error_log': workflow.error_log
        })
        
        logger.error(f"Workflow {workflow_id} permanently failed: {reason}")
        
        # Trigger alert/notification system here
        self._trigger_failure_alert(workflow_id, reason)
    
    def _trigger_failure_alert(self, workflow_id: str, reason: str):
        """Trigger alert for workflow failure"""
        # Implementation would integrate with alerting system
        logger.critical(f"ALERT: Workflow {workflow_id} failed - {reason}")
    
    def _transition_state(self, workflow_id: str, new_state: WorkflowState) -> bool:
        """
        Transition workflow to new state with validation
        
        Args:
            workflow_id: Workflow identifier
            new_state: Target state
            
        Returns:
            True if transition successful, False otherwise
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            logger.error(f"Workflow {workflow_id} not found")
            return False
        
        current_state = workflow.state
        
        # Validate transition
        allowed_transitions = self.state_transitions.get(current_state, [])
        if new_state not in allowed_transitions:
            logger.warning(f"Invalid state transition: {current_state.value} -> {new_state.value}")
            return False
        
        # Perform transition
        workflow.state = new_state
        workflow.updated_at = datetime.now()
        
        self._log_interaction(workflow_id, "STATE_TRANSITION", {
            'from_state': current_state.value,
            'to_state': new_state.value
        })
        
        logger.info(f"Workflow {workflow_id} transitioned: {current_state.value} -> {new_state.value}")
        
        return True
    
    def _log_interaction(self, workflow_id: str, event_type: str, details: Dict[str, Any]):
        """
        Log all agent interactions for UEBA monitoring
        
        Args:
            workflow_id: Workflow identifier
            event_type: Type of event
            details: Event details
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return
        
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'workflow_id': workflow_id,
            'vehicle_id': workflow.vehicle_id,
            'event_type': event_type,
            'state': workflow.state.value,
            'priority': workflow.priority.value,
            'details': details
        }
        
        workflow.agent_interactions.append(interaction)
        
        # Log to audit file for UEBA
        logger.info(f"AUDIT: {json.dumps(interaction)}")
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None
        
        return {
            'workflow_id': workflow_id,
            'vehicle_id': workflow.vehicle_id,
            'state': workflow.state.value,
            'priority': workflow.priority.value,
            'urgency_score': workflow.urgency_score,
            'created_at': workflow.created_at.isoformat(),
            'updated_at': workflow.updated_at.isoformat(),
            'retry_count': workflow.retry_count,
            'has_errors': len(workflow.error_log) > 0,
            'appointment_scheduled': workflow.appointment_details is not None
        }
    
    def get_all_workflows_by_state(self, state: WorkflowState) -> List[Dict[str, Any]]:
        """Get all workflows in a specific state"""
        return [
            self.get_workflow_status(wf_id)
            for wf_id, wf in self.workflows.items()
            if wf.state == state
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        with self.lock:
            stats = self.stats.copy()
        
        # Add current state counts
        state_counts = defaultdict(int)
        for workflow in self.workflows.values():
            state_counts[workflow.state.value] += 1
        
        stats['workflows_by_state'] = dict(state_counts)
        stats['active_workflows'] = len(self.workflows)
        stats['queue_size'] = self.task_queue.qsize()
        
        return stats
    
    def process_task_queue(self):
        """
        Process tasks from the queue
        This should be run in a separate thread/process
        """
        while True:
            try:
                if not self.task_queue.empty():
                    task = self.task_queue.get(timeout=1)
                    
                    # Check if we have capacity
                    with self.lock:
                        if self.active_tasks >= self.max_workers:
                            # Re-queue task
                            self.task_queue.put(task)
                            time.sleep(0.1)
                            continue
                        self.active_tasks += 1
                    
                    # Process task in separate thread
                    thread = threading.Thread(target=self._execute_task, args=(task,))
                    thread.daemon = True
                    thread.start()
                else:
                    time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error processing task queue: {e}")
    
    def _execute_task(self, task: Task):
        """Execute a task by calling the appropriate agent handler"""
        try:
            handler = self.agent_handlers.get(task.agent_type)
            if not handler:
                raise Exception(f"No handler registered for {task.agent_type.value}")
            
            logger.info(f"Executing task for workflow {task.workflow_id} with agent {task.agent_type.value}")
            
            # Call agent handler
            result = handler(task.payload)
            
            # Route result to appropriate processor
            if task.agent_type == AgentType.DATA_ANALYSIS:
                self.process_data_analysis_results(task.workflow_id, result)
            elif task.agent_type == AgentType.DIAGNOSIS:
                self.process_diagnosis_results(task.workflow_id, result)
            elif task.agent_type == AgentType.CUSTOMER_ENGAGEMENT:
                self.process_customer_engagement_results(task.workflow_id, result)
            elif task.agent_type == AgentType.SCHEDULING:
                # Scheduling agent returns options, orchestrator makes decision
                self.make_scheduling_decision(task.workflow_id, result.get('options', []))
            elif task.agent_type == AgentType.FEEDBACK:
                self.process_feedback_results(task.workflow_id, result)
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            self.handle_agent_failure(task.workflow_id, task.agent_type, e)
        finally:
            with self.lock:
                self.active_tasks -= 1
    
    def start(self):
        """Start the orchestrator"""
        logger.info("Starting Master Orchestrator")
        
        # Start task queue processor
        processor_thread = threading.Thread(target=self.process_task_queue)
        processor_thread.daemon = True
        processor_thread.start()
        
        logger.info("Master Orchestrator started successfully")
    
    def shutdown(self):
        """Gracefully shutdown the orchestrator"""
        logger.info("Shutting down Master Orchestrator")
        
        # Wait for active tasks to complete
        while self.active_tasks > 0:
            logger.info(f"Waiting for {self.active_tasks} active tasks to complete...")
            time.sleep(1)
        
        # Log final statistics
        logger.info(f"Final statistics: {json.dumps(self.get_statistics(), indent=2)}")
        logger.info("Master Orchestrator shutdown complete")


# Example usage and integration
if __name__ == "__main__":
    # Initialize orchestrator
    orchestrator = MasterOrchestrator(max_workers=10)
    
    # Register mock agent handlers (replace with actual agent implementations)
    def mock_data_analysis_agent(payload):
        return {
            'anomalies_detected': 3,
            'confidence_score': 0.85,
            'sensor_readings': payload['telemetry_data']
        }
    
    def mock_diagnosis_agent(payload):
        return {
            'predicted_failures': ['brake_pad_wear', 'battery_degradation'],
            'failure_probability': 0.75,
            'severity_score': 0.6,
            'estimated_days_to_failure': 30,
            'recommended_services': ['brake_inspection', 'battery_test']
        }
    
    def mock_customer_engagement_agent(payload):
        return {
            'status': 'contacted',
            'customer_response': 'accepted',
            'preferred_date': (datetime.now() + timedelta(days=7)).isoformat(),
            'customer_preferences': {'preferred_time': 'morning'}
        }
    
    def mock_scheduling_agent(payload):
        return {
            'options': [
                {
                    'datetime': datetime.now() + timedelta(days=7),
                    'service_center': 'Center A',
                    'estimated_duration': 2,
                    'customer_preference_score': 0.9,
                    'service_center_load': 0.6
                },
                {
                    'datetime': datetime.now() + timedelta(days=10),
                    'service_center': 'Center B',
                    'estimated_duration': 2,
                    'customer_preference_score': 0.7,
                    'service_center_load': 0.3
                }
            ]
        }
    
    def mock_feedback_agent(payload):
        return {
            'satisfaction_score': 4.5,
            'comments': 'Great service!',
            'would_recommend': True
        }
    
    def mock_manufacturing_quality_agent(payload):
        return {'status': 'data_received'}
    
    # Register agents
    orchestrator.register_agent(AgentType.DATA_ANALYSIS, mock_data_analysis_agent)
    orchestrator.register_agent(AgentType.DIAGNOSIS, mock_diagnosis_agent)
    orchestrator.register_agent(AgentType.CUSTOMER_ENGAGEMENT, mock_customer_engagement_agent)
    orchestrator.register_agent(AgentType.SCHEDULING, mock_scheduling_agent)
    orchestrator.register_agent(AgentType.FEEDBACK, mock_feedback_agent)
    orchestrator.register_agent(AgentType.MANUFACTURING_QUALITY, mock_manufacturing_quality_agent)
    
    # Start orchestrator
    orchestrator.start()
    
    # Simulate vehicle telemetry
    telemetry = {
        'vehicle_id': 'VEH001',
        'timestamp': datetime.now().isoformat(),
        'engine_temp': 95,
        'brake_wear': 0.75,
        'battery_voltage': 11.8,
        'check_engine_light': True,
        'mileage': 45000
    }
    
    workflow_id = orchestrator.receive_vehicle_telemetry('VEH001', telemetry)
    
    print(f"Created workflow: {workflow_id}")
    print(f"Initial status: {orchestrator.get_workflow_status(workflow_id)}")
    
    # Let it run for a bit
    time.sleep(5)
    
    print(f"Statistics: {json.dumps(orchestrator.get_statistics(), indent=2)}")
