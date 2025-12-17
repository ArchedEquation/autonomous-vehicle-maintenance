# UEBA Monitoring System - Quick Start Guide

## Overview

Get started with the UEBA (User and Entity Behavior Analytics) Monitoring System in minutes. This guide covers installation, basic usage, and common scenarios.

## Installation

### Prerequisites

- Python 3.8+
- pip package manager
- Existing async agent system (optional but recommended)

### Install Dependencies

```bash
pip install -r requirements.txt
```

The UEBA system uses:
- `scipy` for statistical analysis
- `numpy` for numerical operations
- `asyncio` for async operations (built-in Python 3.7+)

## Quick Start

### 1. Run the Demo

The fastest way to see UEBA in action:

```bash
python ueba_demo.py
```

This demonstrates:
- Normal agent behavior tracking
- Unauthorized access detection
- Volume spike detection
- Failed authentication handling
- Suspicious pattern detection
- Unusual hours detection
- Security dashboard
- Audit log export

### 2. Basic Setup

```python
import asyncio
from ueba_monitor import UEBAMonitor
from ueba_integration import UEBAIntegration
from ueba_baseline_profiles import get_all_baseline_profiles
from message_queue import InMemoryMessageQueue

async def main():
    # Initialize message queue
    message_queue = InMemoryMessageQueue()
    await message_queue.start()
    
    # Initialize UEBA monitor
    ueba_monitor = UEBAMonitor(
        window_size_minutes=60,
        anomaly_threshold_std=3.0,
        auto_block_threshold=5
    )
    
    # Initialize integration
    ueba_integration = UEBAIntegration(ueba_monitor, message_queue)
    await ueba_integration.start()
    
    print("UEBA Monitor is running!")
    
    # Keep running
    await asyncio.sleep(3600)
    
    # Cleanup
    await ueba_integration.stop()
    await message_queue.stop()

asyncio.run(main())
```

### 3. Track Agent Behavior

```python
# Track data access
await ueba_integration.track_data_access(
    agent_id="data_analysis_agent",
    data_type="vehicle_data",
    data_id="VEH-12345",
    data_scope="vehicle_telemetry",
    success=True
)

# Track API call
await ueba_integration.track_api_call(
    agent_id="scheduling_agent",
    api_endpoint="/api/create_booking",
    success=True,
    response_code=200
)

# Track booking
await ueba_integration.track_booking_action(
    agent_id="scheduling_agent",
    action="create",
    booking_id="BOOK-001",
    success=True
)

# Track authentication
await ueba_integration.track_authentication(
    agent_id="customer_engagement_agent",
    success=True,
    auth_method="token"
)
```

## Common Scenarios

### Scenario 1: Monitor Normal Operations

```python
# Data Analysis Agent accessing vehicle data
for i in range(10):
    await ueba_integration.track_data_access(
        agent_id="data_analysis_agent",
        data_type="vehicle_data",
        data_id=f"VEH-{1000+i}",
        data_scope="vehicle_telemetry",
        success=True
    )

# Check statistics
stats = ueba_integration.ueba_monitor.get_agent_statistics("data_analysis_agent")
print(f"Total Events: {stats['total_events']}")
print(f"Success Rate: {stats['success_rate']*100:.1f}%")
```

### Scenario 2: Detect Unauthorized Access

```python
# Scheduling Agent trying to access manufacturing data (not authorized)
await ueba_integration.track_data_access(
    agent_id="scheduling_agent",
    data_type="manufacturing_data",  # NOT authorized
    data_id="MFG-SECRET-001",
    data_scope="manufacturing_secrets",  # Forbidden scope
    success=True
)

# Check for alerts
alerts = ueba_integration.ueba_monitor.get_all_alerts(
    agent_id="scheduling_agent"
)

for alert in alerts:
    print(f"Alert: {alert.severity} - {alert.description}")
```

### Scenario 3: Handle Failed Authentication

