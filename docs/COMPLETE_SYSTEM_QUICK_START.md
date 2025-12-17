# Complete System Quick Start Guide

## Overview

This guide will help you get the complete multi-agent vehicle maintenance system up and running in minutes.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   Main Orchestration Loop                        │
│  (Coordinates all components, manages workflows)                 │
└───────────┬─────────────────────────────────────────────────────┘
            │
            ├──────────────────────────────────────────────────────┐
            │                                                       │
┌───────────▼──────────┐  ┌──────────────────┐  ┌────────────────▼─┐
│  Message Queue       │  │  UEBA Monitor    │  │  Manufacturing   │
│  (Async messaging)   │  │  (Security)      │  │  Insights        │
└───────────┬──────────┘  └──────────────────┘  └──────────────────┘
            │
    ┌───────┼───────┬───────────┐
    │       │       │           │
┌───▼───┐ ┌─▼──┐ ┌─▼────┐ ┌────▼────┐
│ Data  │ │Cust│ │Sched │ │  Mock   │
│Analysis│ │Eng │ │Agent │ │  APIs   │
└───────┘ └────┘ └──────┘ └─────────┘
```

## Prerequisites

### Required Software

- Python 3.8 or higher
- pip (Python package manager)

### Required Python Packages

```bash
pip install -r requirements.txt
```

Key packages:
- `asyncio` - Asynchronous programming
- `fastapi` - Mock API servers
- `uvicorn` - ASGI server
- `requests` - HTTP client
- `numpy`, `pandas` - Data processing
- `tensorflow`, `torch` - ML models (optional)

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd autonomous-vehicle-maintenance
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Generate Synthetic Data

```bash
cd mock_infrastructure
python synthetic_vehicle_data.py
cd ..
```

This creates `mock_infrastructure/synthetic_vehicles.json` with 10 test vehicles.

## Running the System

### Option 1: Complete System Demo (Recommended)

This is the easiest way to see the entire system in action.

#### Step 1: Start Mock Infrastructure

**Terminal 1 - Telematics API:**
```bash
python mock_infrastructure/telematics_api.py
```

Expected output:
```
================================================================================
STARTING TELEMATICS API SERVER
================================================================================
Loaded 10 vehicles
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 - Service Scheduler API:**
```bash
python mock_infrastructure/service_scheduler_api.py
```

Expected output:
```
================================================================================
STARTING SERVICE SCHEDULER API SERVER
================================================================================
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8001
```

#### Step 2: Run Main Orchestration Demo

**Terminal 3 - Main Orchestration:**
```bash
python main_orchestration_demo.py
```

Expected output:
```
================================================================================
MAIN ORCHESTRATION LOOP DEMONSTRATION
================================================================================

This demo shows the complete workflow:
1. Poll telematics API for vehicle data
2. Analyze data for anomalies and failures
3. Assess urgency level
4. Engage customers based on urgency
5. Schedule service appointments
6. Collect feedback
7. Feed data to manufacturing insights
8. UEBA monitors all actions in parallel

================================================================================
[STEP 1] Initializing all components...
[STEP 2] Starting main orchestration loop...
[STEP 3] Running orchestration loop...

STATISTICS (after 10 seconds)
================================================================================
Total vehicles processed: 10
Active workflows: 5
Completed workflows: 0
Customers engaged: 3
Appointments scheduled: 1
```

The demo will run for 2 minutes, showing real-time statistics.

### Option 2: Individual Component Testing

Test each component separately:

#### Test Async Communication System

```bash
python async_system_demo.py
```

#### Test UEBA Monitoring

```bash
python ueba_demo.py
```

#### Test Manufacturing Insights

```bash
python manufacturing_insights_demo.py
```

#### Test Mock Infrastructure

```bash
python mock_infrastructure/integrated_demo.py
```

## Understanding the Output

### Main Orchestration Loop Output

```
STATISTICS (after 10 seconds)
================================================================================
Total vehicles processed: 10        # Vehicles seen by system
Active workflows: 5                 # Currently processing
Completed workflows: 0              # Finished workflows
Customers engaged: 3                # Notifications sent
Appointments scheduled: 1           # Appointments booked
Errors encountered: 0               # System errors

Workflow states:
  analyzing_data: 3                 # In analysis
  engaging_customer: 2              # Awaiting customer response
  
Active workflows:
  VIN1234567890: analyzing_data
    Urgency: high
  VIN0987654321: engaging_customer
    Urgency: critical
```

