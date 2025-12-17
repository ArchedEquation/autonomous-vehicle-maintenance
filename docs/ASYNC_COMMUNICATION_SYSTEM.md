# Async Inter-Agent Communication System

## Overview

This document describes the event-driven, asynchronous inter-agent communication system that enables scalable, reliable message passing between autonomous agents in the vehicle predictive maintenance platform.

## Architecture

### Core Components

1. **Message Queue** (`message_queue.py`)
   - In-memory queue implementation with priority support
   - Supports both synchronous and asynchronous operations
   - Extensible to external brokers (RabbitMQ, Kafka)
   - Message logging for UEBA monitoring

2. **Message Schemas** (`message_schemas.py`)
   - Standardized message formats
   - Type-safe message definitions
   - Header with metadata (ID, timestamp, sender, receiver, priority, correlation ID)

3. **Channel Definitions** (`channel_definitions.py`)
   - Named channels for different message types
   - Subscription rules for each agent type
   - Message flow definitions

4. **Timeout Handler** (`message_queue.py`)
   - Tracks pending messages
   - Escalates timeouts to orchestrator
   - Configurable timeout periods per message

5. **Async Agent Base** (`async_agent_base.py`)
   - Base class for all agents
   - Automatic subscription management
   - Message routing and acknowledgment
   - Error handling

## Message Structure

### Message Header

Every message includes a standardized header:

```python
{
    "message_id": "uuid",           # Unique message identifier
    "correlation_id": "uuid",       # Workflow tracking ID
    "timestamp": "ISO-8601",        # Message creation time
    "sender": "agent_name",         # Sending agent
    "receiver": "agent_name",       # Intended receiver
    "message_type": "type",         # Message type enum
    "priority": 1-4,                # Priority level
    "reply_to": "message_id",       # Optional reply reference
    "ttl": 300                      # Time to live (seconds)
}
```

### Message Payload

Payload structure varies by message type but always includes relevant data:

```python
{
    "header": { ... },
    "payload": {
        # Type-specific data
        "vehicle_id": "VEH-12345",
        "customer_id": "CUST-001",
        # ... additional fields
    }
}
```

## Message Types

### 1. Vehicle Data Message
- **Type**: `VEHICLE_DATA`
- **Flow**: External System → Master Orchestrator
- **Payload**: Vehicle sensor data, customer info

### 2. Analysis Request/Result
- **Type**: `ANALYSIS_REQUEST`, `ANALYSIS_RESULT`
- **Flow**: Orchestrator → Data Analysis Agent → Orchestrator
- **Payload**: Sensor data, analysis results, predictions

### 3. Customer Engagement
- **Type**: `CUSTOMER_ENGAGEMENT`
- **Flow**: Orchestrator → Customer Engagement Agent → Orchestrator
- **Payload**: Customer info, message content, channel

### 4. Scheduling Request/Result
- **Type**: `SCHEDULING_REQUEST`, `SCHEDULING_RESULT`
- **Flow**: Orchestrator → Scheduling Agent → Orchestrator
- **Payload**: Appointment details, service center info

### 5. Feedback
- **Type**: `FEEDBACK`
- **Flow**: External System → Orchestrator
- **Payload**: Customer feedback, ratings, comments

### 6. Manufacturing Insights
- **Type**: `MANUFACTURING_INSIGHT`
- **Flow**: Orchestrator → Manufacturing System
- **Payload**: Insights, recommendations, affected components

### 7. Error Messages
- **Type**: `ERROR`
- **Flow**: Any Agent → Orchestrator
- **Payload**: Error code, message, stack trace

### 8. Acknowledgments
- **Type**: `ACK`
- **Flow**: Receiver → Sender
- **Payload**: Acknowledged message ID, status

## Priority Levels

Messages are processed based on priority:

1. **LOW (1)**: Feedback processing, insights generation
2. **NORMAL (2)**: Regular analysis, customer engagement
3. **HIGH (3)**: Predicted failures, urgent scheduling
4. **CRITICAL (4)**: System failures, safety issues

## Communication Channels

### Input Channels
- `channel.vehicle.data.input` - Vehicle data ingestion
- `channel.external.request` - External system requests

### Agent Channels
- `channel.data_analysis.request` - Analysis requests
- `channel.data_analysis.result` - Analysis results
- `channel.customer_engagement.request` - Engagement requests
- `channel.customer_engagement.result` - Engagement results
- `channel.scheduling.request` - Scheduling requests
- `channel.scheduling.result` - Scheduling results

