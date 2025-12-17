"""
Test Suite for Async Inter-Agent Communication System
Validates message passing, timeout handling, and workflow coordination
"""
import asyncio
import pytest
from datetime import datetime

from message_queue import InMemoryMessageQueue, TimeoutHandler
from message_schemas import (
    MessageHeader, MessagePriority, MessageType, AgentType,
    VehicleDataMessage, AnalysisRequestMessage
)
from channel_definitions import Channel
from async_master_orchestrator import AsyncMasterOrchestrator
from async_data_analysis_agent import AsyncDataAnalysisAgent
from async_customer_engagement_agent import AsyncCustomerEngagementAgent
from async_scheduling_agent import AsyncSchedulingAgent


class TestMessageQueue:
    """Test message queue functionality"""
    
    @pytest.mark.asyncio
    async def test_queue_initialization(self):
        """Test queue can be initialized and started"""
        queue = InMemoryMessageQueue(max_queue_size=1000)
        await queue.start()
        
        assert queue._running == True
        
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_message_publish(self):
        """Test message can be published to queue"""
        queue = InMemoryMessageQueue()
        await queue.start()
        
        header = MessageHeader(
            sender="test_sender",
            receiver="test_receiver",
            message_type=MessageType.VEHICLE_DATA.value
        )
        
        message = {
            "header": header.to_dict(),
            "payload": {"test": "data"}
        }
        
        result = await queue.publish("test.channel", message)
        
        assert result == True
        
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_message_subscribe(self):
        """Test subscription to channel"""
        queue = InMemoryMessageQueue()
        await queue.start()
        
        received_messages = []
        
        async def handler(message):
            received_messages.append(message)
        
        await queue.subscribe("test.channel", handler)
        
        # Publish message
        header = MessageHeader(
            sender="test",
            receiver="test",
            message_type=MessageType.VEHICLE_DATA.value
        )
        
        message = {
            "header": header.to_dict(),
            "payload": {"test": "data"}
        }
        
        await queue.publish("test.channel", message)
        
        # Wait for processing
        await asyncio.sleep(0.5)
        
        assert len(received_messages) == 1
        assert received_messages[0]["payload"]["test"] == "data"
        
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_priority_queue(self):
        """Test priority-based message processing"""
        queue = InMemoryMessageQueue()
        await queue.start()
        
        # Publish messages with different priorities
        for priority in [MessagePriority.LOW, MessagePriority.HIGH, MessagePriority.NORMAL]:
            header = MessageHeader(
                sender="test",
                receiver="test",
                message_type=MessageType.VEHICLE_DATA.value,
                priority=priority.value
            )
            
            message = {
                "header": header.to_dict(),
                "payload": {"priority": priority.value}
            }
            
            await queue.publish("test.channel", message)
        
        # Get messages - should be in priority order
        msg1 = await queue.get_next_message("test.channel")
        msg2 = await queue.get_next_message("test.channel")
        msg3 = await queue.get_next_message("test.channel")
        
        # HIGH (3) should come first, then NORMAL (2), then LOW (1)
        assert msg1["payload"]["priority"] == MessagePriority.HIGH.value
        assert msg2["payload"]["priority"] == MessagePriority.NORMAL.value
        assert msg3["payload"]["priority"] == MessagePriority.LOW.value
        
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_message_logging(self):
        """Test message logging for UEBA"""
        queue = InMemoryMessageQueue()
        await queue.start()
        
        header = MessageHeader(
            sender="test_sender",
            receiver="test_receiver",
            message_type=MessageType.VEHICLE_DATA.value
        )
        
        message = {
            "header": header.to_dict(),
            "payload": {"test": "data"}
        }
        
        await queue.publish("test.channel", message)
        
        # Check log
        log = queue.get_message_log(limit=10)
        
        assert len(log) > 0
        assert log[-1]["sender"] == "test_sender"
        assert log[-1]["receiver"] == "test_receiver"
        assert log[-1]["channel"] == "test.channel"
        
        await queue.stop()


