"""
UEBA Monitoring System Demo
Demonstrates behavior tracking, anomaly detection, and security alerts
"""
import asyncio
import logging
from datetime import datetime
import random

from ueba_monitor import UEBAMonitor, AgentBehaviorEvent, AgentAction, SecurityLevel
from ueba_integration import UEBAIntegration
from ueba_baseline_profiles import get_all_baseline_profiles, ANOMALY_DETECTION_CONFIG
from message_queue import InMemoryMessageQueue, TimeoutHandler


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def simulate_normal_behavior(ueba_integration: UEBAIntegration):
    """Simulate normal agent behavior"""
    print("\n" + "="*80)
    print("SCENARIO 1: Normal Agent Behavior")
    print("="*80)
    
    # Data Analysis Agent - Normal behavior
    for i in range(10):
        await ueba_integration.track_data_access(
            agent_id="data_analysis_agent",
            data_type="vehicle_data",
            data_id=f"VEH-{1000+i}",
            data_scope="vehicle_telemetry",
            success=True
        )
        await asyncio.sleep(0.1)
    
    print("✓ Data Analysis Agent: 10 normal data accesses")
    
    # Customer Engagement Agent - Normal behavior
    for i in range(5):
        await ueba_integration.track_api_call(
            agent_id="customer_engagement_agent",
            api_endpoint="/api/send_notification",
            success=True,
            response_code=200
        )
        await asyncio.sleep(0.1)
    
    print("✓ Customer Engagement Agent: 5 normal API calls")
    
    # Scheduling Agent - Normal behavior
    for i in range(3):
        await ueba_integration.track_booking_action(
            agent_id="scheduling_agent",
            action="create",
            booking_id=f"BOOK-{2000+i}",
            success=True
        )
        await asyncio.sleep(0.1)
    
    print("✓ Scheduling Agent: 3 normal bookings created")
    
    await asyncio.sleep(2)
    
    # Show statistics
    stats = ueba_integration.ueba_monitor.get_agent_statistics("data_analysis_agent")
    print(f"\nData Analysis Agent Stats:")
    print(f"  Total Events: {stats['total_events']}")
    print(f"  Success Rate: {stats['success_rate']*100:.1f}%")
    print(f"  Alerts: {stats['total_alerts']}")


async def simulate_unauthorized_access(ueba_integration: UEBAIntegration):
    """Simulate unauthorized data access"""
    print("\n" + "="*80)
    print("SCENARIO 2: Unauthorized Data Access")
    print("="*80)
    
    # Scheduling Agent trying to access manufacturing data (not authorized)
    print("\n⚠ Scheduling Agent attempting to access manufacturing data...")
    
    await ueba_integration.track_data_access(
        agent_id="scheduling_agent",
        data_type="manufacturing_data",  # NOT in authorized resources
        data_id="MFG-SECRET-001",
        data_scope="manufacturing_secrets",  # Forbidden scope
        success=True
    )
    
    await asyncio.sleep(1)
    
    # Check for alerts
    alerts = ueba_integration.ueba_monitor.get_all_alerts(
        agent_id="scheduling_agent",
        limit=5
    )
    
    if alerts:
        print(f"\n🚨 SECURITY ALERT TRIGGERED!")
        for alert in alerts[-2:]:
            print(f"  Alert ID: {alert.alert_id}")
            print(f"  Severity: {alert.severity}")
            print(f"  Type: {alert.anomaly_type}")
            print(f"  Description: {alert.description}")
            print(f"  Recommended Action: {alert.recommended_action}")


async def simulate_volume_spike(ueba_integration: UEBAIntegration):
    """Simulate unusual volume spike"""
    print("\n" + "="*80)
    print("SCENARIO 3: Volume Spike Anomaly")
    print("="*80)
    
    print("\n⚠ Data Analysis Agent making excessive API calls...")
    
    # Make 50 API calls in rapid succession (way above baseline)
    for i in range(50):
        await ueba_integration.track_api_call(
            agent_id="data_analysis_agent",
            api_endpoint="/api/analyze",
            success=True,
            response_code=200
        )
    
    await asyncio.sleep(1)
    
    # Check for alerts
    alerts = ueba_integration.ueba_monitor.get_all_alerts(
        agent_id="data_analysis_agent",
        limit=5
    )
    
    volume_alerts = [a for a in alerts if a.anomaly_type == "volume_spike"]
    
    if volume_alerts:
        print(f"\n🚨 VOLUME SPIKE DETECTED!")
        alert = volume_alerts[-1]
        print(f"  Alert ID: {alert.alert_id}")
        print(f"  Severity: {alert.severity}")
        print(f"  Description: {alert.description}")


