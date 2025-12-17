"""
Manufacturing Quality Insights Module Demo
Demonstrates RCA, CAPA generation, action tracking, and impact measurement
"""
import asyncio
import logging
from datetime import datetime, timedelta
import random

from manufacturing_insights_module import (
    ManufacturingInsightsModule,
    FailureSeverity,
    ActionStatus
)
from manufacturing_api_integration import ManufacturingAPIClient


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Sample data
VEHICLE_MODELS = ["Model S", "Model X", "Model 3", "Model Y"]
COMPONENTS = [
    "Engine", "Transmission", "Brake System", "Suspension",
    "Electrical System", "Cooling System", "Fuel System"
]
FAILURE_MODES = {
    "Engine": ["Overheating", "Oil Leak", "Misfire", "Knock"],
    "Transmission": ["Slipping", "Hard Shift", "Fluid Leak"],
    "Brake System": ["Pad Wear", "Rotor Warping", "Fluid Leak", "ABS Failure"],
    "Suspension": ["Strut Failure", "Spring Break", "Bushing Wear"],
    "Electrical System": ["Battery Failure", "Alternator Failure", "Wiring Issue"],
    "Cooling System": ["Radiator Leak", "Thermostat Failure", "Fan Failure"],
    "Fuel System": ["Pump Failure", "Injector Clog", "Tank Leak"]
}


async def generate_sample_failures(insights_module: ManufacturingInsightsModule):
    """Generate sample failure data"""
    print("\n" + "="*80)
    print("GENERATING SAMPLE FAILURE DATA")
    print("="*80)
    
    # Generate 100 failure records over 90 days
    for i in range(100):
        # Random vehicle
        model = random.choice(VEHICLE_MODELS)
        year = random.randint(2020, 2024)
        batch = f"BATCH-{year}-{random.randint(1, 12):02d}"
        vehicle_id = f"VEH-{random.randint(10000, 99999)}"
        
        # Random component and failure
        component = random.choice(COMPONENTS)
        failure_mode = random.choice(FAILURE_MODES[component])
        
        # Random severity (weighted towards lower severity)
        severity_weights = [0.5, 0.3, 0.15, 0.05]
        severity = random.choices(
            list(FailureSeverity),
            weights=severity_weights
        )[0]
        
        # Random mileage
        mileage = random.randint(5000, 150000)
        
        # Simulate some patterns
        # Pattern 1: Brake System issues in 2023 Model X
        if random.random() < 0.3 and model == "Model X" and year == 2023:
            component = "Brake System"
            failure_mode = "Pad Wear"
            severity = FailureSeverity.HIGH
        
        # Pattern 2: Engine overheating in specific batch
        if random.random() < 0.2 and batch == "BATCH-2022-06":
            component = "Engine"
            failure_mode = "Overheating"
            severity = FailureSeverity.CRITICAL
        
        await insights_module.ingest_failure_data(
            vehicle_id=vehicle_id,
            vehicle_model=model,
            vehicle_year=year,
            manufacturing_batch=batch,
            component=component,
            failure_mode=failure_mode,
            severity=severity,
            mileage=mileage,
            diagnosis_data={
                "diagnostic_code": f"DTC-{random.randint(1000, 9999)}",
                "technician_notes": f"Failure observed at {mileage} miles"
            },
            customer_feedback={
                "satisfaction": random.randint(1, 5),
                "comments": "Component failed unexpectedly"
            }
        )
    
    print(f"\n✓ Generated 100 failure records")



async def demonstrate_rca(insights_module: ManufacturingInsightsModule):
    """Demonstrate root cause analysis"""
    print("\n" + "="*80)
    print("PERFORMING ROOT CAUSE ANALYSIS")
    print("="*80)
    
    analyses = await insights_module.perform_root_cause_analysis(time_window_days=90)
    
    print(f"\n✓ Analyzed {len(analyses)} components")
    
    # Show top 5 components by failure rate
    sorted_components = sorted(
        analyses.items(),
        key=lambda x: x[1].failure_rate,
        reverse=True
    )[:5]
    
    print("\nTop 5 Components by Failure Rate:")
    for component, analysis in sorted_components:
        print(f"\n  {component}:")
        print(f"    Total Failures: {analysis.total_failures}")
        print(f"    Failure Rate: {analysis.failure_rate*100:.2f}%")
        print(f"    Trend: {analysis.trend}")
        print(f"    Avg Mileage at Failure: {analysis.avg_mileage_at_failure:,.0f} miles")
        print(f"    Common Failure Modes:")
        for mode, count in analysis.common_failure_modes[:3]:
            print(f"      - {mode}: {count} occurrences")
    
    return analyses