### UEBA Security Dashboard

```
UEBA SECURITY DASHBOARD
================================================================================
System Health: HEALTHY              # Overall system status
Total Agents: 4                     # Number of agents
Blocked Agents: 0                   # Agents blocked for security
Total Alerts: 0                     # Security alerts

Alert Counts by Severity:
  CRITICAL: 0
  HIGH: 0
  MEDIUM: 0
```

### Manufacturing Insights

```
MANUFACTURING INSIGHTS
================================================================================
Total failure records: 15           # Failures tracked
Total CAPA reports: 2               # Quality reports generated
Pending CAPAs: 2                    # Awaiting action
Completed CAPAs: 0                  # Implemented fixes

Top failing components:
  brake_pads: 5 failures
  battery: 3 failures
  engine_temperature_sensor: 2 failures
```

## Workflow Example

Here's what happens when a vehicle with a critical issue is detected:

### 1. Telemetry Polling (t=0s)

```
[10:00:00] Polled 10 vehicles
[10:00:00] Vehicle VIN1234567890: New telemetry data received
```

### 2. Data Analysis (t=1s)

```
[10:00:01] Vehicle VIN1234567890: idle → analyzing_data
[10:00:01] Sent vehicle VIN1234567890 for analysis
[10:00:02] Analysis complete: anomaly detected
[10:00:02] Predicted failures: ['brake_pads']
[10:00:02] Failure probability: 0.85
```

### 3. Urgency Assessment (t=2s)

```
[10:00:02] Vehicle VIN1234567890: analyzing_data → assessing_urgency
[10:00:02] Predicted days to failure: 2
[10:00:02] Urgency level: HIGH
```

### 4. Customer Engagement (t=3s)

```
[10:00:03] Vehicle VIN1234567890: assessing_urgency → engaging_customer
[10:00:03] Sent customer engagement request
[10:00:03] Message: "IMPORTANT: Your vehicle needs attention soon..."
[10:00:05] Customer response: ACCEPTED
```

### 5. Service Scheduling (t=6s)

```
[10:00:06] Vehicle VIN1234567890: engaging_customer → scheduling_service
[10:00:06] Sent scheduling request
[10:00:07] Appointment booked: APT-123456
[10:00:07] Service center: Downtown Service Center
[10:00:07] Date: 2024-01-17 09:00:00
```

### 6. Completion (t=8s)

```
[10:00:08] Vehicle VIN1234567890: scheduling_service → completed
[10:00:08] Workflow completed successfully
[10:00:08] Fed 1 failures to manufacturing insights
```

## Monitoring the System

### Real-Time Statistics

Get current statistics:

```python
from main_orchestration_loop import MainOrchestrationLoop

orchestrator = MainOrchestrationLoop()
await orchestrator.initialize()
await orchestrator.start()

# Get statistics
stats = orchestrator.get_statistics()
print(f"Active workflows: {stats['active_workflows']}")
print(f"Customers engaged: {stats['customers_engaged']}")
```

### Workflow Status

Track a specific vehicle:

```python
# Get workflow status
status = orchestrator.get_workflow_status("VIN1234567890")

print(f"State: {status['state']}")
print(f"Urgency: {status['urgency_level']}")
print(f"Last update: {status['last_update']}")
```

### UEBA Dashboard

Check security status:

```python
# Get security dashboard
dashboard = orchestrator.ueba_integration.get_system_security_dashboard()

print(f"System Health: {dashboard['system_health']}")
print(f"Blocked Agents: {dashboard['blocked_agents']}")
print(f"Total Alerts: {dashboard['total_alerts']}")
```

### Manufacturing Insights

View quality metrics:

```python
# Get insights summary
summary = orchestrator.manufacturing_insights.generate_summary_report()

print(f"Total failures: {summary['total_failure_records']}")
print(f"CAPA reports: {summary['total_capa_reports']}")
```

## Configuration

### Polling Interval

Adjust how often telemetry is polled:

```python
orchestrator = MainOrchestrationLoop(
    polling_interval=10  # Poll every 10 seconds
)
```

### API URLs

Configure API endpoints:

```python
orchestrator = MainOrchestrationLoop(
    telematics_api_url="http://localhost:8000",
    scheduler_api_url="http://localhost:8001"
)
```

### Urgency Thresholds

Modify urgency assessment (in code):

