"""
Main Orchestration Loop Demo
Demonstrates complete end-to-end workflow with all components
"""
import asyncio
import logging
from datetime import datetime
import time

from main_orchestration_loop import MainOrchestrationLoop


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_main_orchestration():
    """Demonstrate the main orchestration loop"""
    
    print("="*80)
    print("MAIN ORCHESTRATION LOOP DEMONSTRATION")
    print("="*80)
    print("\nThis demo shows the complete workflow:")
    print("1. Poll telematics API for vehicle data")
    print("2. Analyze data for anomalies and failures")
    print("3. Assess urgency level")
    print("4. Engage customers based on urgency")
    print("5. Schedule service appointments")
    print("6. Collect feedback")
    print("7. Feed data to manufacturing insights")
    print("8. UEBA monitors all actions in parallel")
    print("\n" + "="*80)
    
    # Create orchestration loop
    orchestrator = MainOrchestrationLoop(
        telematics_api_url="http://localhost:8000",
        scheduler_api_url="http://localhost:8001",
        polling_interval=10  # Poll every 10 seconds for demo
    )
    
    try:
        # Initialize all components
        print("\n[STEP 1] Initializing all components...")
        await orchestrator.initialize()
        
        # Start orchestration
        print("\n[STEP 2] Starting main orchestration loop...")
        await orchestrator.start()
        
        # Let it run for a while
        print("\n[STEP 3] Running orchestration loop...")
        print("The loop will:")
        print("  - Poll telemetry every 10 seconds")
        print("  - Process vehicle data through the workflow")
        print("  - Handle state transitions automatically")
        print("\nPress Ctrl+C to stop...\n")
        
        # Monitor for 2 minutes
        for i in range(12):  # 12 * 10 seconds = 2 minutes
            await asyncio.sleep(10)
            
            # Print statistics
            stats = orchestrator.get_statistics()
            print(f"\n{'='*80}")
            print(f"STATISTICS (after {(i+1)*10} seconds)")
            print(f"{'='*80}")
            print(f"Total vehicles processed: {stats['total_vehicles_processed']}")
            print(f"Active workflows: {stats['active_workflows']}")
            print(f"Completed workflows: {stats['completed_workflows']}")
            print(f"Customers engaged: {stats['customers_engaged']}")
            print(f"Appointments scheduled: {stats['appointments_scheduled']}")
            print(f"Errors encountered: {stats['errors_encountered']}")
            
            print(f"\nWorkflow states:")
            for state, count in stats['workflow_states'].items():
                if count > 0:
                    print(f"  {state}: {count}")
            
            # Show active workflows
            if orchestrator.active_workflows:
                print(f"\nActive workflows:")
                for vin, workflow in list(orchestrator.active_workflows.items())[:5]:
                    print(f"  {vin}: {workflow.state.value}")
                    if workflow.urgency_level:
                        print(f"    Urgency: {workflow.urgency_level.value}")
        
        print("\n[STEP 4] Demo complete!")
        
        # Final statistics
        print("\n" + "="*80)
        print("FINAL STATISTICS")
        print("="*80)
        stats = orchestrator.get_statistics()
        for key, value in stats.items():
            if key != 'workflow_states':
                print(f"{key}: {value}")
        
        # Show UEBA dashboard
        print("\n" + "="*80)
        print("UEBA SECURITY DASHBOARD")
        print("="*80)
        dashboard = orchestrator.ueba_integration.get_system_security_dashboard()
        print(f"System Health: {dashboard['system_health']}")
        print(f"Total Agents: {dashboard['total_agents']}")
        print(f"Blocked Agents: {dashboard['blocked_agents']}")
        print(f"Total Alerts: {dashboard['total_alerts']}")
        print(f"\nAlert Counts by Severity:")
        for severity, count in dashboard['alert_counts_by_severity'].items():
            if count > 0:
                print(f"  {severity}: {count}")
        
        # Show manufacturing insights
        print("\n" + "="*80)
        print("MANUFACTURING INSIGHTS")
        print("="*80)
        insights_summary = orchestrator.manufacturing_insights.generate_summary_report()
        print(f"Total failure records: {insights_summary['total_failure_records']}")
        print(f"Total CAPA reports: {insights_summary['total_capa_reports']}")
        print(f"Pending CAPAs: {insights_summary['pending_capas']}")
        print(f"Completed CAPAs: {insights_summary['completed_capas']}")
        
        if insights_summary['top_failing_components']:
            print(f"\nTop failing components:")
            for component, count in insights_summary['top_failing_components'][:5]:
                print(f"  {component}: {count} failures")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    
    except Exception as e:
        logger.error(f"Error in demo: {e}", exc_info=True)
    
    finally:
        # Stop orchestration
        print("\n[CLEANUP] Stopping orchestration loop...")
        await orchestrator.stop()
        print("✓ Orchestration loop stopped")