### System Channels
- `channel.system.error` - Error notifications
- `channel.system.timeout` - Timeout escalations
- `channel.system.monitoring` - System monitoring

### Output Channels
- `channel.feedback.input` - Customer feedback
- `channel.feedback.processed` - Processed feedback
- `channel.manufacturing.insights` - Manufacturing insights

## Message Flow

### Complete Workflow

```
Vehicle Data → Data Analysis → Diagnosis → Customer Engagement → 
Scheduling → Feedback → Manufacturing Insights
```

### Detailed Flow

1. **Vehicle Data Ingestion**
   ```
   External System → VEHICLE_DATA_INPUT → Master Orchestrator
   ```

2. **Data Analysis**
   ```
   Master Orchestrator → DATA_ANALYSIS_REQUEST → Data Analysis Agent
   Data Analysis Agent → DATA_ANALYSIS_RESULT → Master Orchestrator
   ```

3. **Diagnosis & Customer Engagement** (if issues detected)
   ```
   Master Orchestrator → CUSTOMER_ENGAGEMENT_REQUEST → Customer Engagement Agent
   Customer Engagement Agent → CUSTOMER_ENGAGEMENT_RESULT → Master Orchestrator
   ```

4. **Scheduling** (if customer accepts)
   ```
   Master Orchestrator → SCHEDULING_REQUEST → Scheduling Agent
   Scheduling Agent → SCHEDULING_RESULT → Master Orchestrator
   ```

5. **Feedback Processing**
   ```
   External System → FEEDBACK_INPUT → Master Orchestrator
   Master Orchestrator → FEEDBACK_PROCESSED → Manufacturing System
   ```

6. **Manufacturing Insights**
   ```
   Master Orchestrator → MANUFACTURING_INSIGHTS → Manufacturing System
   ```

## Timeout Handling

### Configuration

Each message can specify a custom timeout:

```python
await agent.publish_message(
    channel=Channel.DATA_ANALYSIS_REQUEST.value,
    payload=data,
    timeout=60  # 60 seconds
)
```

### Timeout Flow

1. Message published with timeout registration
2. Timeout handler tracks message
3. If no acknowledgment within timeout period:
   - Timeout callback executed
   - Timeout message sent to orchestrator
   - Orchestrator implements retry logic or escalation

### Escalation Strategy

- **First timeout**: Retry with same agent
- **Second timeout**: Route to backup agent
- **Third timeout**: Manual intervention required

## Subscription Model

### Master Orchestrator Subscriptions

The orchestrator subscribes to ALL agent output channels:

```python
MASTER_ORCHESTRATOR = [
    "channel.vehicle.data.input",
    "channel.data_analysis.result",
    "channel.customer_engagement.result",
    "channel.scheduling.result",
    "channel.feedback.processed",
    "channel.manufacturing.insights",
    "channel.system.error",
    "channel.system.timeout",
    "channel.system.monitoring"
]
```

### Worker Agent Subscriptions

Worker agents subscribe ONLY to relevant input channels:

```python
DATA_ANALYSIS_AGENT = [
    "channel.data_analysis.request",
    "channel.orchestrator.command",
    "channel.system.error"
]

CUSTOMER_ENGAGEMENT_AGENT = [
    "channel.customer_engagement.request",
    "channel.orchestrator.command",
    "channel.system.error"
]

SCHEDULING_AGENT = [
    "channel.scheduling.request",
    "channel.orchestrator.command",
    "channel.system.error"
]
```

## UEBA Monitoring

### Message Logging

All messages are logged with:
- Timestamp
- Channel
- Action (published/consumed)
- Message ID
- Correlation ID
- Sender/Receiver
- Message Type
- Priority

### Log Analysis

The message log enables:
- Workflow tracking via correlation ID
- Performance analysis
- Error pattern detection
- Agent behavior monitoring
- Anomaly detection

### Accessing Logs

```python
# Get recent log entries
message_log = message_queue.get_message_log(limit=100)

# Get queue statistics
stats = message_queue.get_queue_stats()
```

## Error Handling

### Error Message Flow

```
Agent Error → ERROR_CHANNEL → Master Orchestrator → 
Retry Logic / Alternative Action / Manual Intervention
```

### Error Types

1. **Processing Errors**: Agent fails to process message
2. **Timeout Errors**: Message not acknowledged in time
3. **Validation Errors**: Invalid message format
4. **System Errors**: Infrastructure failures

### Recovery Strategies

