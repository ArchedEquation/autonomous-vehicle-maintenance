"""
Demo: Data Analysis Agent Integration with Master Orchestrator
Shows real-time telematics processing and workflow coordination
"""

import time
import json
from datetime import datetime, timedelta
import threading
import random

from data_analysis_agent import (
    DataAnalysisAgent,
    TelematicsReading,
    create_data_analysis_handler,
    RiskLevel
)
from master_orchestrator import MasterOrchestrator, AgentType


class TelematicsStreamSimulator:
    """
    Simulates real-time telematics stream from multiple vehicles
    In production, this would connect to actual IoT/telematics platform
    """
    
    def __init__(self, num_vehicles: int = 5):
        self.num_vehicles = num_vehicles
        self.vehicles = [f'VEH{str(i).zfill(3)}' for i in range(1, num_vehicles + 1)]
        self.running = False
        self.stream_thread = None
        self.callbacks = []
    
    def register_callback(self, callback):
        """Register callback for new readings"""
        self.callbacks.append(callback)
    
    def start_streaming(self, interval: float = 2.0):
        """Start streaming telematics data"""
        self.running = True
        self.stream_thread = threading.Thread(
            target=self._stream_loop,
            args=(interval,)
        )
        self.stream_thread.daemon = True
        self.stream_thread.start()
        print(f"Started streaming telematics for {self.num_vehicles} vehicles")
    
    def stop_streaming(self):
        """Stop streaming"""
        self.running = False
        if self.stream_thread:
            self.stream_thread.join(timeout=5)
        print("Stopped telematics streaming")
    
    def _stream_loop(self, interval: float):
        """Main streaming loop"""
        while self.running:
            # Generate reading for random vehicle
            vehicle_id = random.choice(self.vehicles)
            reading = self._generate_reading(vehicle_id)
            
            # Call all registered callbacks
            for callback in self.callbacks:
                callback(reading)
            
            time.sleep(interval)
    
    def _generate_reading(self, vehicle_id: str) -> TelematicsReading:
        """Generate realistic telematics reading"""
        # Determine if this should be a normal or anomalous reading
        is_anomalous = random.random() < 0.15  # 15% chance of anomaly
        
        if is_anomalous:
            return self._generate_anomalous_reading(vehicle_id)
        else:
            return self._generate_normal_reading(vehicle_id)
    
    def _generate_normal_reading(self, vehicle_id: str) -> TelematicsReading:
        """Generate normal telematics reading"""
        return TelematicsReading(
            vehicle_id=vehicle_id,
            timestamp=datetime.now(),
            engine_temp=random.uniform(85, 98),
            oil_pressure=random.uniform(40, 60),
            battery_voltage=random.uniform(12.4, 13.2),
            fuel_efficiency=random.uniform(24, 32),
            coolant_temp=random.uniform(82, 95),
            rpm=random.uniform(1500, 3000),
            speed=random.uniform(30, 80),
            brake_pressure=random.uniform(25, 40),
            tire_pressure_fl=random.uniform(31, 34),
            tire_pressure_fr=random.uniform(31, 34),
            tire_pressure_rl=random.uniform(31, 34),
            tire_pressure_rr=random.uniform(31, 34),
            transmission_temp=random.uniform(80, 92),
            throttle_position=random.uniform(30, 60),
            mileage=random.uniform(30000, 80000)
        )
    
    def _generate_anomalous_reading(self, vehicle_id: str) -> TelematicsReading:
        """Generate anomalous telematics reading"""
        anomaly_type = random.choice([
            'overheating',
            'battery_issue',
            'oil_pressure_low',
            'tire_pressure_low',
            'multiple_issues'
        ])
        
        reading = self._generate_normal_reading(vehicle_id)
        
        if anomaly_type == 'overheating':
            reading.engine_temp = random.uniform(105, 118)
            reading.coolant_temp = random.uniform(105, 115)
        elif anomaly_type == 'battery_issue':
            reading.battery_voltage = random.uniform(11.2, 11.8)
        elif anomaly_type == 'oil_pressure_low':
            reading.oil_pressure = random.uniform(18, 25)
        elif anomaly_type == 'tire_pressure_low':
            reading.tire_pressure_fl = random.uniform(24, 28)
            reading.tire_pressure_rr = random.uniform(24, 28)
        elif anomaly_type == 'multiple_issues':
            reading.engine_temp = random.uniform(102, 110)
            reading.battery_voltage = random.uniform(11.5, 11.9)
            reading.oil_pressure = random.uniform(22, 28)
        
        return reading


