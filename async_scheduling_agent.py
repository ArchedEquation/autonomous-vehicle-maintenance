"""
Async Scheduling Agent
Handles appointment scheduling asynchronously
"""
import asyncio
import logging
from typing import Dict, Any
import random

from async_agent_base import AsyncAgentBase
from message_schemas import MessageType, MessagePriority, AgentType
from channel_definitions import Channel


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AsyncSchedulingAgent(AsyncAgentBase):
    """
    Async Scheduling Agent
    Subscribes to scheduling requests and publishes results
    """
    
    def __init__(self, message_queue, timeout_handler):
        super().__init__(
            agent_name="scheduling_agent",
            agent_type="scheduling_agent",
            message_queue=message_queue,
            timeout_handler=timeout_handler,
            default_timeout=45
        )
        
        # Register message handlers
        self.register_message_handler(
            MessageType.SCHEDULING_REQUEST.value,
            self._handle_scheduling_request
        )
    
    async def process_message(self, message: Dict[str, Any]):
        """Process messages not handled by specific handlers"""
        header = message.get("header", {})
        logger.info(f"Scheduling Agent processing message type: {header.get('message_type')}")
    
    async def _handle_scheduling_request(self, message: Dict[str, Any]):
        """
        Handle scheduling request
        Books appointment at service center
        """
        header = message.get("header", {})
        payload = message.get("payload", {})
        correlation_id = header.get("correlation_id")
        
        logger.info(f"Scheduling Agent processing request, correlation_id: {correlation_id}")
        
        # Simulate scheduling processing
        await asyncio.sleep(1.5)
        
        # Schedule appointment
        scheduling_result = await self._schedule_appointment(payload)
        
        # Publish result
        await self.publish_message(
            channel=Channel.SCHEDULING_RESULT.value,
            payload=scheduling_result,
            message_type=MessageType.SCHEDULING_RESULT.value,
            receiver=AgentType.MASTER_ORCHESTRATOR.value,
            priority=MessagePriority.NORMAL.value,
            correlation_id=correlation_id
        )
        
        logger.info(f"Scheduling Agent published result, correlation_id: {correlation_id}")
    
    async def _schedule_appointment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Schedule appointment at service center
        Simulates booking logic
        """
        customer_id = data.get("customer_id")
        vehicle_id = data.get("vehicle_id")
        service_type = data.get("service_type")
        urgency = data.get("urgency", "normal")
        preferred_dates = data.get("preferred_dates", [])
        
        # Select service center based on urgency
        service_centers = ["Center A", "Center B", "Center C"]
        selected_center = random.choice(service_centers)
        
        # Select date
        scheduled_date = preferred_dates[0] if preferred_dates else "2024-01-20"
        
        appointment_id = f"APT-{random.randint(10000, 99999)}"
        
        logger.info(f"Scheduled appointment {appointment_id} for customer {customer_id}")
        
        return {
            "appointment_id": appointment_id,
            "customer_id": customer_id,
            "vehicle_id": vehicle_id,
            "scheduled_date": scheduled_date,
            "service_center": selected_center,
            "service_type": service_type,
            "status": "confirmed",
            "urgency": urgency
        }
