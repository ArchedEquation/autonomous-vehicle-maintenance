"""
Main Orchestration Loop
State machine-based orchestrator that coordinates all agents and handles complete workflow
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import requests
from collections import defaultdict

# Import all agents and modules
from async_master_orchestrator import AsyncMasterOrchestrator
from async_data_analysis_agent import AsyncDataAnalysisAgent
from async_customer_engagement_agent import AsyncCustomerEngagementAgent
from async_scheduling_agent import AsyncSchedulingAgent
from message_queue import InMemoryMessageQueue, TimeoutHandler
from message_schemas import MessageHeader, MessageType, MessagePriority, VehicleDataMessage
from channel_definitions import Channel
from ueba_monitor import UEBAMonitor
from ueba_integration import UEBAIntegration
from manufacturing_insights_module import ManufacturingInsightsModule, FailureSeverity
from manufacturing_api_integration import ManufacturingAPIClient


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkflowState(Enum):
    """Workflow states for vehicle processing"""
    IDLE = "idle"
    POLLING_TELEMETRY = "polling_telemetry"
    ANALYZING_DATA = "analyzing_data"
    ASSESSING_URGENCY = "assessing_urgency"
    ENGAGING_CUSTOMER = "engaging_customer"
    SCHEDULING_SERVICE = "scheduling_service"
    AWAITING_SERVICE = "awaiting_service"
    COLLECTING_FEEDBACK = "collecting_feedback"
    COMPLETED = "completed"
    ERROR = "error"


class UrgencyLevel(Enum):
    """Urgency levels for failure predictions"""
    CRITICAL = "critical"  # < 24 hours
    HIGH = "high"  # < 7 days
    MEDIUM = "medium"  # < 30 days
    LOW = "low"  # > 30 days


class VehicleWorkflow:
    """Tracks workflow state for a single vehicle"""
    
    def __init__(self, vin: str, vehicle_data: Dict[str, Any]):
        self.vin = vin
        self.vehicle_data = vehicle_data
        self.state = WorkflowState.IDLE
        self.correlation_id = None
        self.analysis_result = None
        self.urgency_level = None
        self.customer_response = None
        self.appointment = None
        self.feedback = None
        self.error_count = 0
        self.last_update = datetime.utcnow()
        self.state_history = []
        self.retry_count = 0
        self.max_retries = 3
    
    def transition_to(self, new_state: WorkflowState, reason: str = ""):
        """Transition to a new state"""
        old_state = self.state
        self.state = new_state
        self.last_update = datetime.utcnow()
        
        self.state_history.append({
            "from_state": old_state.value,
            "to_state": new_state.value,
            "timestamp": self.last_update.isoformat(),
            "reason": reason
        })
        
        logger.info(f"Vehicle {self.vin}: {old_state.value} → {new_state.value} ({reason})")
    
    def can_retry(self) -> bool:
        """Check if workflow can be retried"""
        return self.retry_count < self.max_retries
    
    def increment_retry(self):
        """Increment retry counter"""
        self.retry_count += 1



class MainOrchestrationLoop:
    """
    Main orchestration loop with state machine
    Coordinates all agents and handles complete workflow
    """
    
    def __init__(
        self,
        telematics_api_url: str = "http://localhost:8000",
        scheduler_api_url: str = "http://localhost:8001",
        polling_interval: int = 5
    ):
        self.telematics_api_url = telematics_api_url
        self.scheduler_api_url = scheduler_api_url
        self.polling_interval = polling_interval
        
        # Infrastructure
        self.message_queue = None
        self.timeout_handler = None
        
        # Agents
        self.master_orchestrator = None
        self.data_analysis_agent = None
        self.customer_engagement_agent = None
        self.scheduling_agent = None
        
        # Modules
        self.ueba_monitor = None
        self.ueba_integration = None
        self.manufacturing_insights = None
        self.manufacturing_api = None
        
        # Workflow tracking
        self.vehicle_workflows: Dict[str, VehicleWorkflow] = {}
        self.active_workflows: Dict[str, VehicleWorkflow] = {}
        self.completed_workflows: List[VehicleWorkflow] = []
        
        # Statistics
        self.stats = {
            "total_vehicles_processed": 0,
            "anomalies_detected": 0,
            "customers_engaged": 0,
            "appointments_scheduled": 0,
            "failures_prevented": 0,
            "errors_encountered": 0
        }
        
        # Running state
        self.is_running = False
        self._polling_task = None
        self._workflow_task = None
    
    async def initialize(self):
        """Initialize all components"""
        logger.info("="*80)
        logger.info("INITIALIZING MAIN ORCHESTRATION LOOP")
        logger.info("="*80)
        
        # Initialize message queue
        logger.info("Initializing message queue...")
        self.message_queue = InMemoryMessageQueue()
        self.timeout_handler = TimeoutHandler(default_timeout=30)
        await self.message_queue.start()
        
        # Initialize UEBA monitoring
        logger.info("Initializing UEBA monitoring...")
        self.ueba_monitor = UEBAMonitor(
            window_size_minutes=60,
            anomaly_threshold_std=3.0,
            auto_block_threshold=5
        )
        self.ueba_integration = UEBAIntegration(self.ueba_monitor, self.message_queue)
        await self.ueba_integration.start()
        
        # Initialize manufacturing insights
        logger.info("Initializing manufacturing insights...")
        self.manufacturing_insights = ManufacturingInsightsModule(
            urgent_failure_threshold=10,
            critical_failure_rate=0.05,
            batch_analysis_schedule="weekly"
        )
        await self.manufacturing_insights.start()
        
        # Initialize manufacturing API client
        self.manufacturing_api = ManufacturingAPIClient(
            api_base_url="https://manufacturing.example.com/api",
            webhook_url="https://manufacturing.example.com/webhook"
        )
        
        # Initialize agents
        logger.info("Initializing agents...")
        self.master_orchestrator = AsyncMasterOrchestrator(
            self.message_queue,
            self.timeout_handler
        )
        
        self.data_analysis_agent = AsyncDataAnalysisAgent(
            self.message_queue,
            self.timeout_handler
        )
        
        self.customer_engagement_agent = AsyncCustomerEngagementAgent(
            self.message_queue,
            self.timeout_handler
        )
        
        self.scheduling_agent = AsyncSchedulingAgent(
            self.message_queue,
            self.timeout_handler
        )
        
        # Start all agents
        logger.info("Starting all agents...")
        await self.master_orchestrator.start()
        await self.data_analysis_agent.start()
        await self.customer_engagement_agent.start()
        await self.scheduling_agent.start()
        
        logger.info("✓ All components initialized successfully")
    
    async def start(self):
        """Start the main orchestration loop"""
        if self.is_running:
            logger.warning("Orchestration loop already running")
            return
        
        self.is_running = True
        logger.info("="*80)
        logger.info("STARTING MAIN ORCHESTRATION LOOP")
        logger.info("="*80)
        
        # Start polling and workflow processing
        self._polling_task = asyncio.create_task(self._polling_loop())
        self._workflow_task = asyncio.create_task(self._workflow_processing_loop())
        
        logger.info("✓ Main orchestration loop started")
    
    async def stop(self):
        """Stop the main orchestration loop"""
        logger.info("Stopping main orchestration loop...")
        self.is_running = False
        
        # Cancel tasks
        if self._polling_task:
            self._polling_task.cancel()
        if self._workflow_task:
            self._workflow_task.cancel()
        
        # Stop all components (check if they exist first)
        if self.master_orchestrator:
            await self.master_orchestrator.stop()
        if self.data_analysis_agent:
            await self.data_analysis_agent.stop()
        if self.customer_engagement_agent:
            await self.customer_engagement_agent.stop()
        if self.scheduling_agent:
            await self.scheduling_agent.stop()
        if self.ueba_integration:
            await self.ueba_integration.stop()
        if self.manufacturing_insights:
            await self.manufacturing_insights.stop()
        if self.message_queue:
            await self.message_queue.stop()
        
        logger.info("✓ Main orchestration loop stopped")
    
    async def _polling_loop(self):
        """Continuously poll telematics API for vehicle data"""
        logger.info(f"Starting telemetry polling (interval: {self.polling_interval}s)")
        
        while self.is_running:
            try:
                # Poll all vehicles
                response = requests.get(
                    f"{self.telematics_api_url}/api/telemetry/all",
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    vehicles = data.get("vehicles", [])
                    
                    logger.info(f"Polled {len(vehicles)} vehicles")
                    
                    # Process each vehicle
                    for vehicle_data in vehicles:
                        await self._process_vehicle_data(vehicle_data)
                else:
                    logger.error(f"Telemetry API error: {response.status_code}")
                    self.stats["errors_encountered"] += 1
                
            except requests.exceptions.Timeout:
                logger.error("Telemetry API timeout")
                self.stats["errors_encountered"] += 1
            except requests.exceptions.ConnectionError:
                logger.error("Cannot connect to telemetry API")
                self.stats["errors_encountered"] += 1
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                self.stats["errors_encountered"] += 1
            
            # Wait for next poll
            await asyncio.sleep(self.polling_interval)
    
    async def _process_vehicle_data(self, vehicle_data: Dict[str, Any]):
        """Process vehicle data packet"""
        vin = vehicle_data.get("vin")
        telemetry = vehicle_data.get("telemetry", {})
        
        if not vin:
            return
        
        # Get or create workflow
        if vin not in self.vehicle_workflows:
            self.vehicle_workflows[vin] = VehicleWorkflow(vin, vehicle_data)
            self.stats["total_vehicles_processed"] += 1
        
        workflow = self.vehicle_workflows[vin]
        
        # Update vehicle data
        workflow.vehicle_data = vehicle_data
        
        # Only process if workflow is idle or completed
        if workflow.state in [WorkflowState.IDLE, WorkflowState.COMPLETED]:
            # Generate correlation ID
            correlation_id = f"workflow-{vin}-{datetime.utcnow().timestamp()}"
            workflow.correlation_id = correlation_id
            
            # Transition to analyzing state
            workflow.transition_to(
                WorkflowState.ANALYZING_DATA,
                "New telemetry data received"
            )
            
            # Add to active workflows
            self.active_workflows[vin] = workflow
            
            # Send to data analysis agent
            await self.message_queue.publish(
                channel="channel.data_analysis.request",
                message={
                    "header": {
                        "message_id": f"msg-{datetime.utcnow().timestamp()}",
                        "correlation_id": correlation_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "sender": "main_orchestrator",
                        "receiver": "data_analysis_agent",
                        "message_type": "analysis_request",
                        "priority": 2
                    },
                    "payload": {
                        "vehicle_id": vin,
                        "telemetry": telemetry,
                        "model": vehicle_data.get("model", ""),
                        "customer_id": f"customer-{vin}"
                    }
                }
            )
            
            logger.info(f"Sent vehicle {vin} for analysis (correlation: {correlation_id})")
    
    async def _workflow_processing_loop(self):
        """Process active workflows and handle state transitions"""
        logger.info("Starting workflow processing loop")
        
        while self.is_running:
            try:
                # Process each active workflow
                workflows_to_remove = []
                
                for vin, workflow in list(self.active_workflows.items()):
                    try:
                        # Check for timeout
                        time_since_update = (datetime.utcnow() - workflow.last_update).total_seconds()
                        
                        if time_since_update > 300:  # 5 minute timeout
                            logger.warning(f"Workflow {vin} timed out in state {workflow.state.value}")
                            await self._handle_error(workflow, "Workflow timeout")
                            continue
                        
                        # Process based on current state
                        if workflow.state == WorkflowState.ANALYZING_DATA:
                            # Wait for analysis result (handled by message subscription)
                            pass
                        
                        elif workflow.state == WorkflowState.ASSESSING_URGENCY:
                            await self._assess_urgency(workflow)
                        
                        elif workflow.state == WorkflowState.ENGAGING_CUSTOMER:
                            # Wait for customer response (handled by message subscription)
                            pass
                        
                        elif workflow.state == WorkflowState.SCHEDULING_SERVICE:
                            # Wait for scheduling result (handled by message subscription)
                            pass
                        
                        elif workflow.state == WorkflowState.AWAITING_SERVICE:
                            # Check if service is complete (would need service completion notification)
                            pass
                        
                        elif workflow.state == WorkflowState.COLLECTING_FEEDBACK:
                            # Collect feedback (would need feedback collection logic)
                            pass
                        
                        elif workflow.state == WorkflowState.COMPLETED:
                            # Move to completed workflows
                            workflows_to_remove.append(vin)
                            self.completed_workflows.append(workflow)
                            logger.info(f"Workflow {vin} completed successfully")
                        
                        elif workflow.state == WorkflowState.ERROR:
                            # Handle error state
                            if workflow.can_retry():
                                logger.info(f"Retrying workflow {vin} (attempt {workflow.retry_count + 1})")
                                workflow.increment_retry()
                                workflow.transition_to(WorkflowState.IDLE, "Retry after error")
                                workflows_to_remove.append(vin)
                            else:
                                logger.error(f"Workflow {vin} failed after {workflow.max_retries} retries")
                                workflows_to_remove.append(vin)
                                self.completed_workflows.append(workflow)
                    
                    except Exception as e:
                        logger.error(f"Error processing workflow {vin}: {e}")
                        await self._handle_error(workflow, str(e))
                
                # Remove completed workflows
                for vin in workflows_to_remove:
                    if vin in self.active_workflows:
                        del self.active_workflows[vin]
                
            except Exception as e:
                logger.error(f"Error in workflow processing loop: {e}")
            
            # Process every second
            await asyncio.sleep(1)
    
    async def _assess_urgency(self, workflow: VehicleWorkflow):
        """Assess urgency level from analysis result"""
        if not workflow.analysis_result:
            return
        
        analysis = workflow.analysis_result
        failure_probability = analysis.get("failure_probability", 0.0)
        predicted_days = analysis.get("predicted_days_to_failure", 999)
        
        # Determine urgency level
        if predicted_days < 1:
            workflow.urgency_level = UrgencyLevel.CRITICAL
        elif predicted_days < 7:
            workflow.urgency_level = UrgencyLevel.HIGH
        elif predicted_days < 30:
            workflow.urgency_level = UrgencyLevel.MEDIUM
        else:
            workflow.urgency_level = UrgencyLevel.LOW
        
        logger.info(
            f"Vehicle {workflow.vin} urgency: {workflow.urgency_level.value} "
            f"(failure in {predicted_days} days, probability: {failure_probability:.2f})"
        )
        
        # Decide next action based on urgency
        if workflow.urgency_level in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
            # Immediate customer engagement
            workflow.transition_to(
                WorkflowState.ENGAGING_CUSTOMER,
                f"Urgent issue detected: {workflow.urgency_level.value}"
            )
            await self._handle_customer_engagement(workflow)
        
        elif workflow.urgency_level == UrgencyLevel.MEDIUM:
            # Queue for batch processing (still engage but lower priority)
            workflow.transition_to(
                WorkflowState.ENGAGING_CUSTOMER,
                "Medium priority issue - queued for engagement"
            )
            await self._handle_customer_engagement(workflow)
        
        else:
            # Low priority - just log and complete
            workflow.transition_to(
                WorkflowState.COMPLETED,
                "Low priority - no immediate action needed"
            )
            
            # Still feed to manufacturing insights
            await self._feed_to_manufacturing_insights(workflow)
    
    async def _handle_customer_engagement(self, workflow: VehicleWorkflow):
        """Handle customer engagement"""
        self.stats["customers_engaged"] += 1
        
        # Generate customer message
        message_content = self._generate_customer_message(workflow)
        
        # Determine priority
        if workflow.urgency_level == UrgencyLevel.CRITICAL:
            priority = 4  # CRITICAL
        elif workflow.urgency_level == UrgencyLevel.HIGH:
            priority = 3  # HIGH
        else:
            priority = 2  # NORMAL
        
        # Send engagement request
        await self.message_queue.publish(
            channel="channel.customer_engagement.request",
            message={
                "header": {
                    "message_id": f"msg-{datetime.utcnow().timestamp()}",
                    "correlation_id": workflow.correlation_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "sender": "main_orchestrator",
                    "receiver": "customer_engagement_agent",
                    "message_type": "customer_engagement",
                    "priority": priority
                },
                "payload": {
                    "customer_id": f"customer-{workflow.vin}",
                    "vehicle_id": workflow.vin,
                    "message_content": message_content,
                    "channel": "email",
                    "urgency": workflow.urgency_level.value,
                    "analysis_result": workflow.analysis_result
                }
            }
        )
        
        logger.info(f"Sent customer engagement request for {workflow.vin}")
    
    async def _handle_scheduling(self, workflow: VehicleWorkflow):
        """Handle appointment scheduling"""
        if not workflow.customer_response:
            return
        
        # Check if customer accepted
        decision = workflow.customer_response.get("decision", "declined")
        
        if decision != "accepted":
            workflow.transition_to(
                WorkflowState.COMPLETED,
                f"Customer {decision} service"
            )
            return
        
        # Customer accepted - schedule appointment
        workflow.transition_to(
            WorkflowState.SCHEDULING_SERVICE,
            "Customer accepted - scheduling service"
        )
        
        # Get preferred dates from customer response
        preferred_dates = workflow.customer_response.get("preferred_dates", [])
        
        # Send scheduling request
        await self.message_queue.publish(
            channel="channel.scheduling.request",
            message={
                "header": {
                    "message_id": f"msg-{datetime.utcnow().timestamp()}",
                    "correlation_id": workflow.correlation_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "sender": "main_orchestrator",
                    "receiver": "scheduling_agent",
                    "message_type": "scheduling_request",
                    "priority": 3 if workflow.urgency_level == UrgencyLevel.CRITICAL else 2
                },
                "payload": {
                    "customer_id": f"customer-{workflow.vin}",
                    "vehicle_id": workflow.vin,
                    "service_type": "diagnostic",
                    "urgency": workflow.urgency_level.value,
                    "preferred_dates": preferred_dates
                }
            }
        )
        
        logger.info(f"Sent scheduling request for {workflow.vin}")
    
    async def _handle_feedback(self, workflow: VehicleWorkflow):
        """Handle post-service feedback collection"""
        # In a real system, this would collect feedback from customer
        # For now, simulate feedback
        
        workflow.feedback = {
            "rating": 4,
            "comments": "Service was good",
            "components_mentioned": workflow.analysis_result.get("predicted_failures", [])
        }
        
        # Feed to manufacturing insights
        await self._feed_to_manufacturing_insights(workflow)
        
        workflow.transition_to(
            WorkflowState.COMPLETED,
            "Feedback collected"
        )
    
    async def _feed_to_manufacturing_insights(self, workflow: VehicleWorkflow):
        """Feed workflow data to manufacturing insights module"""
        if not workflow.analysis_result:
            return
        
        predicted_failures = workflow.analysis_result.get("predicted_failures", [])
        
        for failure in predicted_failures:
            # Extract component and failure mode
            component = failure.get("component", "unknown")
            failure_mode = failure.get("mode", "unknown")
            
            # Determine severity
            if workflow.urgency_level == UrgencyLevel.CRITICAL:
                severity = FailureSeverity.CRITICAL
            elif workflow.urgency_level == UrgencyLevel.HIGH:
                severity = FailureSeverity.HIGH
            elif workflow.urgency_level == UrgencyLevel.MEDIUM:
                severity = FailureSeverity.MEDIUM
            else:
                severity = FailureSeverity.LOW
            
            # Ingest failure data
            await self.manufacturing_insights.ingest_failure_data(
                vehicle_id=workflow.vin,
                vehicle_model=workflow.vehicle_data.get("model", "Unknown"),
                vehicle_year=workflow.vehicle_data.get("year", 2020),
                manufacturing_batch=f"BATCH-{workflow.vehicle_data.get('year', 2020)}",
                component=component,
                failure_mode=failure_mode,
                severity=severity,
                mileage=workflow.vehicle_data.get("telemetry", {}).get("odometer", 0),
                diagnosis_data=workflow.analysis_result,
                customer_feedback=workflow.feedback
            )
        
        logger.info(f"Fed {len(predicted_failures)} failures to manufacturing insights")
    
    async def _handle_error(self, workflow: VehicleWorkflow, error_message: str):
        """Handle workflow errors"""
        self.stats["errors_encountered"] += 1
        
        workflow.error_count += 1
        workflow.transition_to(
            WorkflowState.ERROR,
            f"Error: {error_message}"
        )
        
        logger.error(f"Workflow {workflow.vin} error: {error_message}")
        
        # Send error message
        await self.message_queue.publish(
            channel="channel.system.error",
            message={
                "header": {
                    "message_id": f"msg-{datetime.utcnow().timestamp()}",
                    "correlation_id": workflow.correlation_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "sender": "main_orchestrator",
                    "receiver": "system",
                    "message_type": "error",
                    "priority": 3
                },
                "payload": {
                    "error_type": "workflow_error",
                    "vehicle_id": workflow.vin,
                    "workflow_state": workflow.state.value,
                    "error_message": error_message,
                    "error_count": workflow.error_count
                }
            }
        )
    
    def _generate_customer_message(self, workflow: VehicleWorkflow) -> str:
        """Generate customer notification message"""
        analysis = workflow.analysis_result
        predicted_failures = analysis.get("predicted_failures", [])
        predicted_days = analysis.get("predicted_days_to_failure", 999)
        
        if workflow.urgency_level == UrgencyLevel.CRITICAL:
            return (
                f"URGENT: Our analysis detected critical issues with your vehicle. "
                f"Predicted failures: {', '.join([f['component'] for f in predicted_failures])}. "
                f"Please schedule service immediately (within 24 hours)."
            )
        elif workflow.urgency_level == UrgencyLevel.HIGH:
            return (
                f"IMPORTANT: Our analysis suggests your vehicle needs attention soon. "
                f"Potential issues: {', '.join([f['component'] for f in predicted_failures])}. "
                f"Estimated time to failure: {predicted_days} days. "
                f"We recommend scheduling service within the next week."
            )
        elif workflow.urgency_level == UrgencyLevel.MEDIUM:
            return (
                f"Your vehicle may need attention in the coming weeks. "
                f"Potential issues: {', '.join([f['component'] for f in predicted_failures])}. "
                f"We recommend scheduling a service appointment at your convenience."
            )
        else:
            return "Your vehicle is performing well. No immediate action required."
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get orchestration statistics"""
        return {
            "total_vehicles_processed": self.stats["total_vehicles_processed"],
            "active_workflows": len(self.active_workflows),
            "completed_workflows": len(self.completed_workflows),
            "anomalies_detected": self.stats["anomalies_detected"],
            "customers_engaged": self.stats["customers_engaged"],
            "appointments_scheduled": self.stats["appointments_scheduled"],
            "failures_prevented": self.stats["failures_prevented"],
            "errors_encountered": self.stats["errors_encountered"],
            "workflow_states": {
                state.value: sum(
                    1 for w in self.active_workflows.values() 
                    if w.state == state
                )
                for state in WorkflowState
            }
        }
    
    def get_workflow_status(self, vin: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific workflow"""
        workflow = self.vehicle_workflows.get(vin)
        
        if not workflow:
            return None
        
        return {
            "vin": vin,
            "state": workflow.state.value,
            "urgency_level": workflow.urgency_level.value if workflow.urgency_level else None,
            "correlation_id": workflow.correlation_id,
            "last_update": workflow.last_update.isoformat(),
            "retry_count": workflow.retry_count,
            "error_count": workflow.error_count,
            "state_history": workflow.state_history,
            "analysis_result": workflow.analysis_result,
            "customer_response": workflow.customer_response,
            "appointment": workflow.appointment
        }
