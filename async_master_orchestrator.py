"""
Async Master Orchestrator with Event-Driven Architecture
Coordinates all agents using asynchronous message passing
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from async_agent_base import AsyncAgentBase
from message_queue import InMemoryMessageQueue, TimeoutHandler
from message_schemas import (
    MessageHeader, MessagePriority, MessageType, AgentType,
    VehicleDataMessage, AnalysisRequestMessage
)
from channel_definitions import Channel


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AsyncMasterOrchestrator(AsyncAgentBase):
    """
    Master Orchestrator using async message passing
    Subscribes to all agent output channels and coordinates workflow
    """
    
    def __init__(
        self,
        message_queue: InMemoryMessageQueue,
        timeout_handler: TimeoutHandler
    ):
        super().__init__(
            agent_name="master_orchestrator",
            agent_type="master_orchestrator",
            message_queue=message_queue,
            timeout_handler=timeout_handler,
            default_timeout=30
        )
        
        # Workflow state tracking
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        
        # Register message type handlers
        self.register_message_handler(
            MessageType.VEHICLE_DATA.value,
            self._handle_vehicle_data
        )
        self.register_message_handler(
            MessageType.ANALYSIS_RESULT.value,
            self._handle_analysis_result
        )
        self.register_message_handler(
            MessageType.CUSTOMER_ENGAGEMENT_RESULT.value,
            self._handle_engagement_result
        )
        self.register_message_handler(
            MessageType.SCHEDULING_RESULT.value,
            self._handle_scheduling_result
        )
        self.register_message_handler(
            MessageType.FEEDBACK.value,
            self._handle_feedback
        )
        self.register_message_handler(
            MessageType.TIMEOUT.value,
            self._handle_timeout_escalation
        )
    
    async def process_message(self, message: Dict[str, Any]):
        """Process messages not handled by specific handlers"""
        header = message.get("header", {})
        logger.info(f"Orchestrator processing message type: {header.get('message_type')}")
    
    async def _handle_vehicle_data(self, message: Dict[str, Any]):
        """
        Handle incoming vehicle data
        Initiates the workflow by requesting data analysis
        """
        header = message.get("header", {})
        payload = message.get("payload", {})
        correlation_id = header.get("correlation_id")
        
        logger.info(f"Orchestrator received vehicle data, correlation_id: {correlation_id}")
        
        # Track workflow
        self.active_workflows[correlation_id] = {
            "start_time": datetime.utcnow().isoformat(),
            "current_stage": "data_analysis",
            "vehicle_id": payload.get("vehicle_id"),
            "customer_id": payload.get("customer_id"),
            "stages_completed": []
        }
        
        # Request data analysis
        await self.publish_message(
            channel=Channel.DATA_ANALYSIS_REQUEST.value,
            payload=payload,
            message_type=MessageType.ANALYSIS_REQUEST.value,
            receiver=AgentType.DATA_ANALYSIS.value,
            priority=MessagePriority.NORMAL.value,
            correlation_id=correlation_id,
            timeout=60
        )
        
        logger.info(f"Orchestrator requested data analysis for correlation_id: {correlation_id}")
    
    async def _handle_analysis_result(self, message: Dict[str, Any]):
        """
        Handle data analysis results
        Decides next action based on analysis outcome
        """
        header = message.get("header", {})
        payload = message.get("payload", {})
        correlation_id = header.get("correlation_id")
        
        logger.info(f"Orchestrator received analysis result, correlation_id: {correlation_id}")
        
        # Update workflow
        if correlation_id in self.active_workflows:
            workflow = self.active_workflows[correlation_id]
            workflow["stages_completed"].append("data_analysis")
            workflow["analysis_result"] = payload
            
            # Check if customer engagement is needed
            anomaly_detected = payload.get("anomaly_detected", False)
            failure_probability = payload.get("failure_probability", 0.0)
            
            if anomaly_detected or failure_probability > 0.3:
                # High priority if critical issue
                priority = MessagePriority.HIGH.value if failure_probability > 0.7 else MessagePriority.NORMAL.value
                
                workflow["current_stage"] = "customer_engagement"
                
                # Request customer engagement
                engagement_payload = {
                    "customer_id": workflow.get("customer_id"),
                    "vehicle_id": workflow.get("vehicle_id"),
                    "analysis_result": payload,
                    "message_content": self._generate_customer_message(payload),
                    "channel": "email"
                }
                
                await self.publish_message(
                    channel=Channel.CUSTOMER_ENGAGEMENT_REQUEST.value,
                    payload=engagement_payload,
                    message_type=MessageType.CUSTOMER_ENGAGEMENT.value,
                    receiver=AgentType.CUSTOMER_ENGAGEMENT.value,
                    priority=priority,
                    correlation_id=correlation_id,
                    timeout=30
                )
                
                logger.info(f"Orchestrator requested customer engagement for correlation_id: {correlation_id}")
            else:
                # No action needed, complete workflow
                workflow["current_stage"] = "completed"
                workflow["end_time"] = datetime.utcnow().isoformat()
                logger.info(f"Workflow {correlation_id} completed - no issues detected")
    
    async def _handle_engagement_result(self, message: Dict[str, Any]):
        """
        Handle customer engagement results
        Proceeds to scheduling if customer responded positively
        """
        header = message.get("header", {})
        payload = message.get("payload", {})
        correlation_id = header.get("correlation_id")
        
        logger.info(f"Orchestrator received engagement result, correlation_id: {correlation_id}")
        
        if correlation_id in self.active_workflows:
            workflow = self.active_workflows[correlation_id]
            workflow["stages_completed"].append("customer_engagement")
            workflow["engagement_result"] = payload
            
            # Check if scheduling is needed
            customer_response = payload.get("customer_response", "")
            
            if customer_response in ["accepted", "interested"]:
                workflow["current_stage"] = "scheduling"
                
                # Request scheduling
                scheduling_payload = {
                    "customer_id": workflow.get("customer_id"),
                    "vehicle_id": workflow.get("vehicle_id"),
                    "service_type": "diagnostic",
                    "urgency": "high" if workflow["analysis_result"].get("failure_probability", 0) > 0.7 else "normal",
                    "preferred_dates": payload.get("preferred_dates", [])
                }
                
                await self.publish_message(
                    channel=Channel.SCHEDULING_REQUEST.value,
                    payload=scheduling_payload,
                    message_type=MessageType.SCHEDULING_REQUEST.value,
                    receiver=AgentType.SCHEDULING.value,
                    priority=MessagePriority.NORMAL.value,
                    correlation_id=correlation_id,
                    timeout=45
                )
                
                logger.info(f"Orchestrator requested scheduling for correlation_id: {correlation_id}")
            else:
                # Customer declined, complete workflow
                workflow["current_stage"] = "completed"
                workflow["end_time"] = datetime.utcnow().isoformat()
                logger.info(f"Workflow {correlation_id} completed - customer declined")
    
    async def _handle_scheduling_result(self, message: Dict[str, Any]):
        """
        Handle scheduling results
        Completes the workflow
        """
        header = message.get("header", {})
        payload = message.get("payload", {})
        correlation_id = header.get("correlation_id")
        
        logger.info(f"Orchestrator received scheduling result, correlation_id: {correlation_id}")
        
        if correlation_id in self.active_workflows:
            workflow = self.active_workflows[correlation_id]
            workflow["stages_completed"].append("scheduling")
            workflow["scheduling_result"] = payload
            workflow["current_stage"] = "completed"
            workflow["end_time"] = datetime.utcnow().isoformat()
            
            logger.info(f"Workflow {correlation_id} completed successfully")
    
    async def _handle_feedback(self, message: Dict[str, Any]):
        """
        Handle customer feedback
        Generates manufacturing insights
        """
        header = message.get("header", {})
        payload = message.get("payload", {})
        correlation_id = header.get("correlation_id")
        
        logger.info(f"Orchestrator received feedback, correlation_id: {correlation_id}")
        
        # Process feedback and generate insights
        insights = self._generate_manufacturing_insights(payload)
        
        # Publish insights
        await self.publish_message(
            channel=Channel.MANUFACTURING_INSIGHTS.value,
            payload=insights,
            message_type=MessageType.MANUFACTURING_INSIGHT.value,
            receiver="manufacturing_system",
            priority=MessagePriority.LOW.value,
            correlation_id=correlation_id
        )
        
        logger.info(f"Orchestrator published manufacturing insights for correlation_id: {correlation_id}")
    
    async def _handle_timeout_escalation(self, message: Dict[str, Any]):
        """
        Handle timeout escalations from agents
        Implements retry logic or alternative actions
        """
        payload = message.get("payload", {})
        timed_out_message_id = payload.get("timed_out_message_id")
        agent = payload.get("agent")
        
        logger.warning(f"Timeout escalation from {agent} for message {timed_out_message_id}")
        
        # Implement retry logic here
        # For now, just log the timeout
    
    def _generate_customer_message(self, analysis_result: Dict[str, Any]) -> str:
        """Generate customer notification message based on analysis"""
        failure_probability = analysis_result.get("failure_probability", 0.0)
        predicted_failures = analysis_result.get("predicted_failures", [])
        
        if failure_probability > 0.7:
            return f"URGENT: Our analysis detected potential issues with your vehicle. Predicted failures: {', '.join(predicted_failures)}. Please schedule service immediately."
        elif failure_probability > 0.3:
            return f"Our analysis suggests your vehicle may need attention soon. Potential issues: {', '.join(predicted_failures)}. We recommend scheduling a service appointment."
        else:
            return "Your vehicle is performing well. No immediate action required."
    
    def _generate_manufacturing_insights(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Generate manufacturing insights from feedback"""
        return {
            "insight_type": "quality_improvement",
            "affected_components": feedback.get("components_mentioned", []),
            "recommendation": "Review manufacturing process for mentioned components",
            "feedback_summary": feedback.get("comments", ""),
            "severity": "medium"
        }
    
    def get_workflow_status(self, correlation_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a workflow"""
        return self.active_workflows.get(correlation_id)
    
    def get_all_workflows(self) -> Dict[str, Dict[str, Any]]:
        """Get all active workflows"""
        return self.active_workflows