```python
# In _assess_urgency method
if predicted_days < 1:
    urgency = UrgencyLevel.CRITICAL
elif predicted_days < 7:
    urgency = UrgencyLevel.HIGH
elif predicted_days < 30:
    urgency = UrgencyLevel.MEDIUM
else:
    urgency = UrgencyLevel.LOW
```

### Retry Logic

Configure retry behavior:

```python
class VehicleWorkflow:
    max_retries = 3  # Maximum retry attempts
```

## Troubleshooting

### Issue: "Connection refused" errors

**Cause**: Mock APIs not running

**Solution**: Start both mock APIs:
```bash
# Terminal 1
python mock_infrastructure/telematics_api.py

# Terminal 2
python mock_infrastructure/service_scheduler_api.py
```

### Issue: "No vehicles detected"

**Cause**: Synthetic data not generated

**Solution**: Generate synthetic data:
```bash
cd mock_infrastructure
python synthetic_vehicle_data.py
```

### Issue: Workflows stuck in ANALYZING_DATA

**Cause**: Data analysis agent not responding

**Solution**: Check logs for agent errors, restart orchestrator

### Issue: High error count

**Cause**: API timeouts or network issues

**Solution**: 
- Check API availability
- Increase timeout values
- Check network connectivity

### Issue: UEBA alerts

**Cause**: Unusual agent behavior detected

**Solution**: Review UEBA dashboard for details:
```python
dashboard = orchestrator.ueba_integration.get_system_security_dashboard()
print(dashboard['recent_critical_alerts'])
```

## Next Steps

### 1. Explore Individual Components

- **Async Communication**: `docs/ASYNC_COMMUNICATION_SYSTEM.md`
- **UEBA Monitoring**: `docs/UEBA_MONITORING_SYSTEM.md`
- **Manufacturing Insights**: `docs/MANUFACTURING_INSIGHTS.md`
- **Main Orchestration**: `docs/MAIN_ORCHESTRATION_LOOP.md`

### 2. Customize the System

- Modify urgency thresholds
- Add custom message templates
- Implement custom error handlers
- Add new workflow states

### 3. Integrate with Real Systems

- Replace mock APIs with real telemetry streams
- Connect to real service scheduler
- Integrate with real customer communication channels
- Add database persistence

### 4. Deploy to Production

- Set up monitoring and alerting
- Configure logging
- Implement health checks
- Set up load balancing
- Configure auto-scaling

## Common Use Cases

### Use Case 1: Monitor Specific Vehicle

```python
async def monitor_vehicle(vin):
    orchestrator = MainOrchestrationLoop()
    await orchestrator.initialize()
    await orchestrator.start()
    
    while True:
        status = orchestrator.get_workflow_status(vin)
        if status:
            print(f"{vin}: {status['state']}")
            if status['state'] == 'completed':
                break
        await asyncio.sleep(5)
```

### Use Case 2: Custom Error Handling

```python
class CustomOrchestrator(MainOrchestrationLoop):
    async def _handle_error(self, workflow, error_message):
        # Send alert to admin
        await self.send_admin_alert(workflow.vin, error_message)
        
        # Call parent handler
        await super()._handle_error(workflow, error_message)
```

### Use Case 3: Batch Processing

```python
# Process low-priority workflows in batches
async def batch_process_low_priority():
    low_priority_workflows = [
        w for w in orchestrator.active_workflows.values()
        if w.urgency_level == UrgencyLevel.LOW
    ]
    
    for workflow in low_priority_workflows:
        await orchestrator._handle_customer_engagement(workflow)
```

## Performance Tips

1. **Adjust Polling Interval**: Balance between responsiveness and load
2. **Use Batch Processing**: Group low-priority workflows
3. **Enable Caching**: Cache frequently accessed data
4. **Connection Pooling**: Reuse HTTP connections
5. **Horizontal Scaling**: Run multiple orchestrator instances

## Support

For issues or questions:
- Check documentation in `docs/` folder
- Review demo files for examples
- Check CHANGELOG.md for recent changes
- Review troubleshooting section above

## Summary

You now have a complete multi-agent vehicle maintenance system running with:

✅ Continuous telemetry polling
✅ Automatic anomaly detection
✅ Urgency-based customer engagement
✅ Automatic service scheduling
✅ Real-time security monitoring
✅ Quality insights and CAPA reports
✅ Complete workflow management

The system is processing vehicles, detecting issues, engaging customers, and scheduling appointments automatically!
