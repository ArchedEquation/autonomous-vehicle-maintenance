# Main Orchestration Loop Documentation

## Overview

The Main Orchestration Loop is the central coordinator of the entire multi-agent system. It implements a state machine-based workflow that continuously polls vehicle telemetry data, routes it through various agents, and manages the complete lifecycle from anomaly detection to service completion.

## Architecture

### State Machine Design

The orchestration loop uses a state machine to track each vehicle's workflow:

```
┌─────────────┐
│    IDLE     │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ POLLING_TELEMETRY   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  ANALYZING_DATA     │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ ASSESSING_URGENCY   │
└──────┬──────────────┘
       │
       ├─── CRITICAL/HIGH ───┐
       │                     │
       ├─── MEDIUM ──────────┤
       │                     │
       └─── LOW ─────────────┤
                             │
                             ▼
                    ┌─────────────────────┐
                    │ ENGAGING_CUSTOMER   │
                    └──────┬──────────────┘
                           │
                           ├─── ACCEPTED ───┐
                           │                │
                           └─── DECLINED ───┤
                                            │
                                            ▼
                                   ┌─────────────────────┐
                                   │ SCHEDULING_SERVICE  │
                                   └──────┬──────────────┘
                                          │
                                          ▼
                                   ┌─────────────────────┐
                                   │ AWAITING_SERVICE    │
                                   └──────┬──────────────┘
                                          │
                                          ▼
                                   ┌─────────────────────┐
                                   │ COLLECTING_FEEDBACK │
                                   └──────┬──────────────┘
                                          │
                                          ▼
                                   ┌─────────────────────┐
                                   │    COMPLETED        │
                                   └─────────────────────┘
```

### Urgency Levels

The system classifies issues into four urgency levels:

| Level | Time to Failure | Action |
|-------|----------------|--------|
| **CRITICAL** | < 24 hours | Immediate engagement, highest priority |
| **HIGH** | < 7 days | Engagement within 24 hours, high priority |
| **MEDIUM** | < 30 days | Queue for batch processing, normal priority |
| **LOW** | > 30 days | Log only, no immediate action |

## Components

### 1. MainOrchestrationLoop Class

The main orchestrator class that coordinates all components.

#### Initialization

```python
orchestrator = MainOrchestrationLoop(
    telematics_api_url="http://localhost:8000",
    scheduler_api_url="http://localhost:8001",
    polling_interval=5  # seconds
)

await orchestrator.initialize()
await orchestrator.start()
```

#### Key Methods

- **`initialize()`**: Initialize all components (message queue, agents, UEBA, manufacturing insights)
- **`start()`**: Start the orchestration loop
- **`stop()`**: Stop the orchestration loop and cleanup
- **`get_statistics()`**: Get current statistics
- **`get_workflow_status(vin)`**: Get status of a specific vehicle workflow

### 2. VehicleWorkflow Class

Tracks the state and data for a single vehicle's workflow.

#### Attributes

```python
class VehicleWorkflow:
    vin: str                          # Vehicle identification number
    vehicle_data: Dict[str, Any]      # Current vehicle data
    state: WorkflowState              # Current workflow state
    correlation_id: str               # Unique workflow identifier
    analysis_result: Dict             # Results from data analysis
    urgency_level: UrgencyLevel       # Assessed urgency
    customer_response: Dict           # Customer engagement response
    appointment: Dict                 # Scheduled appointment details
    feedback: Dict                    # Post-service feedback
    error_count: int                  # Number of errors encountered
    retry_count: int                  # Number of retry attempts
    max_retries: int = 3              # Maximum retry attempts
    state_history: List               # History of state transitions
```

#### Methods

- **`transition_to(new_state, reason)`**: Transition to a new state
- **`can_retry()`**: Check if workflow can be retried
- **`increment_retry()`**: Increment retry counter

## Workflow Details

### 1. Telemetry Polling

The orchestrator continuously polls the telematics API:

