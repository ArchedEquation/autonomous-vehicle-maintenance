"""
Async Agent Base Class for Event-Driven Architecture
All agents inherit from this base to support asynchronous message passing
"""
import asyncio
import logging
from typing import Dict, Any, Optional, Callable, List
from abc import ABC, abstractmethod

from message_queue import MessageQueue, TimeoutHandler
from message_schemas import (
    MessageHeader, MessagePriority, MessageType, AgentType,
    AcknowledgmentMessage, ErrorMessage
)
from channel_definitions import Channel, ChannelSubscriptions


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AsyncAgentBase(ABC):
    """
    Base class for all async agents in the system
    Provides message queue integration and timeout handling
    """
    
    def __init__(
        self,
        agent_name: str,
        agent_type: str,
        message_queue: MessageQueue,
        timeout_handler: TimeoutHandler,
        default_timeout: int = 30
    ):
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.message_queue = message_queue
        self.timeout_handler = timeout_handler
        self.default_timeout = default_timeout
        self.is_running = False
        self.message_handlers: Dict[str, Callable] = {}
        self.subscribed_channels: List[str] = []
        
        # Register default message handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default message type handlers"""
        self.message_handlers[MessageType.ERROR.value] = self._handle_error_message
        self.message_handlers[MessageType.ACK.value] = self._handle_ack_message
    
    async def start(self):
        """Start the agent and subscribe to channels"""
        self.is_running = True
        
        # Get channel subscriptions for this agent type
        channels = ChannelSubscriptions.get_subscriptions(self.agent_type)
        
        for channel in channels:
            await self.subscribe_to_channel(channel)
        
        logger.info(f"{self.agent_name} started and subscribed to {len(channels)} channels")
    
    async def stop(self):
        """Stop the agent and unsubscribe from channels"""
        self.is_running = False
        
        for channel in self.subscribed_channels:
            await self.message_queue.unsubscribe(channel, self._message_callback)
        
        logger.info(f"{self.agent_name} stopped")
    
    async def subscribe_to_channel(self, channel: str):
        """Subscribe to a message channel"""
        await self.message_queue.subscribe(channel, self._message_callback)
        self.subscribed_channels.append(channel)
        logger.info(f"{self.agent_name} subscribed to {channel}")
    
    async def _message_callback(self, message: Dict[str, Any]):
        """
        Internal callback for received messages
        Routes to appropriate handler based on message type
        """
        try:
            header = message.get("header", {})
            message_type = header.get("message_type")
            message_id = header.get("message_id")
            
            logger.info(f"{self.agent_name} received message {message_id} of type {message_type}")
            
            # Send acknowledgment
            await self._send_acknowledgment(message)
            
            # Route to appropriate handler
            if message_type in self.message_handlers:
                handler = self.message_handlers[message_type]
                await handler(message)
            else:
                # Call the agent's process_message method
                await self.process_message(message)
                
        except Exception as e:
            logger.error(f"{self.agent_name} error processing message: {e}")
            await self._send_error_message(message, str(e))
    
    @abstractmethod
    async def process_message(self, message: Dict[str, Any]):
        """
        Process incoming message - must be implemented by subclasses
        
        Args:
            message: Message dictionary with header and payload
        """
        pass
    
    async def publish_message(
        self,
        channel: str,
        payload: Dict[str, Any],
        message_type: str,
        receiver: str,
        priority: int = MessagePriority.NORMAL.value,
        correlation_id: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> str:
        """
        Publish a message to a channel
        
        Args:
            channel: Target channel
            payload: Message payload
            message_type: Type of message
            receiver: Intended receiver
            priority: Message priority
            correlation_id: Correlation ID for tracking workflow
            timeout: Timeout in seconds
            
        Returns:
            str: Message ID
        """
        # Create message header
        header = MessageHeader(
            sender=self.agent_name,
            receiver=receiver,
            message_type=message_type,
            priority=priority,
            correlation_id=correlation_id or ""
        )
        
        # Create full message
        message = {
            "header": header.to_dict(),
            "payload": payload
        }
        
        # Register for timeout tracking
        timeout_seconds = timeout or self.default_timeout
        await self.timeout_handler.register_message(
            header.message_id,
            timeout_seconds,
            self._handle_timeout
        )
        
        # Publish to queue
        success = await self.message_queue.publish(channel, message)
        
        if success:
            logger.info(f"{self.agent_name} published message {header.message_id} to {channel}")
        else:
            logger.error(f"{self.agent_name} failed to publish message to {channel}")
        
        return header.message_id
    
    async def _send_acknowledgment(self, original_message: Dict[str, Any]):
        """Send acknowledgment for received message"""
        header = original_message.get("header", {})
        message_id = header.get("message_id")
        sender = header.get("sender")
        
        # Acknowledge with timeout handler
        await self.timeout_handler.acknowledge_message(message_id)
        
        # Create ACK message
        ack_header = MessageHeader(
            sender=self.agent_name,
            receiver=sender,
            message_type=MessageType.ACK.value,
            priority=MessagePriority.LOW.value,
            reply_to=message_id
        )
        
        ack_message = AcknowledgmentMessage(
            header=ack_header,
            payload={
                "ack_message_id": message_id,
                "status": "received"
            }
        )
        
        # Don't wait for ACK to be published
        asyncio.create_task(
            self.message_queue.publish(
                Channel.MONITORING_CHANNEL.value,
                ack_message.to_dict()
            )
        )
    
    async def _send_error_message(self, original_message: Dict[str, Any], error: str):
        """Send error message"""
        header = original_message.get("header", {})
        
        error_header = MessageHeader(
            sender=self.agent_name,
            receiver=AgentType.MASTER_ORCHESTRATOR.value,
            message_type=MessageType.ERROR.value,
            priority=MessagePriority.HIGH.value,
            correlation_id=header.get("correlation_id", ""),
            reply_to=header.get("message_id")
        )
        
        error_message = ErrorMessage(
            header=error_header,
            payload={
                "error_code": "PROCESSING_ERROR",
                "error_message": error,
                "original_message_id": header.get("message_id")
            }
        )
        
        await self.message_queue.publish(
            Channel.ERROR_CHANNEL.value,
            error_message.to_dict()
        )
    
    async def _handle_timeout(self, message_id: str):
        """Handle message timeout"""
        logger.warning(f"{self.agent_name} handling timeout for message {message_id}")
        
        # Send timeout notification to orchestrator
        timeout_header = MessageHeader(
            sender=self.agent_name,
            receiver=AgentType.MASTER_ORCHESTRATOR.value,
            message_type=MessageType.TIMEOUT.value,
            priority=MessagePriority.HIGH.value
        )
        
        timeout_message = {
            "header": timeout_header.to_dict(),
            "payload": {
                "timed_out_message_id": message_id,
                "agent": self.agent_name
            }
        }
        
        await self.message_queue.publish(
            Channel.TIMEOUT_CHANNEL.value,
            timeout_message
        )
    
    async def _handle_error_message(self, message: Dict[str, Any]):
        """Handle error messages"""
        payload = message.get("payload", {})
        logger.error(f"{self.agent_name} received error: {payload.get('error_message')}")
    
    async def _handle_ack_message(self, message: Dict[str, Any]):
        """Handle acknowledgment messages"""
        payload = message.get("payload", {})
        ack_message_id = payload.get("ack_message_id")
        logger.debug(f"{self.agent_name} received ACK for message {ack_message_id}")
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """Register a custom message handler"""
        self.message_handlers[message_type] = handler
        logger.info(f"{self.agent_name} registered handler for {message_type}")