async def demonstrate_capa_generation(
    insights_module: ManufacturingInsightsModule,
    analyses: dict
):
    """Demonstrate CAPA report generation"""
    print("\n" + "="*80)
    print("GENERATING CAPA REPORTS")
    print("="*80)
    
    reports = await insights_module.generate_capa_reports(analyses)
    
    print(f"\n✓ Generated {len(reports)} CAPA reports")
    
    # Show details of each report
    for report in reports:
        print(f"\n{'='*80}")
        print(f"CAPA Report: {report.report_id}")
        print(f"{'='*80}")
        print(f"Component: {report.component}")
        print(f"Priority: {report.priority}")
        print(f"Severity: {report.severity}")
        print(f"Frequency: {report.frequency} failures")
        print(f"\nDefect Description:")
        print(f"  {report.defect_description}")
        print(f"\nRoot Cause:")
        print(f"  {report.root_cause}")
        print(f"\nAffected Vehicles:")
        print(f"  Models: {', '.join(report.affected_vehicle_models)}")
        print(f"  Years: {', '.join(map(str, report.affected_vehicle_years))}")
        print(f"  Estimated Affected: {report.estimated_vehicles_affected:,}")
        print(f"\nRecommended Actions:")
        for i, action in enumerate(report.recommended_actions[:5], 1):
            print(f"  {i}. {action}")
        if len(report.recommended_actions) > 5:
            print(f"  ... and {len(report.recommended_actions)-5} more actions")
    
    return reports



async def demonstrate_action_tracking(
    insights_module: ManufacturingInsightsModule,
    reports: list
):
    """Demonstrate action tracking"""
    print("\n" + "="*80)
    print("TRACKING CAPA ACTION IMPLEMENTATION")
    print("="*80)
    
    if not reports:
        print("\nNo CAPA reports to track")
        return
    
    # Track actions for first report
    report = reports[0]
    print(f"\nTracking actions for {report.report_id} ({report.component})")
    
    # Simulate action implementation
    actions = report.recommended_actions[:3]
    
    for i, action in enumerate(actions, 1):
        status = random.choice([
            ActionStatus.IN_PROGRESS,
            ActionStatus.COMPLETED
        ])
        
        await insights_module.track_action_implementation(
            report_id=report.report_id,
            action_description=action,
            status=status,
            assigned_to="Manufacturing Team A",
            completion_date=datetime.utcnow().isoformat() if status == ActionStatus.COMPLETED else None,
            notes=f"Action {i} {'completed' if status == ActionStatus.COMPLETED else 'in progress'}"
        )
        
        print(f"  ✓ Action {i}: {status.value}")
    
    # Show tracking status
    tracking = insights_module.action_tracking.get(report.report_id)
    if tracking:
        print(f"\nOverall Status: {tracking['overall_status']}")
        print(f"Actions Tracked: {len(tracking['actions'])}")


async def demonstrate_impact_measurement(
    insights_module: ManufacturingInsightsModule,
    reports: list
):
    """Demonstrate impact measurement"""
    print("\n" + "="*80)
    print("MEASURING IMPACT OF CAPA ACTIONS")
    print("="*80)
    
    if not reports:
        print("\nNo CAPA reports to measure")
        return
    
    # Simulate implementation and measurement for first report
    report = reports[0]
    
    # Mark as implemented
    report.status = ActionStatus.COMPLETED.value
    report.implementation_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
    
    print(f"\nMeasuring impact for {report.report_id} ({report.component})")
    print(f"Implementation Date: {report.implementation_date}")
    
    # Measure impact
    impact = await insights_module.measure_impact(
        report_id=report.report_id,
        measurement_period_days=30
    )
    
    if impact:
        print(f"\nImpact Measurement Results:")
        print(f"  Failures Before: {impact['failures_before']}")
        print(f"  Failures After: {impact['failures_after']}")
        print(f"  Reduction: {impact['reduction_count']} ({impact['reduction_percentage']:.1f}%)")
        print(f"  Effectiveness: {impact['effectiveness'].upper()}")



async def demonstrate_api_integration(
    insights_module: ManufacturingInsightsModule,
    reports: list
):
    """Demonstrate API integration"""
    print("\n" + "="*80)
    print("SENDING REPORTS TO MANUFACTURING TEAM")
    print("="*80)
    
    # Initialize API client
    api_client = ManufacturingAPIClient(
        api_base_url="https://manufacturing.example.com/api",
        api_key="demo-api-key",
        webhook_url="https://manufacturing.example.com/webhook"
    )
    
    # Send CAPA reports
    for report in reports[:2]:  # Send first 2 reports
        success = await api_client.send_capa_report(report.to_dict())
        if success:
            print(f"  ✓ Sent {report.report_id} to manufacturing team")
    
    # Send summary report
    summary = insights_module.generate_summary_report()
    success = await api_client.send_summary_report(summary)
    if success:
        print(f"  ✓ Sent summary report to manufacturing team")
    
    # Show dashboard data
    dashboard = api_client.get_dashboard_data()
    print(f"\nDashboard Status:")
    print(f"  Total Reports: {dashboard['total_reports']}")