class TestTimeoutHandler:
    """Test timeout handling functionality"""
    
    @pytest.mark.asyncio
    async def test_timeout_registration(self):
        """Test message timeout registration"""
        handler = TimeoutHandler(default_timeout=30)
        
        await handler.register_message("test-msg-123", timeout=5)
        
        assert handler.get_pending_count() == 1
    
    @pytest.mark.asyncio
    async def test_message_acknowledgment(self):
        """Test message acknowledgment removes from timeout tracking"""
        handler = TimeoutHandler(default_timeout=30)
        
        await handler.register_message("test-msg-123", timeout=5)
        result = await handler.acknowledge_message("test-msg-123")
        
        assert result == True
        assert handler.get_pending_count() == 0
    
    @pytest.mark.asyncio
    async def test_timeout_callback(self):
        """Test timeout callback is executed"""
        handler = TimeoutHandler(default_timeout=1)
        
        callback_executed = []
        
        async def timeout_callback(message_id):
            callback_executed.append(message_id)
        
        await handler.register_message("test-msg-123", timeout=1, callback=timeout_callback)
        
        # Wait for timeout
        await asyncio.sleep(2)
        
        assert len(callback_executed) == 1
        assert callback_executed[0] == "test-msg-123"


class TestAgents:
    """Test agent functionality"""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent can be initialized"""
        queue = InMemoryMessageQueue()
        timeout_handler = TimeoutHandler()
        
        await queue.start()
        
        agent = AsyncDataAnalysisAgent(queue, timeout_handler)
        await agent.start()
        
        assert agent.is_running == True
        assert len(agent.subscribed_channels) > 0
        
        await agent.stop()
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_agent_message_handling(self):
        """Test agent can handle messages"""
        queue = InMemoryMessageQueue()
        timeout_handler = TimeoutHandler()
        
        await queue.start()
        
        agent = AsyncDataAnalysisAgent(queue, timeout_handler)
        await agent.start()
        
        # Publish analysis request
        header = MessageHeader(
            sender="test",
            receiver="data_analysis_agent",
            message_type=MessageType.ANALYSIS_REQUEST.value
        )
        
        message = AnalysisRequestMessage(
            header=header,
            payload={
                "vehicle_id": "VEH-TEST",
                "sensor_data": {
                    "engine_temperature": 200,
                    "oil_pressure": 35
                }
            }
        )
        
        await queue.publish(Channel.DATA_ANALYSIS_REQUEST.value, message.to_dict())
        
        # Wait for processing
        await asyncio.sleep(3)
        
        # Check that result was published
        log = queue.get_message_log(limit=10)
        result_messages = [
            entry for entry in log 
            if entry["message_type"] == MessageType.ANALYSIS_RESULT.value
        ]
        
        assert len(result_messages) > 0
        
        await agent.stop()
        await queue.stop()


class TestWorkflows:
    """Test end-to-end workflows"""
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test complete vehicle data workflow"""
        # Initialize system
        queue = InMemoryMessageQueue()
        timeout_handler = TimeoutHandler()
        
        await queue.start()
        
        # Initialize agents
        orchestrator = AsyncMasterOrchestrator(queue, timeout_handler)
        data_agent = AsyncDataAnalysisAgent(queue, timeout_handler)
        engagement_agent = AsyncCustomerEngagementAgent(queue, timeout_handler)
        scheduling_agent = AsyncSchedulingAgent(queue, timeout_handler)
        
        # Start agents
        await orchestrator.start()
        await data_agent.start()
        await engagement_agent.start()
        await scheduling_agent.start()
        
        # Wait for initialization
        await asyncio.sleep(1)
        
        # Publish vehicle data with issue
        vehicle_data = {
            "vehicle_id": "VEH-TEST-001",
            "customer_id": "CUST-TEST-001",
            "timestamp": datetime.utcnow().isoformat(),
            "sensor_data": {
                "engine_temperature": 230,  # High temperature
                "oil_pressure": 35,
                "rpm": 3000,
                "speed": 65
            }
        }
        
        header = MessageHeader(
            sender="external_system",
            receiver="master_orchestrator",
            message_type=MessageType.VEHICLE_DATA.value,
            priority=MessagePriority.NORMAL.value
        )
        
        message = VehicleDataMessage(header=header, payload=vehicle_data)
        correlation_id = header.correlation_id
        
        await queue.publish(Channel.VEHICLE_DATA_INPUT.value, message.to_dict())
        
        # Wait for workflow to complete
        await asyncio.sleep(8)
        
        # Check workflow status
        workflow = orchestrator.get_workflow_status(correlation_id)
        
        assert workflow is not None
        assert workflow["vehicle_id"] == "VEH-TEST-001"
        assert "data_analysis" in workflow["stages_completed"]
        
        # Cleanup
        await orchestrator.stop()
        await data_agent.stop()
        await engagement_agent.stop()
        await scheduling_agent.stop()
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_workflow_with_normal_vehicle(self):
        """Test workflow with vehicle that has no issues"""
        # Initialize system
        queue = InMemoryMessageQueue()
        timeout_handler = TimeoutHandler()
        
        await queue.start()
        
        orchestrator = AsyncMasterOrchestrator(queue, timeout_handler)
        data_agent = AsyncDataAnalysisAgent(queue, timeout_handler)
        
        await orchestrator.start()
        await data_agent.start()
        
        await asyncio.sleep(1)
        
        # Publish vehicle data with normal readings
        vehicle_data = {
            "vehicle_id": "VEH-NORMAL",
            "customer_id": "CUST-NORMAL",
            "timestamp": datetime.utcnow().isoformat(),
            "sensor_data": {
                "engine_temperature": 190,  # Normal
                "oil_pressure": 40,  # Normal
                "rpm": 2000,
                "speed": 50
            }
        }
        
        header = MessageHeader(
            sender="external_system",
            receiver="master_orchestrator",
            message_type=MessageType.VEHICLE_DATA.value
        )
        
        message = VehicleDataMessage(header=header, payload=vehicle_data)
        correlation_id = header.correlation_id
        
        await queue.publish(Channel.VEHICLE_DATA_INPUT.value, message.to_dict())
        
        # Wait for processing
        await asyncio.sleep(4)
        
        # Check workflow - should complete without engagement
        workflow = orchestrator.get_workflow_status(correlation_id)
        
        assert workflow is not None
        assert workflow["current_stage"] == "completed"
        assert "customer_engagement" not in workflow["stages_completed"]
        
        # Cleanup
        await orchestrator.stop()
        await data_agent.stop()
        await queue.stop()


