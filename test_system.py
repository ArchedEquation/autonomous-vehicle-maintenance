"""
Quick System Test - Verify all components are working
"""

import sys
from datetime import datetime

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    try:
        from master_orchestrator import MasterOrchestrator, AgentType, WorkflowState
        print("  ✓ Master Orchestrator imported")
    except Exception as e:
        print(f"  ✗ Master Orchestrator import failed: {e}")
        return False
    
    try:
        from data_analysis_agent import DataAnalysisAgent, TelematicsReading, RiskLevel
        print("  ✓ Data Analysis Agent imported")
    except Exception as e:
        print(f"  ✗ Data Analysis Agent import failed: {e}")
        return False
    
    try:
        from customer_engagement_agent import CustomerEngagementAgent, DiagnosticReport, CustomerProfile
        print("  ✓ Customer Engagement Agent imported")
    except Exception as e:
        print(f"  ✗ Customer Engagement Agent import failed: {e}")
        return False
    
    try:
        from scheduling_agent import SchedulingAgent, BookingRequest, UrgencyLevel
        print("  ✓ Scheduling Agent imported")
    except Exception as e:
        print(f"  ✗ Scheduling Agent import failed: {e}")
        return False
    
    try:
        from orchestrator_integration_example import VehicleMaintenanceAgentSystem
        print("  ✓ Integration Example imported")
    except Exception as e:
        print(f"  ✗ Integration Example import failed: {e}")
        return False
    
    try:
        from data_analysis_integration_demo import IntegratedMaintenanceSystem
        print("  ✓ Integration Demo imported")
    except Exception as e:
        print(f"  ✗ Integration Demo import failed: {e}")
        return False
    
    return True


