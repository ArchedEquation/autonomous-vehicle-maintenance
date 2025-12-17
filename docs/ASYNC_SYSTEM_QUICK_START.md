# Async Inter-Agent Communication System - Quick Start Guide

## Overview

This guide will help you quickly set up and run the asynchronous inter-agent communication system for vehicle predictive maintenance.

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Basic understanding of async/await in Python

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
python -c "import asyncio; print('Asyncio ready!')"
```

## Quick Start

### Running the Demo

The easiest way to understand the system is to run the demo:

```bash
python async_system_demo.py
```

This will:
1. Initialize the message queue and timeout handler
2. Start all agents (Orchestrator, Data Analysis, Customer Engagement, Scheduling)
3. Run three scenarios:
   - Vehicle with potential engine issue
   - Vehicle with critical oil pressure issue
   - Vehicle with normal readings
4. Display message flow, queue statistics, and workflow tracking

### Expected Output

```
================================================================================
ASYNC INTER-AGENT COMMUNICATION SYSTEM DEMO
Event-Driven Architecture with Message Passing
================================================================================

[Message Flow Diagram]

================================================================================
ALL AGENTS STARTED AND SUBSCRIBED TO CHANNELS
================================================================================

================================================================================
SCENARIO 1: Vehicle with Potential Engine Issue
================================================================================

[Workflow execution logs...]

Workflow 1 Status: {
  'current_stage': 'completed',
  'vehicle_id': 'VEH-12345',
  'stages_completed': ['data_analysis', 'customer_engagement', 'scheduling']
}

[Additional scenarios and statistics...]
```

## System Components

### 1. Message Queue (`message_queue.py`)

The message queue handles all inter-agent communication:

```python
from message_queue import InMemoryMessageQueue, TimeoutHandler

# Initialize
message_queue = InMemoryMessageQueue(max_queue_size=10000)
timeout_handler = TimeoutHandler(default_timeout=30)

await message_queue.start()
```

### 2. Message Schemas (`message_schemas.py`)

Standardized message formats:

```python
from message_schemas import MessageHeader, VehicleDataMessage, MessagePriority

# Create a message
header = MessageHeader(
    sender="external_system",
    receiver="master_orchestrator",
    message_type="VEHICLE_DATA",
    priority=MessagePriority.NORMAL.value
)

message = VehicleDataMessage(
    header=header,
    payload={
        "vehicle_id": "VEH-12345",
        "sensor_data": {...}
    }
)
```

### 3. Agents

All agents inherit from `AsyncAgentBase`:

- **Master Orchestrator**: Coordinates all workflows
- **Data Analysis Agent**: Performs anomaly detection and predictions
- **Customer Engagement Agent**: Handles customer communications
- **Scheduling Agent**: Manages appointment booking

## Basic Usage

### Publishing a Message

```python
import asyncio
from message_queue import InMemoryMessageQueue
from message_schemas import MessageHeader, MessageType
from channel_definitions import Channel

async def publish_example():
    message_queue = InMemoryMessageQueue()
    await message_queue.start()
    
    # Create message
    header = MessageHeader(
        sender="my_agent",
        receiver="target_agent",
        message_type=MessageType.VEHICLE_DATA.value
    )
    
    message = {
        "header": header.to_dict(),
        "payload": {"data": "example"}
    }
    
    # Publish
    await message_queue.publish(
        Channel.VEHICLE_DATA_INPUT.value,
        message
    )

asyncio.run(publish_example())
```

### Subscribing to a Channel

```python
async def message_handler(message):
    print(f"Received: {message}")

async def subscribe_example():
    message_queue = InMemoryMessageQueue()
    await message_queue.start()
    
    # Subscribe
    await message_queue.subscribe(
        Channel.VEHICLE_DATA_INPUT.value,
        message_handler
    )
    
    # Keep running
    await asyncio.sleep(60)

asyncio.run(subscribe_example())
```

### Creating a Custom Agent

```python
from async_agent_base import AsyncAgentBase
from message_schemas import MessageType

class MyCustomAgent(AsyncAgentBase):
    def __init__(self, message_queue, timeout_handler):
        super().__init__(
            agent_name="my_custom_agent",
            agent_type="custom_agent",
            message_queue=message_queue,
            timeout_handler=timeout_handler
        )
        
        # Register custom message handler
        self.register_message_handler(
            MessageType.VEHICLE_DATA.value,
            self._handle_vehicle_data
        )
    
    async def process_message(self, message):
        # Handle messages not caught by specific handlers
        print(f"Processing: {message}")
    
    async def _handle_vehicle_data(self, message):
        # Custom processing logic
        payload = message.get("payload", {})
        print(f"Handling vehicle data: {payload}")
        
        # Publish result
        await self.publish_message(
            channel="my.output.channel",
            payload={"result": "processed"},
            message_type="MY_RESULT",
            receiver="target_agent"
        )
```

## Common Workflows

### 1. Vehicle Data Analysis Workflow

```
Vehicle Data → Data Analysis → Customer Engagement → Scheduling
```

**Steps:**
1. External system publishes vehicle data
2. Orchestrator receives and routes to Data Analysis Agent
3. Data Analysis Agent performs anomaly detection
4. If issues detected, Orchestrator triggers Customer Engagement
5. If customer accepts, Orchestrator triggers Scheduling
6. Workflow completes

### 2. Feedback Processing Workflow

```
Customer Feedback → Orchestrator → Manufacturing Insights
```

**Steps:**
1. Customer provides feedback
2. Orchestrator processes feedback
3. Generates manufacturing insights
4. Publishes to manufacturing system

## Message Priority

Messages are processed based on priority:

```python
from message_schemas import MessagePriority