```python
# Simulate failed auth attempts
for i in range(4):
    await ueba_integration.track_authentication(
        agent_id="customer_engagement_agent",
        success=False,
        auth_method="token"
    )

# Check if agent was blocked
is_blocked = "customer_engagement_agent" in ueba_integration.ueba_monitor.blocked_agents
print(f"Agent Blocked: {is_blocked}")
```

### Scenario 4: Monitor Volume Spikes

```python
# Excessive API calls
for i in range(50):
    await ueba_integration.track_api_call(
        agent_id="data_analysis_agent",
        api_endpoint="/api/analyze",
        success=True
    )

# Check for volume spike alerts
alerts = ueba_integration.ueba_monitor.get_all_alerts(
    agent_id="data_analysis_agent"
)

volume_alerts = [a for a in alerts if a.anomaly_type == "volume_spike"]
print(f"Volume Spike Alerts: {len(volume_alerts)}")
```

## Security Dashboard

### Get Agent Report

```python
report = ueba_integration.get_agent_security_report("scheduling_agent")

print(f"Agent: {report['agent_id']}")
print(f"Risk Level: {report['risk_level']}")
print(f"Blocked: {report['is_blocked']}")
print(f"Total Events: {report['statistics']['total_events']}")
print(f"Total Alerts: {len(report['recent_alerts'])}")
```

### Get System Dashboard

```python
dashboard = ueba_integration.get_system_security_dashboard()

print(f"System Health: {dashboard['system_health']}")
print(f"Total Agents: {dashboard['total_agents']}")
print(f"Blocked Agents: {dashboard['blocked_agents']}")
print(f"Total Alerts: {dashboard['total_alerts']}")

print("\nAlerts by Severity:")
for severity, count in dashboard['alert_counts_by_severity'].items():
    print(f"  {severity}: {count}")
```

## Baseline Profiles

### View Existing Profiles

```python
from ueba_baseline_profiles import get_all_baseline_profiles

profiles = get_all_baseline_profiles()

for agent_id, profile in profiles.items():
    print(f"\n{agent_id}:")
    print(f"  Authorized Resources: {profile.authorized_resources}")
    print(f"  API Calls/min: {profile.avg_api_calls_per_minute} ± {profile.std_api_calls_per_minute}")
    print(f"  Active Hours: {len(profile.typical_active_hours)} hours")
```

### Create Custom Profile

```python
from ueba_monitor import BaselineProfile, AgentAction

custom_profile = BaselineProfile(
    agent_id="my_custom_agent",
    authorized_resources={"resource1", "resource2"},
    authorized_actions={
        AgentAction.API_CALL.value,
        AgentAction.DATA_ACCESS.value
    },
    avg_api_calls_per_minute=10.0,
    std_api_calls_per_minute=3.0,
    avg_data_accesses_per_hour=100.0,
    std_data_accesses_per_hour=30.0,
    typical_active_hours={9, 10, 11, 12, 13, 14, 15, 16, 17},
    max_concurrent_operations=20,
    allowed_data_scopes={"scope1", "scope2"}
)

ueba_monitor.register_baseline_profile(custom_profile)
```

## Alert Management

### Register Alert Callback

```python
async def my_alert_handler(alert):
    print(f"ALERT: {alert.severity} - {alert.description}")
    
    if alert.severity == "CRITICAL":
        # Send notification
        await send_email_notification(alert)

ueba_monitor.register_alert_callback(my_alert_handler)
```

### Get Alerts by Severity

```python
from ueba_monitor import SecurityLevel

# Get critical alerts
critical_alerts = ueba_monitor.get_all_alerts(
    severity=SecurityLevel.CRITICAL,
    limit=10
)

for alert in critical_alerts:
    print(f"{alert.timestamp}: {alert.agent_id} - {alert.description}")
```

### Get Alerts by Agent

```python
# Get all alerts for specific agent
agent_alerts = ueba_monitor.get_all_alerts(
    agent_id="scheduling_agent",
    limit=20
)

print(f"Total Alerts: {len(agent_alerts)}")
```

## Audit Logging

### View Audit Log

```python
# Get recent audit entries
audit_log = ueba_monitor.get_audit_log(limit=50)

for entry in audit_log[-10:]:
    print(f"{entry['timestamp']}: {entry['agent_id']} - {entry['action_type']}")
```