async def simulate_failed_authentication(ueba_integration: UEBAIntegration):
    """Simulate failed authentication attempts"""
    print("\n" + "="*80)
    print("SCENARIO 4: Failed Authentication Attempts")
    print("="*80)
    
    print("\n⚠ Customer Engagement Agent: Multiple failed auth attempts...")
    
    # Simulate 4 failed authentication attempts
    for i in range(4):
        await ueba_integration.track_authentication(
            agent_id="customer_engagement_agent",
            success=False,
            auth_method="token"
        )
        print(f"  Failed attempt {i+1}")
        await asyncio.sleep(0.5)
    
    await asyncio.sleep(1)
    
    # Check if agent was blocked
    is_blocked = "customer_engagement_agent" in ueba_integration.ueba_monitor.blocked_agents
    
    if is_blocked:
        print(f"\n🔒 AGENT AUTO-BLOCKED!")
        print(f"  Agent: customer_engagement_agent")
        print(f"  Reason: Multiple failed authentication attempts")
    
    # Check for alerts
    alerts = ueba_integration.ueba_monitor.get_all_alerts(
        agent_id="customer_engagement_agent",
        limit=5
    )
    
    auth_alerts = [a for a in alerts if a.anomaly_type == "failed_auth"]
    
    if auth_alerts:
        alert = auth_alerts[-1]
        print(f"\n🚨 CRITICAL SECURITY ALERT!")
        print(f"  Alert ID: {alert.alert_id}")
        print(f"  Severity: {alert.severity}")
        print(f"  Description: {alert.description}")
        print(f"  Auto-Blocked: {alert.auto_blocked}")


async def simulate_suspicious_pattern(ueba_integration: UEBAIntegration):
    """Simulate suspicious booking pattern"""
    print("\n" + "="*80)
    print("SCENARIO 5: Suspicious Booking Pattern")
    print("="*80)
    
    print("\n⚠ Scheduling Agent: Repeated booking cancellations...")
    
    # Create and cancel bookings repeatedly
    for i in range(6):
        booking_id = f"BOOK-SUSPICIOUS-{i}"
        
        # Create booking
        await ueba_integration.track_booking_action(
            agent_id="scheduling_agent",
            action="create",
            booking_id=booking_id,
            success=True
        )
        
        # Immediately cancel it
        await ueba_integration.track_booking_action(
            agent_id="scheduling_agent",
            action="cancel",
            booking_id=booking_id,
            success=True
        )
        
        print(f"  Booking {i+1}: Created and cancelled")
        await asyncio.sleep(0.2)
    
    await asyncio.sleep(1)
    
    # Check for alerts
    alerts = ueba_integration.ueba_monitor.get_all_alerts(
        agent_id="scheduling_agent",
        limit=10
    )
    
    pattern_alerts = [a for a in alerts if a.anomaly_type == "suspicious_pattern"]
    
    if pattern_alerts:
        print(f"\n🚨 SUSPICIOUS PATTERN DETECTED!")
        alert = pattern_alerts[-1]
        print(f"  Alert ID: {alert.alert_id}")
        print(f"  Severity: {alert.severity}")
        print(f"  Description: {alert.description}")


async def simulate_unusual_hours(ueba_integration: UEBAIntegration):
    """Simulate activity during unusual hours"""
    print("\n" + "="*80)
    print("SCENARIO 6: Activity During Unusual Hours")
    print("="*80)
    
    print("\n⚠ Customer Engagement Agent active at 3 AM (outside business hours)...")
    
    # Create event with timestamp at 3 AM
    unusual_time = datetime.utcnow().replace(hour=3, minute=0, second=0)
    
    event = AgentBehaviorEvent(
        timestamp=unusual_time.isoformat(),
        agent_id="customer_engagement_agent",
        action_type=AgentAction.MESSAGE_SEND.value,
        resource_type="customer_data",
        resource_id="CUST-001",
        success=True,
        metadata={"hour": 3}
    )
    
    await ueba_integration.ueba_monitor.track_event(event)
    
    await asyncio.sleep(1)
    
    # Check for alerts
    alerts = ueba_integration.ueba_monitor.get_all_alerts(
        agent_id="customer_engagement_agent",
        limit=10
    )
    
    timing_alerts = [a for a in alerts if a.anomaly_type == "unusual_hours"]
    
    if timing_alerts:
        print(f"\n🚨 UNUSUAL HOURS ALERT!")
        alert = timing_alerts[-1]
        print(f"  Alert ID: {alert.alert_id}")
        print(f"  Severity: {alert.severity}")
        print(f"  Description: {alert.description}")