class IntegratedMaintenanceSystem:
    """
    Complete integrated system with Data Analysis Agent and Master Orchestrator
    """
    
    def __init__(self):
        # Initialize Data Analysis Agent
        self.data_agent = DataAnalysisAgent(
            model_path='deep_vae_full_model',
            scaler_path='scaler.pkl',
            baseline_window=50,
            anomaly_threshold=0.05
        )
        
        # Initialize Master Orchestrator
        self.orchestrator = MasterOrchestrator(max_workers=10)
        
        # Register Data Analysis Agent with orchestrator
        handler = create_data_analysis_handler(self.data_agent)
        self.orchestrator.register_agent(AgentType.DATA_ANALYSIS, handler)
        
        # Register mock agents for other stages
        self._register_mock_agents()
        
        # Telematics simulator
        self.simulator = TelematicsStreamSimulator(num_vehicles=5)
        
        # Statistics
        self.processed_count = 0
        self.high_risk_count = 0
        
        print("Integrated Maintenance System initialized")
    
    def _register_mock_agents(self):
        """Register mock agents for demonstration"""
        
        def mock_diagnosis_agent(payload):
            """Mock diagnosis agent"""
            analysis = payload.get('analysis_results', {})
            anomaly_score = analysis.get('anomaly_score', 0)
            
            return {
                'predicted_failures': ['brake_wear', 'battery_degradation'],
                'failure_probability': min(anomaly_score * 2, 0.95),
                'severity_score': min(anomaly_score * 1.5, 0.9),
                'estimated_days_to_failure': max(7, int(90 * (1 - anomaly_score))),
                'recommended_services': ['inspection', 'diagnostic_test']
            }
        
        def mock_customer_engagement_agent(payload):
            """Mock customer engagement agent"""
            return {
                'status': 'contacted',
                'customer_response': 'accepted',
                'preferred_date': (datetime.now() + timedelta(days=3)).isoformat()
            }
        
        def mock_scheduling_agent(payload):
            """Mock scheduling agent"""
            return {
                'options': [{
                    'datetime': datetime.now() + timedelta(days=3),
                    'service_center': 'Main Center',
                    'estimated_duration': 2,
                    'customer_preference_score': 0.8,
                    'service_center_load': 0.5
                }]
            }
        
        self.orchestrator.register_agent(AgentType.DIAGNOSIS, mock_diagnosis_agent)
        self.orchestrator.register_agent(AgentType.CUSTOMER_ENGAGEMENT, mock_customer_engagement_agent)
        self.orchestrator.register_agent(AgentType.SCHEDULING, mock_scheduling_agent)
    
    def start(self):
        """Start the integrated system"""
        print("\n" + "="*60)
        print("Starting Integrated Vehicle Maintenance System")
        print("="*60 + "\n")
        
        # Start Data Analysis Agent
        self.data_agent.start_processing()
        
        # Start Master Orchestrator
        self.orchestrator.start()
        
        # Register callback for telematics stream
        self.simulator.register_callback(self._handle_telematics_reading)
        
        # Start telematics stream
        self.simulator.start_streaming(interval=3.0)
        
        print("System started successfully\n")
    
    def _handle_telematics_reading(self, reading: TelematicsReading):
        """Handle incoming telematics reading"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Received telematics from {reading.vehicle_id}")
        
        # First, do quick analysis with Data Analysis Agent
        report = self.data_agent.analyze_reading(reading)
        
        print(f"  └─ Risk: {report.risk_level.value.upper()} | "
              f"Anomaly: {report.anomaly_score:.4f} | "
              f"Confidence: {report.confidence_score:.2f}")
        
        if report.detected_anomalies:
            print(f"  └─ Anomalies: {', '.join(report.detected_anomalies[:2])}")
        
        if report.recommendations:
            print(f"  └─ Recommendation: {report.recommendations[0]}")
        
        # Update statistics
        self.processed_count += 1
        if report.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            self.high_risk_count += 1
        
        # If risk is medium or higher, send to Master Orchestrator for full workflow
        if report.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]:
            print(f"  └─ ⚠️  Escalating to Master Orchestrator for full workflow")
            
            # Convert reading to telemetry dict
            telemetry_dict = reading.to_dict()
            
            # Send to orchestrator
            workflow_id = self.orchestrator.receive_vehicle_telemetry(
                reading.vehicle_id,
                telemetry_dict
            )
            
            print(f"  └─ Created workflow: {workflow_id[:8]}...")
    
    def get_system_status(self) -> dict:
        """Get comprehensive system status"""
        return {
            'data_agent': self.data_agent.get_statistics(),
            'orchestrator': self.orchestrator.get_statistics(),
            'processed_readings': self.processed_count,
            'high_risk_vehicles': self.high_risk_count,
            'timestamp': datetime.now().isoformat()
        }
    
    def stop(self):
        """Stop the integrated system"""
        print("\n" + "="*60)
        print("Stopping Integrated Vehicle Maintenance System")
        print("="*60 + "\n")
        
        # Stop telematics stream
        self.simulator.stop_streaming()
        
        # Stop Data Analysis Agent
        self.data_agent.stop_processing()
        
        # Orchestrator continues processing existing workflows
        print("System stopped\n")


def run_demo(duration_seconds: int = 30):
    """
    Run demonstration of integrated system
    
    Args:
        duration_seconds: How long to run the demo
    """
    print("\n" + "="*70)
    print(" VEHICLE MAINTENANCE MULTI-AGENT SYSTEM DEMO")
    print(" Real-Time Telematics Processing with Data Analysis Agent")
    print("="*70 + "\n")
    
    # Initialize system
    system = IntegratedMaintenanceSystem()
    
    # Start system
    system.start()
    
    # Run for specified duration
    print(f"Running demo for {duration_seconds} seconds...")
    print("Watch for real-time telematics processing and workflow creation\n")
    
    try:
        # Print status updates every 10 seconds
        for i in range(duration_seconds // 10):
            time.sleep(10)
            
            print("\n" + "-"*60)
            print(f"STATUS UPDATE ({(i+1)*10}s elapsed)")
            print("-"*60)
            
            status = system.get_system_status()
            
            print(f"Readings Processed: {status['processed_readings']}")
            print(f"High Risk Vehicles: {status['high_risk_vehicles']}")
            print(f"Anomalies Detected: {status['data_agent']['anomalies_detected']}")
            print(f"Active Workflows: {status['orchestrator']['active_workflows']}")
            print(f"Completed Workflows: {status['orchestrator']['completed']}")
            print("-"*60 + "\n")
        
        # Sleep remaining time
        remaining = duration_seconds % 10
        if remaining > 0:
            time.sleep(remaining)
    
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    
    # Stop system
    system.stop()
    
    # Final statistics
    print("\n" + "="*70)
    print(" FINAL STATISTICS")
    print("="*70 + "\n")
    
    final_status = system.get_system_status()
    
    print("Data Analysis Agent:")
    print(f"  Total Readings: {final_status['data_agent']['total_readings']}")
    print(f"  Anomalies Detected: {final_status['data_agent']['anomalies_detected']}")
    print(f"  Corrupted Readings: {final_status['data_agent']['corrupted_readings']}")
    print(f"  Vehicles Monitored: {final_status['data_agent']['vehicles_monitored']}")
    print(f"  Baselines Created: {final_status['data_agent']['vehicles_with_baselines']}")
    
    print("\nMaster Orchestrator:")
    print(f"  Total Workflows: {final_status['orchestrator']['total_workflows']}")
    print(f"  Completed: {final_status['orchestrator']['completed']}")
    print(f"  Failed: {final_status['orchestrator']['failed']}")
    print(f"  Urgent Cases: {final_status['orchestrator']['urgent_handled']}")
    print(f"  Active Workflows: {final_status['orchestrator']['active_workflows']}")
    
    print("\nSystem Performance:")
    print(f"  High Risk Detections: {final_status['high_risk_vehicles']}")
    print(f"  Detection Rate: {final_status['high_risk_vehicles']/max(final_status['processed_readings'],1)*100:.1f}%")
    
    print("\n" + "="*70)
    print(" Demo Complete!")
    print("="*70 + "\n")


def test_specific_scenarios():
    """Test specific scenarios with detailed output"""
    print("\n" + "="*70)
    print(" SCENARIO TESTING")
    print("="*70 + "\n")
    
    agent = DataAnalysisAgent()
    
    # Scenario 1: Critical overheating
    print("Scenario 1: Critical Engine Overheating")
    print("-" * 50)
    
    critical_reading = TelematicsReading(
        vehicle_id='TEST001',
        timestamp=datetime.now(),
        engine_temp=118.0,
        oil_pressure=20.0,
        battery_voltage=11.4,
        fuel_efficiency=12.0,
        coolant_temp=112.0,
        rpm=4500.0,
        speed=85.0,
        brake_pressure=45.0,
        tire_pressure_fl=32.0,
        tire_pressure_fr=32.0,
        tire_pressure_rl=32.0,
        tire_pressure_rr=32.0,
        transmission_temp=98.0,
        throttle_position=85.0,
        mileage=95000.0
    )
    
    report = agent.analyze_reading(critical_reading)
    print(json.dumps(report.to_dict(), indent=2, default=str))
    
    # Scenario 2: Gradual battery degradation
    print("\n\nScenario 2: Gradual Battery Degradation")
    print("-" * 50)
    
    # Simulate trend over time
    for i in range(5):
        reading = TelematicsReading(
            vehicle_id='TEST002',
            timestamp=datetime.now() + timedelta(hours=i),
            engine_temp=92.0,
            oil_pressure=45.0,
            battery_voltage=12.8 - (i * 0.3),  # Declining
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
            mileage=50000.0 + i * 100
        )
        
        report = agent.analyze_reading(reading)
        print(f"\nReading {i+1}: Battery={reading.battery_voltage:.1f}V, "
              f"Risk={report.risk_level.value}, "
              f"Trends={len(report.trending_parameters)}")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Run scenario tests
        test_specific_scenarios()
    else:
        # Run full demo
        duration = int(sys.argv[1]) if len(sys.argv) > 1 else 30
        run_demo(duration_seconds=duration)
