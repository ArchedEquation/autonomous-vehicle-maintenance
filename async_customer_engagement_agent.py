"""
Async Customer Engagement Agent
Handles customer communications asynchronously
"""
import asyncio
import logging
from typing import Dict, Any

from async_agent_base import AsyncAgentBase
from message_schemas import MessageType, MessagePriority, AgentType
from channel_definitions import Channel


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AsyncCustomerEngagementAgent(AsyncAgentBase):
    """
    Async Customer Engagement Agent
    Subscribes to engagement requests and publishes results
    """
    
    def __init__(self, message_queue, timeout_handler):
        super().__init__(
            agent_name="customer_engagement_agent",
            agent_type="customer_engagement_agent",
            message_queue=message_queue,
            timeout_handler=timeout_handler,
            default_timeout=30
        )
        
        # Register message handlers
        self.register_message_handler(
            MessageType.CUSTOMER_ENGAGEMENT.value,
            self._handle_engagement_request
        )
    
    async def process_message(self, message: Dict[str, Any]):
        """Process messages not handled by specific handlers"""
        header = message.get("header", {})
        logger.info(f"Customer Engagement Agent processing message type: {header.get('message_type')}")
    
    async def _handle_engagement_request(self, message: Dict[str, Any]):
        """
        Handle customer engagement request
        Sends notifications and tracks customer response
        """
        header = message.get("header", {})
        payload = message.get("payload", {})
        correlation_id = header.get("correlation_id")
        
        logger.info(f"Customer Engagement Agent processing request, correlation_id: {correlation_id}")
        
        # Simulate sending notification
        await asyncio.sleep(1)
        
        # Send notification
        notification_result = await self._send_customer_notification(payload)
        
        # Publish result
        await self.publish_message(
            channel=Channel.CUSTOMER_ENGAGEMENT_RESULT.value,
            payload=notification_result,
            message_type=MessageType.CUSTOMER_ENGAGEMENT.value,
            receiver=AgentType.MASTER_ORCHESTRATOR.value,
            priority=MessagePriority.NORMAL.value,
            correlation_id=correlation_id
        )
        
        logger.info(f"Customer Engagement Agent published result, correlation_id: {correlation_id}")
    
    async def _send_customer_notification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send notification to customer
        Simulates email/SMS sending
        """
        customer_id = data.get("customer_id")
        message_content = data.get("message_content")
        channel = data.get("channel", "email")
        
        logger.info(f"Sending {channel} to customer {customer_id}: {message_content}")
        
        # Simulate customer response (in real system, this would be async)
        customer_response = "accepted"  # Could be: accepted, declined, no_response
        
        return {
            "customer_id": customer_id,
            "notification_sent": True,
            "channel": channel,
            "customer_response": customer_response,
            "response_timestamp": "2024-01-15T10:30:00Z",
            "preferred_dates": ["2024-01-20", "2024-01-21"]
        }