# Critical (4) - Immediate processing
priority = MessagePriority.CRITICAL.value

# High (3) - Process before normal
priority = MessagePriority.HIGH.value

# Normal (2) - Standard processing
priority = MessagePriority.NORMAL.value

# Low (1) - Process when queue is empty
priority = MessagePriority.LOW.value
```

## Timeout Handling

Configure timeouts for messages:

```python
# Publish with custom timeout
message_id = await agent.publish_message(
    channel="my.channel",
    payload=data,
    message_type="MY_TYPE",
    receiver="target_agent",
    timeout=60  # 60 seconds
)

# Timeout callback will be triggered if no acknowledgment
```

## Monitoring

### Get Queue Statistics

```python
stats = message_queue.get_queue_stats()
print(f"Total Channels: {stats['total_channels']}")
print(f"Total Messages: {stats['total_messages_logged']}")
```

### Get Message Log

```python
# Get last 100 messages
log = message_queue.get_message_log(limit=100)

for entry in log:
    print(f"{entry['timestamp']}: {entry['sender']} -> {entry['receiver']}")
```

### Track Workflow

```python
# Get workflow status by correlation ID
workflow = orchestrator.get_workflow_status(correlation_id)

print(f"Current Stage: {workflow['current_stage']}")
print(f"Completed: {workflow['stages_completed']}")
```

## Troubleshooting

### Issue: Messages Not Being Received

**Solution:**
1. Verify agent is started: `await agent.start()`
2. Check channel subscriptions
3. Verify channel names match

### Issue: Timeouts Occurring

**Solution:**
1. Increase timeout value
2. Check agent processing time
3. Verify agent is running and responsive

### Issue: High Queue Depth

**Solution:**
1. Add more agent instances
2. Optimize agent processing logic
3. Increase queue size

## Testing

### Unit Test Example

```python
import pytest
import asyncio
from message_queue import InMemoryMessageQueue

@pytest.mark.asyncio
async def test_message_publish():
    queue = InMemoryMessageQueue()
    await queue.start()
    
    message = {
        "header": {"message_id": "test-123"},
        "payload": {"data": "test"}
    }
    
    result = await queue.publish("test.channel", message)
    assert result == True
    
    await queue.stop()
```

### Integration Test Example

```python
@pytest.mark.asyncio
async def test_workflow():
    # Setup
    queue = InMemoryMessageQueue()
    timeout_handler = TimeoutHandler()
    orchestrator = AsyncMasterOrchestrator(queue, timeout_handler)
    
    await queue.start()
    await orchestrator.start()
    
    # Publish vehicle data
    vehicle_data = {...}
    await queue.publish(Channel.VEHICLE_DATA_INPUT.value, vehicle_data)
    
    # Wait for processing
    await asyncio.sleep(5)
    
    # Verify workflow
    workflow = orchestrator.get_workflow_status(correlation_id)
    assert workflow['current_stage'] == 'completed'
    
    # Cleanup
    await orchestrator.stop()
    await queue.stop()
```

## Best Practices

1. **Always use correlation IDs** for end-to-end tracking
2. **Set appropriate timeouts** based on operation complexity
3. **Use priority levels** to ensure critical messages are processed first
4. **Implement error handling** in all message handlers
5. **Log all important events** for debugging
6. **Monitor queue depth** to prevent backlog
7. **Test timeout scenarios** to ensure proper escalation

## Next Steps

1. Read the [Full Documentation](ASYNC_COMMUNICATION_SYSTEM.md)
2. Explore the [API Reference](API_REFERENCE.md)
3. Review the [System Overview](SYSTEM_OVERVIEW.md)
4. Check out individual agent documentation:
   - [Data Analysis Agent](DATA_ANALYSIS_AGENT_README.md)
   - [Customer Engagement Agent](CUSTOMER_ENGAGEMENT_README.md)
   - [Scheduling Agent](SCHEDULING_AGENT_README.md)
   - [Master Orchestrator](ORCHESTRATOR_README.md)

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the message logs
3. Examine queue statistics
4. Verify agent subscriptions

## Example: Complete System Setup

```python
import asyncio
from message_queue import InMemoryMessageQueue, TimeoutHandler
from async_master_orchestrator import AsyncMasterOrchestrator
from async_data_analysis_agent import AsyncDataAnalysisAgent
from async_customer_engagement_agent import AsyncCustomerEngagementAgent
from async_scheduling_agent import AsyncSchedulingAgent

async def main():
    # Initialize infrastructure
    message_queue = InMemoryMessageQueue()
    timeout_handler = TimeoutHandler(default_timeout=30)
    
    await message_queue.start()
    
    # Initialize agents
    orchestrator = AsyncMasterOrchestrator(message_queue, timeout_handler)
    data_agent = AsyncDataAnalysisAgent(message_queue, timeout_handler)
    engagement_agent = AsyncCustomerEngagementAgent(message_queue, timeout_handler)
    scheduling_agent = AsyncSchedulingAgent(message_queue, timeout_handler)
    
    # Start all agents
    await orchestrator.start()
    await data_agent.start()
    await engagement_agent.start()
    await scheduling_agent.start()
    
    print("System is running!")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        
        # Stop all agents
        await orchestrator.stop()
        await data_agent.stop()
        await engagement_agent.stop()
        await scheduling_agent.stop()
        await message_queue.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

This will start a fully functional async inter-agent communication system ready to process vehicle data and coordinate workflows!