- **Automatic Retry**: Retry failed operation
- **Circuit Breaker**: Temporarily disable failing agent
- **Fallback**: Route to backup agent
- **Dead Letter Queue**: Store unprocessable messages

## Performance Considerations

### Scalability

- **Horizontal Scaling**: Add more agent instances
- **Load Balancing**: Distribute messages across instances
- **Priority Queues**: Process critical messages first
- **Batch Processing**: Group related messages

### Optimization

- **Async Processing**: Non-blocking operations
- **Connection Pooling**: Reuse connections
- **Message Batching**: Reduce overhead
- **Compression**: Reduce message size

## External Message Broker Integration

### RabbitMQ Integration

```python
class RabbitMQMessageQueue(MessageQueue):
    def __init__(self, host, port, username, password):
        self.connection = pika.BlockingConnection(...)
        self.channel = self.connection.channel()
    
    async def publish(self, channel, message):
        self.channel.basic_publish(
            exchange='',
            routing_key=channel,
            body=json.dumps(message)
        )
```

### Kafka Integration

```python
class KafkaMessageQueue(MessageQueue):
    def __init__(self, bootstrap_servers):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    
    async def publish(self, channel, message):
        self.producer.send(channel, message)
```

## Usage Examples

### Starting the System

```python
import asyncio
from message_queue import InMemoryMessageQueue, TimeoutHandler
from async_master_orchestrator import AsyncMasterOrchestrator
from async_data_analysis_agent import AsyncDataAnalysisAgent

async def main():
    # Initialize components
    message_queue = InMemoryMessageQueue()
    timeout_handler = TimeoutHandler(default_timeout=30)
    
    await message_queue.start()
    
    # Initialize agents
    orchestrator = AsyncMasterOrchestrator(message_queue, timeout_handler)
    data_agent = AsyncDataAnalysisAgent(message_queue, timeout_handler)
    
    # Start agents
    await orchestrator.start()
    await data_agent.start()
    
    # System is now running...

asyncio.run(main())
```

### Publishing a Message

```python
# Publish vehicle data
vehicle_data = {
    "vehicle_id": "VEH-12345",
    "sensor_data": {...}
}

header = MessageHeader(
    sender="external_system",
    receiver="master_orchestrator",
    message_type=MessageType.VEHICLE_DATA.value,
    priority=MessagePriority.NORMAL.value
)

message = VehicleDataMessage(header=header, payload=vehicle_data)

await message_queue.publish(
    Channel.VEHICLE_DATA_INPUT.value,
    message.to_dict()
)
```

### Tracking Workflow

```python
# Get workflow status by correlation ID
workflow = orchestrator.get_workflow_status(correlation_id)

print(f"Current Stage: {workflow['current_stage']}")
print(f"Stages Completed: {workflow['stages_completed']}")
```

## Testing

### Unit Tests

Test individual components:
- Message queue operations
- Timeout handling
- Message routing
- Agent subscriptions

### Integration Tests

Test agent interactions:
- End-to-end workflows
- Error handling
- Timeout scenarios
- Priority processing

### Load Tests

Test system performance:
- Message throughput
- Concurrent workflows
- Queue capacity
- Agent scalability

## Best Practices

1. **Always use correlation IDs** for workflow tracking
2. **Set appropriate timeouts** based on operation complexity
3. **Use priority levels** to ensure critical messages are processed first
4. **Log all messages** for monitoring and debugging
5. **Implement retry logic** for transient failures
6. **Monitor queue depth** to prevent backlog
7. **Use acknowledgments** to confirm message receipt
8. **Handle errors gracefully** with fallback strategies

## Troubleshooting

### Common Issues

1. **Messages not being received**
   - Check agent subscriptions
   - Verify channel names
   - Check message queue status

2. **Timeouts occurring**
   - Increase timeout values
   - Check agent processing time
   - Verify agent is running

3. **High queue depth**
   - Add more agent instances
   - Optimize processing logic
   - Implement backpressure

4. **Message loss**
   - Enable message persistence
   - Implement acknowledgments
   - Use external message broker

## Future Enhancements

1. **Message Persistence**: Store messages to disk
2. **Distributed Tracing**: OpenTelemetry integration
3. **Message Replay**: Replay failed workflows
4. **Schema Validation**: Validate message formats
5. **Rate Limiting**: Prevent message flooding
6. **Dead Letter Queue**: Handle unprocessable messages
7. **Message Encryption**: Secure sensitive data
8. **Multi-tenancy**: Isolate customer data
