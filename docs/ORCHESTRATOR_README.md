# Master Orchestrator Documentation

## Overview

The Master Orchestrator is the central coordination system for the vehicle maintenance multi-agent workflow. It manages state machines, priority queues, agent coordination, retry logic, and comprehensive audit logging.

## Features

- **State Machine Management**: 12-state workflow with validated transitions
- **Priority Queue**: 4-level priority system (URGENT/HIGH/SCHEDULED/ROUTINE)
- **Agent Coordination**: Routes tasks to appropriate agents
- **Retry Logic**: 3 attempts with exponential backoff
- **UEBA Audit Logging**: Complete audit trail for compliance
- **Error Handling**: Graceful failure recovery
- **Statistics Tracking**: Performance metrics and monitoring

## Architecture

See [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) for complete architecture details.

## Usage

### Basic Setup

```python
from master_orchestrator import MasterOrchestrator, AgentType

# Initialize orchestrator
orchestrator = MasterOrchestrator(max_workers=10)

# Register agents
orchestrator.register_agent(AgentType.DATA_ANALYSIS, data_handler)
orchestrator.register_agent(AgentType.DIAGNOSIS, diagnosis_handler)
orchestrator.register_agent(AgentType.CUSTOMER_ENGAGEMENT, engagement_handler)
orchestrator.register_agent(AgentType.SCHEDULING, scheduling_handler)

# Start processing
orchestrator.start()
```

### Process Vehicle Telemetry

```python
# Receive vehicle data
telemetry = {
    'vehicle_id': 'VEH001',
    'timestamp': datetime.now().isoformat(),
    'engine_temp': 95.0,
    'battery_voltage': 12.6,
    # ... other sensors
}

# Create workflow
workflow_id = orchestrator.receive_vehicle_telemetry('VEH001', telemetry)

# Check status
status = orchestrator.get_workflow_status(workflow_id)
print(f"State: {status['state']}")
print(f"Priority: {status['priority']}")
```

## Workflow States

```
PENDING → DATA_ANALYSIS → DIAGNOSIS → URGENCY_ASSESSMENT
    ↓
CUSTOMER_ENGAGEMENT → SCHEDULING → SCHEDULED → IN_SERVICE
    ↓
FEEDBACK → COMPLETED

(Any state can → FAILED → RETRY)
```

## Priority Levels

| Priority | Value | Use Case | Processing |
|----------|-------|----------|------------|
| URGENT | 1 | Safety issues | Immediate |
| HIGH | 2 | Imminent failures | Fast-tracked |
| SCHEDULED | 3 | Planned maintenance | Standard |
| ROUTINE | 4 | Regular checks | Batch |

## Agent Types

- **DATA_ANALYSIS**: Processes telematics and detects anomalies
- **DIAGNOSIS**: Predicts failures and recommends services
- **CUSTOMER_ENGAGEMENT**: Communicates with customers
- **SCHEDULING**: Optimizes appointment scheduling
- **FEEDBACK**: Collects post-service feedback
- **MANUFACTURING_QUALITY**: Analyzes quality patterns

## Error Handling

### Retry Strategy

1. Agent failure detected
2. Log error and increment retry count
3. Transition to RETRY state
4. Apply exponential backoff (2s, 4s, 8s)
5. Re-execute from failure point
6. If max retries exceeded → FAILED state

### Failure Alerts

- Critical failures trigger alerts
- Logged to audit trail
- Can integrate with monitoring systems

## Statistics

```python
stats = orchestrator.get_statistics()
```

Returns:
- `total_workflows`: Total workflows created
- `completed`: Successfully completed
- `failed`: Failed workflows
- `urgent_handled`: Critical cases
- `active_workflows`: Currently processing
- `workflows_by_state`: State breakdown
- `average_completion_time`: Average time to complete

## Configuration

```python
MasterOrchestrator(
    max_workers=10  # Concurrent task limit
)
```

## Integration

See [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) for integration examples.

## API Reference

### Methods

#### `register_agent(agent_type: AgentType, handler: Callable)`
Register a worker agent handler.

#### `start()`
Start the orchestrator task processing.

#### `receive_vehicle_telemetry(vehicle_id: str, telemetry_data: Dict) -> str`
Entry point for vehicle telemetry. Returns workflow_id.

#### `get_workflow_status(workflow_id: str) -> Dict`
Get current status of a workflow.

#### `get_statistics() -> Dict`
Get orchestrator statistics.

#### `shutdown()`
Gracefully shutdown the orchestrator.

## Examples

See `orchestrator_integration_example.py` for complete examples.

## License

[Your License Here]