async def show_security_dashboard(ueba_integration: UEBAIntegration):
    """Display security dashboard"""
    print("\n" + "="*80)
    print("SECURITY DASHBOARD")
    print("="*80)
    
    dashboard = ueba_integration.get_system_security_dashboard()
    
    print(f"\nSystem Health: {dashboard['system_health']}")
    print(f"Total Agents: {dashboard['total_agents']}")
    print(f"Blocked Agents: {dashboard['blocked_agents']}")
    print(f"Total Alerts: {dashboard['total_alerts']}")
    
    print(f"\nAlerts by Severity:")
    for severity, count in dashboard['alert_counts_by_severity'].items():
        print(f"  {severity}: {count}")
    
    print(f"\nAgent Statistics:")
    for agent_id, stats in dashboard['agent_statistics'].items():
        print(f"\n  {agent_id}:")
        print(f"    Total Events: {stats['total_events']}")
        print(f"    Success Rate: {stats['success_rate']*100:.1f}%")
        print(f"    Total Alerts: {stats['total_alerts']}")
        print(f"    Blocked: {stats['is_blocked']}")
    
    if dashboard['recent_critical_alerts']:
        print(f"\nRecent Critical Alerts:")
        for alert in dashboard['recent_critical_alerts']:
            print(f"  - {alert['agent_id']}: {alert['description']}")


async def show_agent_security_report(ueba_integration: UEBAIntegration, agent_id: str):
    """Show detailed security report for an agent"""
    print("\n" + "="*80)
    print(f"SECURITY REPORT: {agent_id}")
    print("="*80)
    
    report = ueba_integration.get_agent_security_report(agent_id)
    
    print(f"\nRisk Level: {report['risk_level']}")
    print(f"Blocked: {report['is_blocked']}")
    
    stats = report['statistics']
    print(f"\nStatistics:")
    print(f"  Total Events: {stats['total_events']}")
    print(f"  Successful: {stats['successful_events']}")
    print(f"  Failed: {stats['failed_events']}")
    print(f"  Success Rate: {stats['success_rate']*100:.1f}%")
    
    if stats['action_counts']:
        print(f"\nAction Breakdown:")
        for action, count in stats['action_counts'].items():
            print(f"  {action}: {count}")
    
    if report['recent_alerts']:
        print(f"\nRecent Alerts ({len(report['recent_alerts'])}):")
        for alert in report['recent_alerts'][-5:]:
            print(f"  [{alert['severity']}] {alert['anomaly_type']}: {alert['description']}")


async def export_audit_data(ueba_integration: UEBAIntegration):
    """Export audit logs and alerts"""
    print("\n" + "="*80)
    print("EXPORTING AUDIT DATA")
    print("="*80)
    
    # Export audit log
    ueba_integration.ueba_monitor.export_audit_log("ueba_audit_log.json")
    print("✓ Audit log exported to: ueba_audit_log.json")
    
    # Export alerts
    ueba_integration.ueba_monitor.export_alerts("ueba_security_alerts.json")
    print("✓ Security alerts exported to: ueba_security_alerts.json")


async def main():
    """Main demo function"""
    print("="*80)
    print("UEBA MONITORING SYSTEM DEMO")
    print("Behavior Tracking, Anomaly Detection, and Security Alerts")
    print("="*80)
    
    # Initialize components
    message_queue = InMemoryMessageQueue()
    await message_queue.start()
    
    ueba_monitor = UEBAMonitor(
        window_size_minutes=ANOMALY_DETECTION_CONFIG["monitoring_window_minutes"],
        anomaly_threshold_std=ANOMALY_DETECTION_CONFIG["volume_spike_threshold_std"],
        auto_block_threshold=ANOMALY_DETECTION_CONFIG["auto_block_threshold"]
    )
    
    ueba_integration = UEBAIntegration(ueba_monitor, message_queue)
    await ueba_integration.start()
    
    print("\n✓ UEBA Monitor initialized and started")
    print("✓ Baseline profiles registered for all agents")
    
    # Run scenarios
    await simulate_normal_behavior(ueba_integration)
    await simulate_unauthorized_access(ueba_integration)
    await simulate_volume_spike(ueba_integration)
    await simulate_failed_authentication(ueba_integration)
    await simulate_suspicious_pattern(ueba_integration)
    await simulate_unusual_hours(ueba_integration)
    
    # Show dashboards and reports
    await show_security_dashboard(ueba_integration)
    await show_agent_security_report(ueba_integration, "scheduling_agent")
    
    # Export data
    await export_audit_data(ueba_integration)
    
    # Cleanup
    print("\n" + "="*80)
    print("DEMO COMPLETE")
    print("="*80)
    
    await ueba_integration.stop()
    await message_queue.stop()
    
    print("\n✓ UEBA Monitor stopped")
    print("✓ All audit data exported")


if __name__ == "__main__":
    asyncio.run(main())