class TestMonitoring:
    """Test monitoring and logging functionality"""
    
    @pytest.mark.asyncio
    async def test_queue_statistics(self):
        """Test queue statistics collection"""
        queue = InMemoryMessageQueue()
        await queue.start()
        
        # Publish some messages
        for i in range(5):
            header = MessageHeader(
                sender="test",
                receiver="test",
                message_type=MessageType.VEHICLE_DATA.value
            )
            
            message = {
                "header": header.to_dict(),
                "payload": {"index": i}
            }
            
            await queue.publish(f"test.channel.{i % 2}", message)
        
        stats = queue.get_queue_stats()
        
        assert stats["total_channels"] >= 2
        assert stats["total_messages_logged"] >= 5
        
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_correlation_tracking(self):
        """Test correlation ID tracking across workflow"""
        queue = InMemoryMessageQueue()
        timeout_handler = TimeoutHandler()
        
        await queue.start()
        
        orchestrator = AsyncMasterOrchestrator(queue, timeout_handler)
        data_agent = AsyncDataAnalysisAgent(queue, timeout_handler)
        
        await orchestrator.start()
        await data_agent.start()
        
        await asyncio.sleep(1)
        
        # Publish message
        header = MessageHeader(
            sender="test",
            receiver="master_orchestrator",
            message_type=MessageType.VEHICLE_DATA.value
        )
        
        correlation_id = header.correlation_id
        
        message = VehicleDataMessage(
            header=header,
            payload={
                "vehicle_id": "VEH-TRACK",
                "sensor_data": {"engine_temperature": 200}
            }
        )
        
        await queue.publish(Channel.VEHICLE_DATA_INPUT.value, message.to_dict())
        
        await asyncio.sleep(4)
        
        # Check message log for correlation ID
        log = queue.get_message_log(limit=50)
        correlated_messages = [
            entry for entry in log 
            if entry["correlation_id"] == correlation_id
        ]
        
        # Should have multiple messages with same correlation ID
        assert len(correlated_messages) >= 2
        
        await orchestrator.stop()
        await data_agent.stop()
        await queue.stop()


if __name__ == "__main__":
    print("Running Async System Tests...")
    print("=" * 80)
    
    # Run tests
    pytest.main([__file__, "-v", "-s"])
