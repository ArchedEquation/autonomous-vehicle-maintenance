"""
Integration Example: Master Orchestrator with Existing ML Models
Demonstrates how to connect the orchestrator with actual ML models
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import pickle
import json
from master_orchestrator import (
    MasterOrchestrator, 
    AgentType, 
    WorkflowState,
    TaskPriority
)

# Import ML models (adjust paths as needed)
try:
    from tensorflow import keras
    import tensorflow as tf
except ImportError:
    print("TensorFlow not available - using mock implementations")
    keras = None


class VehicleMaintenanceAgentSystem:
    """
    Complete agent system integrating ML models with the orchestrator
    """
    
    def __init__(self):
        self.orchestrator = MasterOrchestrator(max_workers=10)
        
        # Load ML models
        self.load_models()
        
        # Register agents
        self.register_all_agents()
        
        print("Vehicle Maintenance Agent System initialized")
    
    def load_models(self):
        """Load all ML models"""
        try:
            # Load anomaly detection model (VAE)
            self.anomaly_model = keras.models.load_model('deep_vae_full_model')
            with open('scaler.pkl', 'rb') as f:
                self.scaler = pickle.load(f)
            print("Loaded anomaly detection model")
        except Exception as e:
            print(f"Could not load anomaly model: {e}")
            self.anomaly_model = None
            self.scaler = None
        
        try:
            # Load failure prediction model
            self.failure_model = keras.models.load_model(
                'weights_and_metadata/vehicle_failure_lstm_optimized.keras'
            )
            print("Loaded failure prediction model")
        except Exception as e:
            print(f"Could not load failure model: {e}")
            self.failure_model = None
        
        try:
            # Load service center load prediction model
            self.load_model = keras.models.load_model(
                'weights_and_metadata/service_load_lstm_model.weights.h5'
            )
            print("Loaded service center load model")
        except Exception as e:
            print(f"Could not load service center model: {e}")
            self.load_model = None
    
    def register_all_agents(self):
        """Register all agent handlers with the orchestrator"""
        self.orchestrator.register_agent(
            AgentType.DATA_ANALYSIS, 
            self.data_analysis_agent
        )
        self.orchestrator.register_agent(
            AgentType.DIAGNOSIS, 
            self.diagnosis_agent
        )
        self.orchestrator.register_agent(
            AgentType.CUSTOMER_ENGAGEMENT, 
            self.customer_engagement_agent
        )
        self.orchestrator.register_agent(
            AgentType.SCHEDULING, 
            self.scheduling_agent
        )
        self.orchestrator.register_agent(
            AgentType.FEEDBACK, 
            self.feedback_agent
        )
        self.orchestrator.register_agent(
            AgentType.MANUFACTURING_QUALITY, 
            self.manufacturing_quality_agent
        )
    
    def data_analysis_agent(self, payload: dict) -> dict:
        """
        Data Analysis Agent: Processes telemetry and detects anomalies
        Uses VAE model for anomaly detection
        """
        telemetry_data = payload['telemetry_data']
        vehicle_id = payload['vehicle_id']
        
        print(f"[Data Analysis Agent] Processing vehicle {vehicle_id}")
        
        # Prepare sensor data
        sensor_features = self._extract_sensor_features(telemetry_data)
        
        # Detect anomalies using VAE
        if self.anomaly_model and self.scaler:
            try:
                # Scale features
                scaled_features = self.scaler.transform([sensor_features])
                
                # Get reconstruction
                reconstruction = self.anomaly_model.predict(scaled_features, verbose=0)
                
                # Calculate reconstruction error
                mse = np.mean(np.square(scaled_features - reconstruction))
                
                # Threshold for anomaly (tune based on your data)
                anomaly_threshold = 0.05
                is_anomaly = mse > anomaly_threshold
                
                anomalies_detected = int(is_anomaly)
                confidence_score = min(mse / anomaly_threshold, 1.0) if is_anomaly else 0.0
                
            except Exception as e:
                print(f"Error in anomaly detection: {e}")
                anomalies_detected = 0
                confidence_score = 0.5
        else:
            # Fallback: rule-based anomaly detection
            anomalies_detected = self._rule_based_anomaly_detection(telemetry_data)
            confidence_score = 0.7 if anomalies_detected > 0 else 0.3
        
        return {
            'anomalies_detected': anomalies_detected,
            'confidence_score': confidence_score,
            'sensor_readings': sensor_features,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def diagnosis_agent(self, payload: dict) -> dict:
        """
        Diagnosis Agent: Predicts failures and recommends services
        Uses LSTM failure prediction model
        """
        vehicle_id = payload['vehicle_id']
        analysis_results = payload['analysis_results']
        telemetry_data = payload['telemetry_data']
        
        print(f"[Diagnosis Agent] Diagnosing vehicle {vehicle_id}")
        
        # Prepare sequence data for LSTM
        sensor_sequence = self._prepare_sequence_data(telemetry_data)
        
        # Predict failures
        if self.failure_model:
            try:
                # Predict failure probability
                prediction = self.failure_model.predict(sensor_sequence, verbose=0)
                failure_probability = float(prediction[0][0])
                
                # Estimate time to failure based on probability
                if failure_probability > 0.8:
                    estimated_days = 7
                elif failure_probability > 0.6:
                    estimated_days = 30
                elif failure_probability > 0.4:
                    estimated_days = 90
                else:
                    estimated_days = 180
                
            except Exception as e:
                print(f"Error in failure prediction: {e}")
                failure_probability = 0.5
                estimated_days = 60
        else:
            # Fallback: rule-based diagnosis
            failure_probability = self._rule_based_failure_prediction(telemetry_data)
            estimated_days = int(180 * (1 - failure_probability))
        
        # Identify specific failure types
        predicted_failures = self._identify_failure_types(telemetry_data, failure_probability)
        
        # Calculate severity
        severity_score = self._calculate_severity(predicted_failures, failure_probability)
        
        # Recommend services
        recommended_services = self._recommend_services(predicted_failures)
        
        return {
            'predicted_failures': predicted_failures,
            'failure_probability': failure_probability,
            'severity_score': severity_score,
            'estimated_days_to_failure': estimated_days,
            'recommended_services': recommended_services,
            'diagnosis_timestamp': datetime.now().isoformat()
        }
    
    def customer_engagement_agent(self, payload: dict) -> dict:
        """
        Customer Engagement Agent: Contacts customer and gathers preferences
        In production, this would integrate with CRM, SMS, email systems
        """
        vehicle_id = payload['vehicle_id']
        diagnosis_results = payload['diagnosis_results']
        urgency_score = payload.get('urgency_score', 0)
        immediate = payload.get('immediate', False)
        
        print(f"[Customer Engagement Agent] Contacting customer for vehicle {vehicle_id}")
        
        # Determine communication channel based on urgency
        if immediate or urgency_score > 0.7:
            channel = 'phone_call'
            priority = 'immediate'
        elif urgency_score > 0.4:
            channel = 'sms'
            priority = 'high'
        else:
            channel = 'email'
            priority = 'normal'
        
        # Simulate customer contact (in production, integrate with actual systems)
        message = self._generate_customer_message(diagnosis_results, urgency_score)
        
        # Simulate customer response
        customer_response = self._simulate_customer_response(urgency_score)
        
        # Get customer preferences
        preferred_date = self._get_customer_preferred_date(urgency_score)
        
        return {
            'status': 'contacted',
            'channel': channel,
            'priority': priority,
            'message_sent': message,
            'customer_response': customer_response,
            'preferred_date': preferred_date,
            'customer_preferences': {
                'preferred_time': 'morning',
                'preferred_service_center': 'nearest',
                'loaner_vehicle_needed': urgency_score > 0.6
            },
            'engagement_timestamp': datetime.now().isoformat()
        }
    
    def scheduling_agent(self, payload: dict) -> dict:
        """
        Scheduling Agent: Finds optimal appointment slots
        Uses service center load prediction model
        """
        vehicle_id = payload['vehicle_id']
        diagnosis_results = payload['diagnosis_results']
        customer_preferences = payload.get('customer_preferences', {})
        urgency_score = payload.get('urgency_score', 0)
        
        print(f"[Scheduling Agent] Finding appointment slots for vehicle {vehicle_id}")
        
        # Get available service centers
        service_centers = self._get_available_service_centers()
        
        # Generate scheduling options
        options = []
        
        for center in service_centers:
            # Predict service center load
            load_prediction = self._predict_service_center_load(center)
            
            # Generate time slots
            slots = self._generate_time_slots(center, urgency_score, customer_preferences)
            
            for slot in slots:
                # Calculate scores
                preference_score = self._calculate_preference_score(
                    slot, customer_preferences
                )
                
                options.append({
                    'datetime': slot['datetime'],
                    'service_center': center['name'],
                    'service_center_id': center['id'],
                    'estimated_duration': self._estimate_service_duration(
                        diagnosis_results['recommended_services']
                    ),
                    'customer_preference_score': preference_score,
                    'service_center_load': load_prediction,
                    'available_technicians': slot['available_technicians'],
                    'loaner_vehicle_available': slot['loaner_available']
                })
        
        # Sort by overall score
        options.sort(key=lambda x: (
            x['customer_preference_score'] * 0.6 + 
            (1 - x['service_center_load']) * 0.4
        ), reverse=True)
        
        return {
            'options': options[:5],  # Return top 5 options
            'scheduling_timestamp': datetime.now().isoformat()
        }
    
    def feedback_agent(self, payload: dict) -> dict:
        """
        Feedback Agent: Collects post-service feedback
        In production, integrates with survey systems and sentiment analysis
        """
        vehicle_id = payload['vehicle_id']
        service_results = payload['service_results']
        
        print(f"[Feedback Agent] Collecting feedback for vehicle {vehicle_id}")
        
        # Simulate feedback collection (in production, send surveys)
        feedback = self._simulate_customer_feedback(service_results)
        
        # Analyze sentiment (could use the sentiment analysis model)
        sentiment_score = self._analyze_feedback_sentiment(feedback['comments'])
        
        return {
            'satisfaction_score': feedback['satisfaction_score'],
            'comments': feedback['comments'],
            'would_recommend': feedback['would_recommend'],
            'sentiment_score': sentiment_score,
            'service_quality_rating': feedback['service_quality'],
            'timeliness_rating': feedback['timeliness'],
            'feedback_timestamp': datetime.now().isoformat()
        }
    
    def manufacturing_quality_agent(self, payload: dict) -> dict:
        """
        Manufacturing Quality Agent: Analyzes patterns for quality improvement
        Feeds data back to manufacturing for defect prevention
        """
        vehicle_id = payload['vehicle_id']
        diagnosis_results = payload['diagnosis_results']
        
        print(f"[Manufacturing Quality Agent] Analyzing patterns for vehicle {vehicle_id}")
        
        # Extract vehicle metadata
        vehicle_metadata = self._extract_vehicle_metadata(vehicle_id)
        
        # Identify patterns
        patterns = self._identify_quality_patterns(
            vehicle_metadata,
            diagnosis_results
        )
        
        # Generate quality report
        quality_report = {
            'vehicle_model': vehicle_metadata['model'],
            'manufacturing_date': vehicle_metadata['manufacturing_date'],
            'identified_patterns': patterns,
            'defect_categories': self._categorize_defects(diagnosis_results),
            'recommended_improvements': self._recommend_manufacturing_improvements(patterns),
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        return quality_report
    
    # Helper methods
    
    def _extract_sensor_features(self, telemetry_data: dict) -> list:
        """Extract numerical sensor features from telemetry"""
        features = [
            telemetry_data.get('engine_temp', 90),
            telemetry_data.get('brake_wear', 0.5),
            telemetry_data.get('battery_voltage', 12.6),
            telemetry_data.get('tire_pressure', 32),
            telemetry_data.get('oil_pressure', 40),
            telemetry_data.get('coolant_level', 100),
            telemetry_data.get('transmission_temp', 80),
            telemetry_data.get('mileage', 50000) / 1000  # Normalize
        ]
        return features
    
    def _rule_based_anomaly_detection(self, telemetry_data: dict) -> int:
        """Simple rule-based anomaly detection"""
        anomalies = 0
        
        if telemetry_data.get('engine_temp', 90) > 105:
            anomalies += 1
        if telemetry_data.get('brake_wear', 0) > 0.8:
            anomalies += 1
        if telemetry_data.get('battery_voltage', 12.6) < 11.5:
            anomalies += 1
        if telemetry_data.get('check_engine_light', False):
            anomalies += 1
        
        return anomalies
    
    def _prepare_sequence_data(self, telemetry_data: dict) -> np.ndarray:
        """Prepare sequence data for LSTM model"""
        # In production, this would use historical data
        # For now, create a simple sequence
        features = self._extract_sensor_features(telemetry_data)
        sequence = np.array([features] * 10)  # Simulate 10 time steps
        return sequence.reshape(1, 10, len(features))
    
    def _rule_based_failure_prediction(self, telemetry_data: dict) -> float:
        """Rule-based failure probability"""
        score = 0.0
        
        if telemetry_data.get('brake_wear', 0) > 0.7:
            score += 0.3
        if telemetry_data.get('battery_voltage', 12.6) < 12.0:
            score += 0.2
        if telemetry_data.get('engine_temp', 90) > 100:
            score += 0.2
        if telemetry_data.get('check_engine_light', False):
            score += 0.3
        
        return min(score, 1.0)
    
    def _identify_failure_types(self, telemetry_data: dict, probability: float) -> list:
        """Identify specific failure types"""
        failures = []
        
        if telemetry_data.get('brake_wear', 0) > 0.7:
            failures.append('brake_pad_wear')
        if telemetry_data.get('battery_voltage', 12.6) < 12.0:
            failures.append('battery_degradation')
        if telemetry_data.get('engine_temp', 90) > 100:
            failures.append('cooling_system_issue')
        if telemetry_data.get('check_engine_light', False):
            failures.append('engine_diagnostic_required')
        
        return failures if failures else ['general_maintenance']
    
    def _calculate_severity(self, failures: list, probability: float) -> float:
        """Calculate severity score"""
        critical_failures = ['brake_failure', 'steering_failure', 'engine_critical']
        
        if any(f in critical_failures for f in failures):
            return 0.9
        
        return min(probability * len(failures) * 0.3, 1.0)
    
    def _recommend_services(self, failures: list) -> list:
        """Recommend services based on failures"""
        service_map = {
            'brake_pad_wear': 'brake_inspection_and_replacement',
            'battery_degradation': 'battery_test_and_replacement',
            'cooling_system_issue': 'cooling_system_service',
            'engine_diagnostic_required': 'engine_diagnostic',
            'general_maintenance': 'routine_maintenance'
        }
        
        return [service_map.get(f, 'inspection') for f in failures]
    
    def _generate_customer_message(self, diagnosis: dict, urgency: float) -> str:
        """Generate customer notification message"""
        if urgency > 0.7:
            return f"URGENT: Your vehicle requires immediate attention. Predicted issues: {', '.join(diagnosis['predicted_failures'])}"
        else:
            return f"Maintenance recommended for your vehicle. Services needed: {', '.join(diagnosis['recommended_services'])}"
    
    def _simulate_customer_response(self, urgency: float) -> str:
        """Simulate customer response"""
        return 'accepted' if urgency > 0.5 else 'will_call_back'
    
    def _get_customer_preferred_date(self, urgency: float) -> str:
        """Get customer preferred date"""
        days_ahead = 2 if urgency > 0.7 else 7
        return (datetime.now() + timedelta(days=days_ahead)).isoformat()
    
    def _get_available_service_centers(self) -> list:
        """Get available service centers"""
        return [
            {'id': 'SC001', 'name': 'Downtown Service Center', 'location': 'downtown'},
            {'id': 'SC002', 'name': 'North Branch', 'location': 'north'},
            {'id': 'SC003', 'name': 'South Branch', 'location': 'south'}
        ]
    
    def _predict_service_center_load(self, center: dict) -> float:
        """Predict service center load"""
        # In production, use the load prediction model
        return np.random.uniform(0.3, 0.8)
    
    def _generate_time_slots(self, center: dict, urgency: float, preferences: dict) -> list:
        """Generate available time slots"""
        slots = []
        start_date = datetime.now() + timedelta(days=1 if urgency > 0.7 else 3)
        
        for day in range(5):
            date = start_date + timedelta(days=day)
            for hour in [9, 11, 14, 16]:
                slots.append({
                    'datetime': date.replace(hour=hour, minute=0),
                    'available_technicians': np.random.randint(1, 4),
                    'loaner_available': np.random.choice([True, False])
                })
        
        return slots
    
    def _calculate_preference_score(self, slot: dict, preferences: dict) -> float:
        """Calculate how well slot matches customer preferences"""
        score = 0.5  # Base score
        
        if preferences.get('preferred_time') == 'morning' and slot['datetime'].hour < 12:
            score += 0.3
        if preferences.get('loaner_vehicle_needed') and slot['loaner_available']:
            score += 0.2
        
        return min(score, 1.0)
    
    def _estimate_service_duration(self, services: list) -> float:
        """Estimate service duration in hours"""
        duration_map = {
            'brake_inspection_and_replacement': 2.0,
            'battery_test_and_replacement': 1.0,
            'cooling_system_service': 2.5,
            'engine_diagnostic': 1.5,
            'routine_maintenance': 1.0
        }
        
        return sum(duration_map.get(s, 1.0) for s in services)
    
    def _simulate_customer_feedback(self, service_results: dict) -> dict:
        """Simulate customer feedback"""
        return {
            'satisfaction_score': np.random.uniform(3.5, 5.0),
            'comments': 'Service was professional and timely',
            'would_recommend': True,
            'service_quality': np.random.uniform(3.5, 5.0),
            'timeliness': np.random.uniform(3.5, 5.0)
        }
    
    def _analyze_feedback_sentiment(self, comments: str) -> float:
        """Analyze sentiment of feedback comments"""
        # In production, use the sentiment analysis model
        positive_words = ['good', 'great', 'excellent', 'professional', 'timely']
        score = sum(1 for word in positive_words if word in comments.lower())
        return min(score / len(positive_words), 1.0)
    
    def _extract_vehicle_metadata(self, vehicle_id: str) -> dict:
        """Extract vehicle metadata"""
        return {
            'model': 'Model X',
            'manufacturing_date': '2020-06-15',
            'vin': vehicle_id,
            'production_plant': 'Plant A'
        }
    
    def _identify_quality_patterns(self, metadata: dict, diagnosis: dict) -> list:
        """Identify quality patterns"""
        return [
            {
                'pattern': 'brake_wear_pattern',
                'frequency': 'common',
                'affected_models': [metadata['model']]
            }
        ]
    
    def _categorize_defects(self, diagnosis: dict) -> list:
        """Categorize defects"""
        return ['wear_and_tear', 'electrical_system']
    
    def _recommend_manufacturing_improvements(self, patterns: list) -> list:
        """Recommend manufacturing improvements"""
        return ['improve_brake_pad_quality', 'enhance_battery_testing']
    
    def start(self):
        """Start the agent system"""
        self.orchestrator.start()
        print("Vehicle Maintenance Agent System started")
    
    def process_vehicle(self, vehicle_id: str, telemetry_data: dict) -> str:
        """Process a vehicle through the system"""
        return self.orchestrator.receive_vehicle_telemetry(vehicle_id, telemetry_data)
    
    def get_workflow_status(self, workflow_id: str) -> dict:
        """Get workflow status"""
        return self.orchestrator.get_workflow_status(workflow_id)
    
    def get_statistics(self) -> dict:
        """Get system statistics"""
        return self.orchestrator.get_statistics()


# Example usage
if __name__ == "__main__":
    import time
    
    # Initialize system
    system = VehicleMaintenanceAgentSystem()
    system.start()
    
    # Example 1: Critical vehicle issue
    print("\n=== Example 1: Critical Vehicle Issue ===")
    critical_telemetry = {
        'vehicle_id': 'VEH001',
        'timestamp': datetime.now().isoformat(),
        'engine_temp': 110,
        'brake_wear': 0.85,
        'battery_voltage': 11.2,
        'check_engine_light': True,
        'brake_failure': True,
        'mileage': 75000
    }
    
    workflow_id_1 = system.process_vehicle('VEH001', critical_telemetry)
    print(f"Created critical workflow: {workflow_id_1}")
    
    # Example 2: Routine maintenance
    print("\n=== Example 2: Routine Maintenance ===")
    routine_telemetry = {
        'vehicle_id': 'VEH002',
        'timestamp': datetime.now().isoformat(),
        'engine_temp': 92,
        'brake_wear': 0.45,
        'battery_voltage': 12.4,
        'check_engine_light': False,
        'maintenance_due': True,
        'mileage': 30000
    }
    
    workflow_id_2 = system.process_vehicle('VEH002', routine_telemetry)
    print(f"Created routine workflow: {workflow_id_2}")
    
    # Wait for processing
    print("\nProcessing workflows...")
    time.sleep(3)
    
    # Check status
    print(f"\nWorkflow 1 status: {json.dumps(system.get_workflow_status(workflow_id_1), indent=2)}")
    print(f"\nWorkflow 2 status: {json.dumps(system.get_workflow_status(workflow_id_2), indent=2)}")
    
    # Get statistics
    print(f"\nSystem statistics: {json.dumps(system.get_statistics(), indent=2)}")