```python
async def _polling_loop(self):
    while self.is_running:
        # Poll all vehicles
        response = requests.get(f"{self.telematics_api_url}/api/telemetry/all")
        vehicles = response.json().get("vehicles", [])
        
        # Process each vehicle
        for vehicle_data in vehicles:
            await self._process_vehicle_data(vehicle_data)
        
        await asyncio.sleep(self.polling_interval)
```

**Features:**
- Configurable polling interval
- Handles API timeouts and connection errors
- Processes multiple vehicles in parallel
- Tracks polling statistics

### 2. Data Analysis

When vehicle data is received:

```python
async def _process_vehicle_data(self, vehicle_data):
    vin = vehicle_data.get("vin")
    
    # Create or get workflow
    workflow = self.vehicle_workflows.get(vin) or VehicleWorkflow(vin, vehicle_data)
    
    # Generate correlation ID
    correlation_id = f"workflow-{vin}-{timestamp}"
    
    # Send to data analysis agent
    await self.message_queue.publish(
        channel="channel.data_analysis.request",
        message={
            "header": {...},
            "payload": {
                "vehicle_id": vin,
                "telemetry": vehicle_data["telemetry"]
            }
        }
    )
```

**Features:**
- Automatic workflow creation for new vehicles
- Correlation ID tracking for entire workflow
- Asynchronous message passing
- State transition tracking

### 3. Urgency Assessment

Based on analysis results:

```python
async def _assess_urgency(self, workflow):
    predicted_days = workflow.analysis_result.get("predicted_days_to_failure")
    
    if predicted_days < 1:
        workflow.urgency_level = UrgencyLevel.CRITICAL
    elif predicted_days < 7:
        workflow.urgency_level = UrgencyLevel.HIGH
    elif predicted_days < 30:
        workflow.urgency_level = UrgencyLevel.MEDIUM
    else:
        workflow.urgency_level = UrgencyLevel.LOW
    
    # Take action based on urgency
    if workflow.urgency_level in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
        await self._handle_customer_engagement(workflow)
```

**Decision Rules:**
- CRITICAL: Immediate customer engagement, highest priority
- HIGH: Engagement within 24 hours
- MEDIUM: Queue for batch processing
- LOW: Log only, feed to manufacturing insights

### 4. Customer Engagement

Generates personalized messages based on urgency:

```python
def _generate_customer_message(self, workflow):
    if workflow.urgency_level == UrgencyLevel.CRITICAL:
        return (
            f"URGENT: Critical issues detected. "
            f"Predicted failures: {failures}. "
            f"Please schedule service immediately."
        )
    elif workflow.urgency_level == UrgencyLevel.HIGH:
        return (
            f"IMPORTANT: Your vehicle needs attention soon. "
            f"Estimated time to failure: {days} days."
        )
    # ... more levels
```

**Features:**
- Urgency-based message generation
- Priority-based message routing
- Multiple communication channels (email, SMS, push)
- Customer response tracking

### 5. Service Scheduling

When customer accepts:

```python
async def _handle_scheduling(self, workflow):
    if workflow.customer_response.get("decision") == "accepted":
        await self.message_queue.publish(
            channel="channel.scheduling.request",
            message={
                "payload": {
                    "vehicle_id": workflow.vin,
                    "service_type": "diagnostic",
                    "urgency": workflow.urgency_level.value,
                    "preferred_dates": customer_preferences
                }
            }
        )
```

**Features:**
- Automatic appointment scheduling
- Urgency-based prioritization
- Customer preference consideration
- Appointment confirmation tracking

### 6. Manufacturing Insights Integration

Continuously feeds data to manufacturing insights:

```python
async def _feed_to_manufacturing_insights(self, workflow):
    for failure in workflow.analysis_result.get("predicted_failures", []):
        await self.manufacturing_insights.ingest_failure_data(
            vehicle_id=workflow.vin,
            component=failure["component"],
            failure_mode=failure["mode"],
            severity=self._map_urgency_to_severity(workflow.urgency_level),
            diagnosis_data=workflow.analysis_result,
            customer_feedback=workflow.feedback
        )
```