async def demonstrate_summary_report(insights_module: ManufacturingInsightsModule):
    """Demonstrate summary report generation"""
    print("\n" + "="*80)
    print("GENERATING SUMMARY REPORT")
    print("="*80)
    
    summary = insights_module.generate_summary_report()
    
    print(f"\nQuality Insights Summary:")
    print(f"  Total Failure Records: {summary['total_failure_records']}")
    print(f"  Total CAPA Reports: {summary['total_capa_reports']}")
    
    print(f"\nCAPA Status Breakdown:")
    for status, count in summary['capa_status_breakdown'].items():
        print(f"  {status}: {count}")
    
    print(f"\nCAPA Priority Breakdown:")
    for priority, count in summary['capa_priority_breakdown'].items():
        print(f"  {priority}: {count}")
    
    print(f"\nTop 5 Failing Components:")
    for item in summary['top_failing_components'][:5]:
        print(f"  {item['component']}: {item['failures']} failures")
    
    print(f"\nImpact Summary:")
    impact = summary['impact_summary']
    print(f"  Measured CAPAs: {impact['measured_capas']}")
    print(f"  Total Failure Reduction: {impact['total_failure_reduction']}")
    print(f"  Avg Reduction per CAPA: {impact['avg_reduction_per_capa']:.1f}")


async def demonstrate_export(insights_module: ManufacturingInsightsModule):
    """Demonstrate data export"""
    print("\n" + "="*80)
    print("EXPORTING DATA")
    print("="*80)
    
    # Export CAPA reports
    insights_module.export_capa_reports("capa_reports.json")
    print("  ✓ Exported CAPA reports to capa_reports.json")
    
    # Export failure records
    insights_module.export_failure_records("failure_records.json", days=90)
    print("  ✓ Exported failure records to failure_records.json")
    
    # Export impact measurements
    insights_module.export_impact_measurements("impact_measurements.json")
    print("  ✓ Exported impact measurements to impact_measurements.json")



async def main():
    """Main demo function"""
    print("="*80)
    print("MANUFACTURING QUALITY INSIGHTS MODULE DEMO")
    print("Root Cause Analysis, CAPA Reports, and Impact Tracking")
    print("="*80)
    
    # Initialize module
    insights_module = ManufacturingInsightsModule(
        urgent_failure_threshold=10,
        critical_failure_rate=0.05,
        batch_analysis_schedule="weekly"
    )
    
    # Register callbacks
    async def urgent_alert_callback(component, failure_mode, count):
        print(f"\n🚨 URGENT ALERT: {component}/{failure_mode} - {count} failures!")
    
    async def report_callback(report):
        print(f"\n📋 New CAPA Report: {report.report_id} - {report.component}")
    
    insights_module.register_urgent_alert_callback(urgent_alert_callback)
    insights_module.register_report_callback(report_callback)
    
    await insights_module.start()
    
    print("\n✓ Manufacturing Insights Module started")
    
    # Run demonstrations
    await generate_sample_failures(insights_module)
    
    analyses = await demonstrate_rca(insights_module)
    
    reports = await demonstrate_capa_generation(insights_module, analyses)
    
    await demonstrate_action_tracking(insights_module, reports)
    
    await demonstrate_impact_measurement(insights_module, reports)
    
    await demonstrate_api_integration(insights_module, reports)
    
    await demonstrate_summary_report(insights_module)
    
    await demonstrate_export(insights_module)
    
    # Cleanup
    print("\n" + "="*80)
    print("DEMO COMPLETE")
    print("="*80)
    
    await insights_module.stop()
    
    print("\n✓ Manufacturing Insights Module stopped")
    print("\nKey Features Demonstrated:")
    print("  ✓ Failure data ingestion from diagnosis and feedback agents")
    print("  ✓ Root cause analysis with component-level insights")
    print("  ✓ Automated CAPA report generation")
    print("  ✓ Action implementation tracking")
    print("  ✓ Impact measurement of corrective actions")
    print("  ✓ API integration for manufacturing teams")
    print("  ✓ Summary reports and data export")
    print("  ✓ Urgent issue detection and alerting")


if __name__ == "__main__":
    asyncio.run(main())