def test_data_analysis_agent():
    """Test Data Analysis Agent basic functionality"""
    print("\nTesting Data Analysis Agent...")
    
    try:
        from data_analysis_agent import DataAnalysisAgent, TelematicsReading
        
        # Initialize agent
        agent = DataAnalysisAgent()
        print("  ✓ Agent initialized")
        
        # Create test reading
        reading = TelematicsReading(
            vehicle_id='TEST001',
            timestamp=datetime.now(),
            engine_temp=95.0,
            oil_pressure=45.0,
            battery_voltage=12.6,
            fuel_efficiency=28.0,
            coolant_temp=88.0,
            rpm=2000.0,
            speed=60.0,
            brake_pressure=30.0,
            tire_pressure_fl=32.0,
            tire_pressure_fr=32.0,
            tire_pressure_rl=32.0,
            tire_pressure_rr=32.0,
            transmission_temp=85.0,
            throttle_position=40.0,
            mileage=45000.0
        )
        print("  ✓ Test reading created")
        
        # Analyze reading
        report = agent.analyze_reading(reading)
        print(f"  ✓ Analysis completed: Risk={report.risk_level.value}, "
              f"Anomaly={report.anomaly_score:.4f}")
        
        # Check report structure
        assert report.vehicle_id == 'TEST001'
        assert report.risk_level is not None
        assert report.anomaly_score >= 0
        assert isinstance(report.recommendations, list)
        print("  ✓ Report structure validated")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Data Analysis Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_master_orchestrator():
    """Test Master Orchestrator basic functionality"""
    print("\nTesting Master Orchestrator...")
    
    try:
        from master_orchestrator import MasterOrchestrator, AgentType
        
        # Initialize orchestrator
        orchestrator = MasterOrchestrator(max_workers=5)
        print("  ✓ Orchestrator initialized")
        
        # Register mock agent
        def mock_agent(payload):
            return {'status': 'success', 'data': payload}
        
        orchestrator.register_agent(AgentType.DATA_ANALYSIS, mock_agent)
        print("  ✓ Mock agent registered")
        
        # Start orchestrator
        orchestrator.start()
        print("  ✓ Orchestrator started")
        
        # Create test workflow
        telemetry = {
            'vehicle_id': 'TEST001',
            'timestamp': datetime.now().isoformat(),
            'engine_temp': 95.0,
            'battery_voltage': 12.6
        }
        
        workflow_id = orchestrator.receive_vehicle_telemetry('TEST001', telemetry)
        print(f"  ✓ Workflow created: {workflow_id[:8]}...")
        
        # Get workflow status
        import time
        time.sleep(0.5)
        status = orchestrator.get_workflow_status(workflow_id)
        assert status is not None
        print(f"  ✓ Workflow status retrieved: {status['state']}")
        
        # Get statistics
        stats = orchestrator.get_statistics()
        assert stats['total_workflows'] > 0
        print(f"  ✓ Statistics retrieved: {stats['total_workflows']} workflows")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Master Orchestrator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_customer_engagement_agent():
    """Test Customer Engagement Agent basic functionality"""
    print("\nTesting Customer Engagement Agent...")
    
    try:
        from customer_engagement_agent import (
            CustomerEngagementAgent,
            DiagnosticReport,
            CustomerProfile,
            UrgencyLevel,
            CommunicationChannel
        )
        
        # Initialize agent
        agent = CustomerEngagementAgent()
        print("  ✓ Agent initialized")
        
        # Create test diagnostic report
        report = DiagnosticReport(
            vehicle_id='TEST001',
            customer_id='CUST001',
            urgency_level=UrgencyLevel.URGENT,
            issues_detected=['battery_degradation'],
            recommended_services=['battery_test', 'battery_replacement'],
            estimated_cost=200.00,
            risk_description='vehicle may not start',
            time_to_failure_days=7,
            safety_critical=False
        )
        print("  ✓ Diagnostic report created")
        
        # Create test customer profile
        customer = CustomerProfile(
            customer_id='CUST001',
            name='Test Customer',
            phone='+1-555-0100',
            email='test@example.com',
            preferred_channel=CommunicationChannel.PHONE_CALL,
            preferred_time='morning',
            communication_style='formal'
        )
        print("  ✓ Customer profile created")
        
        # Engage customer
        result = agent.engage_customer(report, customer)
        print(f"  ✓ Engagement completed: Outcome={result.outcome.value}")
        
        # Check result structure
        assert result.customer_id == 'CUST001'
        assert result.vehicle_id == 'TEST001'
        assert result.outcome is not None
        assert isinstance(result.conversation_transcript, list)
        print("  ✓ Result structure validated")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Customer Engagement Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scheduling_agent():
    """Test Scheduling Agent basic functionality"""
    print("\nTesting Scheduling Agent...")
    
    try:
        from scheduling_agent import (
            SchedulingAgent,
            BookingRequest,
            UrgencyLevel
        )
        
        # Initialize agent
        agent = SchedulingAgent()
        print("  ✓ Agent initialized")
        
        # Create test booking request
        request = BookingRequest(
            request_id="TEST001",
            vehicle_id="VEH001",
            customer_id="CUST001",
            urgency_level=UrgencyLevel.NORMAL,
            services_required=['oil_change', 'inspection'],
            estimated_duration=1.5,
            diagnostic_details={'issue': 'routine_maintenance'},
            customer_preferences={'preferred_time': 'morning'},
            parts_needed=['oil_filter'],
            customer_location={'lat': 40.7128, 'lon': -74.0060}
        )
        print("  ✓ Booking request created")
        
        # Schedule appointment
        result = agent.schedule_appointment(request)
        print(f"  ✓ Scheduling completed: Success={result.success}")
        
        # Check result structure
        if result.success:
            assert result.appointment is not None
            assert result.appointment.vehicle_id == 'VEH001'
            assert result.appointment.customer_id == 'CUST001'
            print("  ✓ Result structure validated")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Scheduling Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test integration between components"""
    print("\nTesting Component Integration...")
    
    try:
        from data_analysis_agent import DataAnalysisAgent, create_data_analysis_handler
        from customer_engagement_agent import CustomerEngagementAgent, create_customer_engagement_handler
        from master_orchestrator import MasterOrchestrator, AgentType
        
        # Initialize components
        data_agent = DataAnalysisAgent()
        engagement_agent = CustomerEngagementAgent()
        orchestrator = MasterOrchestrator(max_workers=5)
        print("  ✓ Components initialized")
        
        # Create and register handlers
        data_handler = create_data_analysis_handler(data_agent)
        engagement_handler = create_customer_engagement_handler(engagement_agent)
        orchestrator.register_agent(AgentType.DATA_ANALYSIS, data_handler)
        orchestrator.register_agent(AgentType.CUSTOMER_ENGAGEMENT, engagement_handler)
        print("  ✓ Handlers registered")
        
        # Start orchestrator
        orchestrator.start()
        print("  ✓ System started")
        
        # Test workflow
        telemetry = {
            'vehicle_id': 'TEST002',
            'timestamp': datetime.now().isoformat(),
            'engine_temp': 110.0,  # High temp
            'oil_pressure': 45.0,
            'battery_voltage': 12.6,
            'fuel_efficiency': 28.0,
            'coolant_temp': 105.0,  # High temp
            'rpm': 3000.0,
            'speed': 70.0,
            'brake_pressure': 35.0,
            'tire_pressure_fl': 32.0,
            'tire_pressure_fr': 32.0,
            'tire_pressure_rl': 32.0,
            'tire_pressure_rr': 32.0,
            'transmission_temp': 90.0,
            'throttle_position': 60.0,
            'mileage': 60000.0
        }
        
        workflow_id = orchestrator.receive_vehicle_telemetry('TEST002', telemetry)
        print(f"  ✓ Integrated workflow created: {workflow_id[:8]}...")
        
        # Wait for processing
        import time
        time.sleep(1)
        
        status = orchestrator.get_workflow_status(workflow_id)
        print(f"  ✓ Workflow processed: {status['state']}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ml_models():
    """Test ML model loading"""
    print("\nTesting ML Model Loading...")
    
    try:
        import os
        
        # Check for model files
        model_path = 'deep_vae_full_model'
        scaler_path = 'scaler.pkl'
        
        if os.path.exists(model_path):
            print(f"  ✓ VAE model found at {model_path}")
        else:
            print(f"  ⚠ VAE model not found at {model_path} (will use fallback)")
        
        if os.path.exists(scaler_path):
            print(f"  ✓ Scaler found at {scaler_path}")
        else:
            print(f"  ⚠ Scaler not found at {scaler_path} (will use fallback)")
        
        # Try loading with agent
        from data_analysis_agent import DataAnalysisAgent
        agent = DataAnalysisAgent()
        
        if agent.model is not None:
            print("  ✓ VAE model loaded successfully")
        else:
            print("  ⚠ VAE model not loaded (using fallback detection)")
        
        if agent.scaler is not None:
            print("  ✓ Scaler loaded successfully")
        else:
            print("  ⚠ Scaler not loaded (using fallback)")
        
        return True
        
    except Exception as e:
        print(f"  ⚠ ML model test warning: {e}")
        print("  → System will use rule-based fallback")
        return True  # Not critical


def run_all_tests():
    """Run all tests"""
    print("="*70)
    print(" VEHICLE MAINTENANCE MULTI-AGENT SYSTEM - SYSTEM TEST")
    print("="*70)
    print()
    
    results = []
    
    # Test imports
    results.append(("Imports", test_imports()))
    
    # Test Data Analysis Agent
    results.append(("Data Analysis Agent", test_data_analysis_agent()))
    
    # Test Customer Engagement Agent
    results.append(("Customer Engagement Agent", test_customer_engagement_agent()))
    
    # Test Scheduling Agent
    results.append(("Scheduling Agent", test_scheduling_agent()))
    
    # Test Master Orchestrator
    results.append(("Master Orchestrator", test_master_orchestrator()))
    
    # Test Integration
    results.append(("Component Integration", test_integration()))
    
    # Test ML Models (non-critical)
    results.append(("ML Models", test_ml_models()))
    
    # Summary
    print("\n" + "="*70)
    print(" TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("  1. Run demo: python data_analysis_integration_demo.py 30")
        print("  2. Read docs: QUICK_START_GUIDE.md")
        print("  3. Check examples in demo files")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("  1. Ensure all dependencies are installed: pip install -r requirements.txt")
        print("  2. Check that model files exist (or system will use fallback)")
        print("  3. Review error messages above")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