### Filter Audit Log

```python
# Get audit log for specific agent
agent_log = ueba_monitor.get_audit_log(
    agent_id="data_analysis_agent",
    limit=100
)

# Get audit log for specific action
action_log = ueba_monitor.get_audit_log(
    action_type="data_access",
    limit=100
)
```

### Export Audit Data

```python
# Export audit log
ueba_monitor.export_audit_log("audit_log.json")

# Export security alerts
ueba_monitor.export_alerts("security_alerts.json")

print("Audit data exported successfully!")
```

## Agent Management

### Block Agent

```python
# Manually block an agent
ueba_monitor.block_agent(
    agent_id="suspicious_agent",
    reason="Manual review required due to suspicious activity"
)

print("Agent blocked successfully")
```

### Unblock Agent

```python
# Unblock an agent
ueba_monitor.unblock_agent("suspicious_agent")

print("Agent unblocked successfully")
```

### Check Block Status

```python
# Check if agent is blocked
is_blocked = "suspicious_agent" in ueba_monitor.blocked_agents

print(f"Agent Blocked: {is_blocked}")
```

## Configuration

### Adjust Thresholds

```python
from ueba_baseline_profiles import ANOMALY_DETECTION_CONFIG

# View current configuration
print("Current Thresholds:")
print(f"  Volume Spike: {ANOMALY_DETECTION_CONFIG['volume_spike_threshold_std']} std dev")
print(f"  Failed Auth: {ANOMALY_DETECTION_CONFIG['failed_auth_threshold']} attempts")
print(f"  Auto-Block: {ANOMALY_DETECTION_CONFIG['auto_block_threshold']} alerts")

# Create monitor with custom thresholds
ueba_monitor = UEBAMonitor(
    window_size_minutes=30,  # Shorter window
    anomaly_threshold_std=2.5,  # More sensitive
    auto_block_threshold=3  # Block faster
)
```

### View Rate Limits

```python
from ueba_baseline_profiles import RATE_LIMITS

for agent_id, limits in RATE_LIMITS.items():
    print(f"\n{agent_id}:")
    print(f"  API Calls/min: {limits['api_calls_per_minute']}")
    print(f"  Data Accesses/hour: {limits['data_accesses_per_hour']}")
    print(f"  Concurrent Ops: {limits['concurrent_operations']}")
```

## Integration with Async System

### Automatic Tracking

When integrated with the async agent system, UEBA automatically tracks:
- All message passing between agents
- API calls via message queue
- Data access events
- Authentication attempts

```python
# Initialize with async system
from async_master_orchestrator import AsyncMasterOrchestrator
from async_data_analysis_agent import AsyncDataAnalysisAgent

# Create agents
orchestrator = AsyncMasterOrchestrator(message_queue, timeout_handler)
data_agent = AsyncDataAnalysisAgent(message_queue, timeout_handler)

# Start agents (UEBA automatically tracks their activities)
await orchestrator.start()
await data_agent.start()

# UEBA is now monitoring all agent activities!
```

## Troubleshooting

### High False Positive Rate

**Problem:** Too many alerts for normal behavior

**Solution:**
```python
# Increase threshold
ueba_monitor = UEBAMonitor(
    anomaly_threshold_std=4.0  # Less sensitive
)

# Or update baseline profiles with current metrics
```

### Missed Anomalies

**Problem:** Suspicious behavior not detected

**Solution:**
```python
# Decrease threshold
ueba_monitor = UEBAMonitor(
    anomaly_threshold_std=2.0,  # More sensitive
    auto_block_threshold=3  # Block faster
)
```

### Performance Issues

**Problem:** High CPU/memory usage

**Solution:**
```python
# Reduce window size
ueba_monitor = UEBAMonitor(
    window_size_minutes=30  # Shorter window
)

# Export and clear logs regularly
ueba_monitor.export_audit_log("audit_log.json")
```

## Best Practices

### 1. Calibrate Baselines