**Features:**
- Real-time failure data ingestion
- Automatic CAPA report generation
- Root cause analysis
- Quality trend tracking

### 7. UEBA Monitoring

All actions are monitored in parallel:

```python
# UEBA automatically tracks:
- Message queue activity
- Agent API calls
- Data access patterns
- Timing anomalies
- Failed operations
- Security violations
```

**Features:**
- Real-time behavior tracking
- Anomaly detection
- Automatic agent blocking
- Security audit logging

## Error Handling

### Timeout Handling

```python
async def _workflow_processing_loop(self):
    for vin, workflow in self.active_workflows.items():
        time_since_update = (datetime.utcnow() - workflow.last_update).total_seconds()
        
        if time_since_update > 300:  # 5 minute timeout
            await self._handle_error(workflow, "Workflow timeout")
```

### Retry Logic

```python
async def _handle_error(self, workflow, error_message):
    workflow.error_count += 1
    workflow.transition_to(WorkflowState.ERROR, error_message)
    
    if workflow.can_retry():
        workflow.increment_retry()
        workflow.transition_to(WorkflowState.IDLE, "Retry after error")
    else:
        # Max retries exceeded, mark as failed
        workflow.transition_to(WorkflowState.COMPLETED, "Failed after max retries")
```

### Error Types Handled

1. **API Timeouts**: Telemetry or scheduler API not responding
2. **Agent Failures**: Agent crashes or becomes unresponsive
3. **Customer No-Response**: Customer doesn't respond within timeout
4. **Data Validation Errors**: Invalid or corrupted data
5. **Network Errors**: Connection failures

## Statistics and Monitoring

### Available Statistics

```python
stats = orchestrator.get_statistics()

{
    "total_vehicles_processed": 150,
    "active_workflows": 12,
    "completed_workflows": 138,
    "anomalies_detected": 45,
    "customers_engaged": 42,
    "appointments_scheduled": 35,
    "failures_prevented": 30,
    "errors_encountered": 3,
    "workflow_states": {
        "idle": 0,
        "analyzing_data": 5,
        "engaging_customer": 4,
        "scheduling_service": 2,
        "completed": 138
    }
}
```

### Workflow Status

```python
status = orchestrator.get_workflow_status("VIN123456")

{
    "vin": "VIN123456",
    "state": "engaging_customer",
    "urgency_level": "high",
    "correlation_id": "workflow-VIN123456-1234567890",
    "last_update": "2024-01-15T10:30:00",
    "retry_count": 0,
    "error_count": 0,
    "state_history": [
        {
            "from_state": "idle",
            "to_state": "analyzing_data",
            "timestamp": "2024-01-15T10:25:00",
            "reason": "New telemetry data received"
        },
        {
            "from_state": "analyzing_data",
            "to_state": "assessing_urgency",
            "timestamp": "2024-01-15T10:26:00",
            "reason": "Analysis complete"
        }
    ],
    "analysis_result": {...},
    "customer_response": null,
    "appointment": null
}
```

## Integration with Other Components

### Message Queue

All inter-agent communication uses the message queue:

```python
# Publishing messages
await self.message_queue.publish(
    channel="channel.data_analysis.request",
    message={...}
)

# Subscribing to results
await self.message_queue.subscribe(
    "channel.data_analysis.result",
    self._handle_analysis_result
)
```

### UEBA Monitor

Automatic security monitoring:

```python
# UEBA tracks all message queue activity
# No explicit calls needed - automatic integration

# Get security dashboard
dashboard = orchestrator.ueba_integration.get_system_security_dashboard()
```

### Manufacturing Insights

Continuous data feeding:

```python
# Automatic ingestion during workflow
await self._feed_to_manufacturing_insights(workflow)

# Get insights summary
summary = orchestrator.manufacturing_insights.generate_summary_report()
```

## Usage Examples

