"""
Message Queue Implementation for Inter-Agent Communication
Supports both in-memory queue and external message brokers (RabbitMQ, Kafka)
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from collections import defaultdict, deque
from abc import ABC, abstractmethod
import threading

from message_schemas import MessageHeader, MessagePriority


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageQueue(ABC):
    """Abstract base class for message queue implementations"""
    
    @abstractmethod
    async def publish(self, channel: str, message: Dict[str, Any]) -> bool:
        """Publish a message to a channel"""
        pass
    
    @abstractmethod
    async def subscribe(self, channel: str, callback: Callable) -> None:
        """Subscribe to a channel with a callback"""
        pass
    
    @abstractmethod
    async def unsubscribe(self, channel: str, callback: Callable) -> None:
        """Unsubscribe from a channel"""
        pass


class InMemoryMessageQueue(MessageQueue):
    """
    In-memory message queue implementation with priority support
    Suitable for single-process applications and testing
    """
    
    def __init__(self, max_queue_size: int = 10000):
        self.channels: Dict[str, List[deque]] = defaultdict(
            lambda: [deque() for _ in range(5)]  # 5 priority levels
        )
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.message_log: List[Dict[str, Any]] = []
        self.max_queue_size = max_queue_size
        self.lock = asyncio.Lock()
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
    async def start(self):
        """Start the message queue processing"""
        self._running = True
        logger.info("InMemoryMessageQueue started")
    
    async def stop(self):
        """Stop the message queue processing"""
        self._running = False
        for task in self._tasks:
            task.cancel()
        logger.info("InMemoryMessageQueue stopped")
    
    async def publish(self, channel: str, message: Dict[str, Any]) -> bool:
        """
        Publish a message to a channel with priority support
        
        Args:
            channel: Channel name
            message: Message dictionary with header and payload
            
        Returns:
            bool: True if published successfully
        """
        try:
            async with self.lock:
                # Extract priority from message header
                priority = message.get("header", {}).get("priority", MessagePriority.NORMAL.value)
                priority_index = min(max(priority - 1, 0), 4)
                
                # Add to appropriate priority queue
                queue = self.channels[channel][priority_index]
                
                if len(queue) >= self.max_queue_size:
                    logger.warning(f"Queue for channel {channel} is full, dropping oldest message")
                    queue.popleft()
                
                queue.append(message)
                
                # Log the message
                self._log_message(channel, message, "published")
                
                logger.info(f"Published message to {channel} with priority {priority}")
                
            # Notify subscribers asynchronously
            await self._notify_subscribers(channel, message)
            
            return True
            
        except Exception as e:
            logger.error(f"Error publishing message to {channel}: {e}")
            return False
    
    async def subscribe(self, channel: str, callback: Callable) -> None:
        """
        Subscribe to a channel
        
        Args:
            channel: Channel name
            callback: Async callback function to handle messages
        """
        async with self.lock:
            if callback not in self.subscribers[channel]:
                self.subscribers[channel].append(callback)
                logger.info(f"Subscribed to channel: {channel}")
    
    async def unsubscribe(self, channel: str, callback: Callable) -> None:
        """
        Unsubscribe from a channel
        
        Args:
            channel: Channel name
            callback: Callback function to remove
        """
        async with self.lock:
            if callback in self.subscribers[channel]:
                self.subscribers[channel].remove(callback)
                logger.info(f"Unsubscribed from channel: {channel}")
    
    async def _notify_subscribers(self, channel: str, message: Dict[str, Any]) -> None:
        """Notify all subscribers of a new message"""
        subscribers = self.subscribers.get(channel, [])
        
        for callback in subscribers:
            try:
                # Create task for each subscriber
                task = asyncio.create_task(callback(message))
                self._tasks.append(task)
            except Exception as e:
                logger.error(f"Error notifying subscriber on {channel}: {e}")
    
    def _log_message(self, channel: str, message: Dict[str, Any], action: str) -> None:
        """Log message for UEBA monitoring"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "channel": channel,
            "action": action,
            "message_id": message.get("header", {}).get("message_id"),
            "correlation_id": message.get("header", {}).get("correlation_id"),
            "sender": message.get("header", {}).get("sender"),
            "receiver": message.get("header", {}).get("receiver"),
            "message_type": message.get("header", {}).get("message_type"),
            "priority": message.get("header", {}).get("priority")
        }
        
        self.message_log.append(log_entry)
        
        # Keep log size manageable
        if len(self.message_log) > 100000:
            self.message_log = self.message_log[-50000:]
    
    async def get_next_message(self, channel: str) -> Optional[Dict[str, Any]]:
        """Get next message from channel (highest priority first)"""
        async with self.lock:
            if channel in self.channels:
                # Check priority queues from highest to lowest
                for priority_queue in reversed(self.channels[channel]):
                    if priority_queue:
                        message = priority_queue.popleft()
                        self._log_message(channel, message, "consumed")
                        return message
        return None
    
    def get_message_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent message log entries"""
        return self.message_log[-limit:]
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        stats = {
            "total_channels": len(self.channels),
            "total_subscribers": sum(len(subs) for subs in self.subscribers.values()),
            "total_messages_logged": len(self.message_log),
            "channels": {}
        }
        
        for channel, priority_queues in self.channels.items():
            total_messages = sum(len(q) for q in priority_queues)
            stats["channels"][channel] = {
                "total_messages": total_messages,
                "subscribers": len(self.subscribers.get(channel, []))
            }
        
        return stats


class TimeoutHandler:
    """
    Handles message timeouts and escalation
    """
    
    def __init__(self, default_timeout: int = 30):
        self.default_timeout = default_timeout
        self.pending_messages: Dict[str, Dict[str, Any]] = {}
        self.timeout_callbacks: Dict[str, Callable] = {}
        self.lock = asyncio.Lock()
        
    async def register_message(
        self,
        message_id: str,
        timeout: Optional[int] = None,
        callback: Optional[Callable] = None
    ) -> None:
        """
        Register a message for timeout tracking
        
        Args:
            message_id: Unique message identifier
            timeout: Timeout in seconds (uses default if None)
            callback: Callback to execute on timeout
        """
        async with self.lock:
            timeout_seconds = timeout or self.default_timeout
            expiry_time = datetime.utcnow() + timedelta(seconds=timeout_seconds)
            
            self.pending_messages[message_id] = {
                "expiry_time": expiry_time,
                "timeout_seconds": timeout_seconds
            }
            
            if callback:
                self.timeout_callbacks[message_id] = callback
            
            # Schedule timeout check
            asyncio.create_task(self._check_timeout(message_id))
    
    async def acknowledge_message(self, message_id: str) -> bool:
        """
        Acknowledge message receipt (removes from timeout tracking)
        
        Args:
            message_id: Message identifier
            
        Returns:
            bool: True if message was pending
        """
        async with self.lock:
            if message_id in self.pending_messages:
                del self.pending_messages[message_id]
                if message_id in self.timeout_callbacks:
                    del self.timeout_callbacks[message_id]
                logger.info(f"Message {message_id} acknowledged")
                return True
            return False
    
    async def _check_timeout(self, message_id: str) -> None:
        """Check if message has timed out"""
        while True:
            async with self.lock:
                if message_id not in self.pending_messages:
                    return
                
                message_info = self.pending_messages[message_id]
                
                if datetime.utcnow() >= message_info["expiry_time"]:
                    logger.warning(f"Message {message_id} timed out after {message_info['timeout_seconds']}s")
                    
                    # Execute timeout callback if registered
                    if message_id in self.timeout_callbacks:
                        callback = self.timeout_callbacks[message_id]
                        try:
                            await callback(message_id)
                        except Exception as e:
                            logger.error(f"Error executing timeout callback: {e}")
                    
                    # Remove from tracking
                    del self.pending_messages[message_id]
                    if message_id in self.timeout_callbacks:
                        del self.timeout_callbacks[message_id]
                    return
            
            # Check every second
            await asyncio.sleep(1)
    
    def get_pending_count(self) -> int:
        """Get count of pending messages"""
        return len(self.pending_messages)