async def demo_single_vehicle_workflow():
    """Demonstrate workflow for a single vehicle"""
    
    print("="*80)
    print("SINGLE VEHICLE WORKFLOW DEMONSTRATION")
    print("="*80)
    
    orchestrator = MainOrchestrationLoop(
        telematics_api_url="http://localhost:8000",
        scheduler_api_url="http://localhost:8001",
        polling_interval=5
    )
    
    try:
        # Initialize
        await orchestrator.initialize()
        await orchestrator.start()
        
        # Monitor a specific vehicle
        target_vin = None
        
        print("\nWaiting for vehicle data...")
        
        # Wait for first vehicle
        for _ in range(20):  # Wait up to 100 seconds
            await asyncio.sleep(5)
            
            if orchestrator.vehicle_workflows:
                target_vin = list(orchestrator.vehicle_workflows.keys())[0]
                break
        
        if not target_vin:
            print("No vehicles detected")
            return
        
        print(f"\nTracking vehicle: {target_vin}")
        print("="*80)
        
        # Monitor workflow progress
        last_state = None
        
        for _ in range(60):  # Monitor for up to 5 minutes
            await asyncio.sleep(5)
            
            status = orchestrator.get_workflow_status(target_vin)
            
            if not status:
                print(f"\nWorkflow for {target_vin} not found")
                break
            
            current_state = status['state']
            
            if current_state != last_state:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] State: {current_state}")
                
                if status['urgency_level']:
                    print(f"  Urgency: {status['urgency_level']}")
                
                if status['analysis_result']:
                    print(f"  Analysis: {status['analysis_result'].get('anomaly_detected', False)}")
                    failures = status['analysis_result'].get('predicted_failures', [])
                    if failures:
                        print(f"  Predicted failures: {len(failures)}")
                
                if status['customer_response']:
                    print(f"  Customer response: {status['customer_response'].get('decision', 'unknown')}")
                
                if status['appointment']:
                    print(f"  Appointment: {status['appointment'].get('appointment_id', 'unknown')}")
                
                last_state = current_state
            
            # Check if completed
            if current_state == 'completed':
                print(f"\n✓ Workflow completed!")
                print(f"\nState history:")
                for transition in status['state_history']:
                    print(f"  {transition['from_state']} → {transition['to_state']}: {transition['reason']}")
                break
        
    finally:
        await orchestrator.stop()


async def demo_error_handling():
    """Demonstrate error handling and retry logic"""
    
    print("="*80)
    print("ERROR HANDLING DEMONSTRATION")
    print("="*80)
    print("\nThis demo shows how the orchestrator handles:")
    print("1. API timeouts")
    print("2. Agent failures")
    print("3. Customer no-response")
    print("4. Retry logic")
    print("="*80)
    
    orchestrator = MainOrchestrationLoop(
        telematics_api_url="http://localhost:9999",  # Invalid URL to trigger errors
        scheduler_api_url="http://localhost:8001",
        polling_interval=5
    )
    
    try:
        await orchestrator.initialize()
        await orchestrator.start()
        
        print("\nRunning with invalid telemetry API URL...")
        print("Expecting connection errors...\n")
        
        # Run for 30 seconds
        for i in range(6):
            await asyncio.sleep(5)
            
            stats = orchestrator.get_statistics()
            print(f"[{i*5}s] Errors encountered: {stats['errors_encountered']}")
        
        print("\n✓ Error handling working correctly")
        
    finally:
        await orchestrator.stop()


async def main():
    """Main demo entry point"""
    
    print("\n" + "="*80)
    print("MAIN ORCHESTRATION LOOP - DEMO SUITE")
    print("="*80)
    print("\nAvailable demos:")
    print("1. Full orchestration loop (2 minutes)")
    print("2. Single vehicle workflow tracking")
    print("3. Error handling demonstration")
    print("\nNOTE: Make sure the following services are running:")
    print("  - Telematics API (port 8000)")
    print("  - Service Scheduler API (port 8001)")
    print("\nTo start services:")
    print("  python mock_infrastructure/telematics_api.py")
    print("  python mock_infrastructure/service_scheduler_api.py")
    print("="*80)
    
    # Run full demo
    await demo_main_orchestration()
    
    # Uncomment to run other demos:
    # await demo_single_vehicle_workflow()
    # await demo_error_handling()


if __name__ == "__main__":
    asyncio.run(main())