### Basic Usage

```python
import asyncio
from main_orchestration_loop import MainOrchestrationLoop

async def main():
    # Create orchestrator
    orchestrator = MainOrchestrationLoop(
        telematics_api_url="http://localhost:8000",
        scheduler_api_url="http://localhost:8001",
        polling_interval=5
    )
    
    # Initialize and start
    await orchestrator.initialize()
    await orchestrator.start()
    
    # Run for some time
    await asyncio.sleep(300)  # 5 minutes
    
    # Get statistics
    stats = orchestrator.get_statistics()
    print(f"Processed {stats['total_vehicles_processed']} vehicles")
    
    # Stop
    await orchestrator.stop()

asyncio.run(main())
```

### Monitoring Specific Vehicle

```python
async def monitor_vehicle(orchestrator, vin):
    while True:
        status = orchestrator.get_workflow_status(vin)
        
        if status:
            print(f"Vehicle {vin}: {status['state']}")
            
            if status['state'] == 'completed':
                print("Workflow completed!")
                break
        
        await asyncio.sleep(5)
```

### Custom Error Handling

```python
class CustomOrchestrator(MainOrchestrationLoop):
    async def _handle_error(self, workflow, error_message):
        # Custom error handling
        await self.send_admin_alert(workflow.vin, error_message)
        
        # Call parent error handler
        await super()._handle_error(workflow, error_message)
```

## Performance Considerations

### Scalability

- **Concurrent Processing**: Multiple vehicles processed in parallel
- **Async I/O**: Non-blocking operations for API calls
- **Message Queue**: Decoupled agent communication
- **State Persistence**: Workflows can be persisted to database

### Optimization Tips

1. **Polling Interval**: Adjust based on vehicle count and urgency requirements
2. **Batch Processing**: Group low-priority workflows for efficiency
3. **Caching**: Cache frequently accessed data (vehicle info, service centers)
4. **Connection Pooling**: Reuse HTTP connections for API calls

### Resource Usage

- **Memory**: ~50MB base + ~1KB per active workflow
- **CPU**: Low (mostly I/O bound)
- **Network**: Depends on polling interval and vehicle count

## Troubleshooting

### Common Issues

**Issue**: Workflows stuck in ANALYZING_DATA state
- **Cause**: Data analysis agent not responding
- **Solution**: Check agent logs, verify message queue connectivity

**Issue**: High error count
- **Cause**: API timeouts or network issues
- **Solution**: Check API availability, increase timeout values

**Issue**: No workflows progressing
- **Cause**: Message queue not running
- **Solution**: Verify message queue is started

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Checks

```python
# Check component health
assert orchestrator.is_running
assert orchestrator.message_queue._running
assert orchestrator.ueba_monitor.is_running
assert orchestrator.manufacturing_insights.is_running
```

## Best Practices

1. **Always initialize before starting**: Call `initialize()` before `start()`
2. **Graceful shutdown**: Always call `stop()` to cleanup resources
3. **Monitor statistics**: Regularly check statistics for anomalies
4. **Handle errors**: Implement custom error handlers for critical workflows
5. **Test with mock data**: Use mock infrastructure for testing
6. **Set appropriate timeouts**: Balance responsiveness vs. false timeouts
7. **Monitor UEBA alerts**: Review security alerts regularly

## Future Enhancements

- [ ] Workflow persistence to database
- [ ] Multi-region support
- [ ] Advanced scheduling algorithms
- [ ] Machine learning for urgency prediction
- [ ] Real-time dashboard UI
- [ ] Webhook notifications
- [ ] A/B testing for customer messages
- [ ] Predictive maintenance scheduling

## Related Documentation

- [Async Communication System](ASYNC_COMMUNICATION_SYSTEM.md)
- [UEBA Monitoring System](UEBA_MONITORING_SYSTEM.md)
- [Manufacturing Insights](MANUFACTURING_INSIGHTS.md)
- [Mock Infrastructure](../mock_infrastructure/README.md)