```python
# Monitor for 1-2 weeks to establish baselines
# Then update profiles with actual metrics

profile = BaselineProfile(
    agent_id="my_agent",
    avg_api_calls_per_minute=actual_average,
    std_api_calls_per_minute=actual_std_dev,
    # ... other metrics
)
```

### 2. Review Alerts Regularly

```python
# Daily: Check critical alerts
critical = ueba_monitor.get_all_alerts(severity=SecurityLevel.CRITICAL)

# Weekly: Review all alerts
all_alerts = ueba_monitor.get_all_alerts(limit=100)

# Monthly: Update baseline profiles
```

### 3. Export Audit Data

```python
# Regular exports for compliance
import schedule

def export_daily():
    timestamp = datetime.now().strftime("%Y%m%d")
    ueba_monitor.export_audit_log(f"audit_log_{timestamp}.json")
    ueba_monitor.export_alerts(f"alerts_{timestamp}.json")

schedule.every().day.at("00:00").do(export_daily)
```

### 4. Set Up Alert Notifications

```python
async def critical_alert_handler(alert):
    if alert.severity == "CRITICAL":
        # Send email
        await send_email(
            to="security@company.com",
            subject=f"CRITICAL: {alert.agent_id}",
            body=alert.description
        )
        
        # Send SMS
        await send_sms(
            to="+1234567890",
            message=f"CRITICAL ALERT: {alert.agent_id}"
        )

ueba_monitor.register_alert_callback(critical_alert_handler)
```

## Next Steps

1. **Read Full Documentation**: [UEBA_MONITORING_SYSTEM.md](UEBA_MONITORING_SYSTEM.md)
2. **Run the Demo**: `python ueba_demo.py`
3. **Integrate with Your System**: Add UEBA to your async agents
4. **Customize Profiles**: Adjust baselines for your use case
5. **Set Up Monitoring**: Create dashboards and alerts

## Support

For questions or issues:
1. Check the [full documentation](UEBA_MONITORING_SYSTEM.md)
2. Review the demo code (`ueba_demo.py`)
3. Examine baseline profiles (`ueba_baseline_profiles.py`)
4. Contact the security team

## Example: Complete Setup

```python
import asyncio
from ueba_monitor import UEBAMonitor
from ueba_integration import UEBAIntegration
from message_queue import InMemoryMessageQueue, TimeoutHandler
from async_master_orchestrator import AsyncMasterOrchestrator
from async_data_analysis_agent import AsyncDataAnalysisAgent

async def main():
    # Initialize infrastructure
    message_queue = InMemoryMessageQueue()
    timeout_handler = TimeoutHandler()
    await message_queue.start()
    
    # Initialize UEBA
    ueba_monitor = UEBAMonitor(
        window_size_minutes=60,
        anomaly_threshold_std=3.0,
        auto_block_threshold=5
    )
    
    ueba_integration = UEBAIntegration(ueba_monitor, message_queue)
    await ueba_integration.start()
    
    # Initialize agents
    orchestrator = AsyncMasterOrchestrator(message_queue, timeout_handler)
    data_agent = AsyncDataAnalysisAgent(message_queue, timeout_handler)
    
    # Start agents
    await orchestrator.start()
    await data_agent.start()
    
    print("System running with UEBA monitoring!")
    
    # Monitor for 1 hour
    await asyncio.sleep(3600)
    
    # Show dashboard
    dashboard = ueba_integration.get_system_security_dashboard()
    print(f"System Health: {dashboard['system_health']}")
    
    # Export audit data
    ueba_monitor.export_audit_log("audit_log.json")
    ueba_monitor.export_alerts("security_alerts.json")
    
    # Cleanup
    await orchestrator.stop()
    await data_agent.stop()
    await ueba_integration.stop()
    await message_queue.stop()

asyncio.run(main())
```

This complete setup provides:
- ✅ Real-time behavior tracking
- ✅ Anomaly detection
- ✅ Security alerts
- ✅ Audit logging
- ✅ Automatic agent blocking
- ✅ Security dashboard

You're now ready to use the UEBA Monitoring System!
