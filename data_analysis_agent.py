"""
Data Analysis Agent for Real-Time Vehicle Telematics Processing
Handles streaming data, anomaly detection, and enriched analysis reporting
"""

import numpy as np
import pandas as pd
import pickle
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import deque
import threading
import queue
import time
from enum import Enum

try:
    from tensorflow import keras
    import tensorflow as tf
except ImportError:
    keras = None
    tf = None
    print("TensorFlow not available - using fallback mode")


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_analysis_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DataAnalysisAgent')


class RiskLevel(Enum):
    """Risk level classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TelematicsReading:
    """Single telematics reading"""
    vehicle_id: str
    timestamp: datetime
    engine_temp: Optional[float] = None
    oil_pressure: Optional[float] = None
    battery_voltage: Optional[float] = None
    fuel_efficiency: Optional[float] = None
    coolant_temp: Optional[float] = None
    rpm: Optional[float] = None
    speed: Optional[float] = None
    brake_pressure: Optional[float] = None
    tire_pressure_fl: Optional[float] = None
    tire_pressure_fr: Optional[float] = None
    tire_pressure_rl: Optional[float] = None
    tire_pressure_rr: Optional[float] = None
    transmission_temp: Optional[float] = None
    throttle_position: Optional[float] = None
    mileage: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def get_sensor_values(self) -> List[float]:
        """Extract sensor values as list, handling missing data"""
        sensors = [
            self.engine_temp,
            self.oil_pressure,
            self.battery_voltage,
            self.fuel_efficiency,
            self.coolant_temp,
            self.rpm,
            self.speed,
            self.brake_pressure,
            self.tire_pressure_fl,
            self.tire_pressure_fr,
            self.tire_pressure_rl,
            self.tire_pressure_rr,
            self.transmission_temp,
            self.throttle_position,
            self.mileage
        ]
        return sensors
    
    def get_valid_sensor_count(self) -> int:
        """Count non-None sensors"""
        return sum(1 for s in self.get_sensor_values() if s is not None)


@dataclass
class VehicleBaseline:
    """Historical baseline for a vehicle"""
    vehicle_id: str
    mean_values: Dict[str, float]
    std_values: Dict[str, float]
    min_values: Dict[str, float]
    max_values: Dict[str, float]
    sample_count: int
    last_updated: datetime


@dataclass
class AnalysisReport:
    """Structured analysis report output"""
    vehicle_id: str
    timestamp: datetime
    anomaly_score: float
    risk_level: RiskLevel
    trending_parameters: List[Dict[str, Any]]
    historical_context: Dict[str, Any]
    detected_anomalies: List[str]
    sensor_health: Dict[str, str]
    recommendations: List[str]
    confidence_score: float
    data_quality_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['risk_level'] = self.risk_level.value
        return data


class MaintenanceRecordServer:
    """
    Mock maintenance record server
    In production, this would connect to actual database/API
    """
    
    def __init__(self):
        self.records = {}
        logger.info("Maintenance Record Server initialized")
    
    def get_maintenance_history(self, vehicle_id: str) -> List[Dict[str, Any]]:
        """Get maintenance history for a vehicle"""
        # Mock data - replace with actual database query
        if vehicle_id not in self.records:
            self.records[vehicle_id] = self._generate_mock_history(vehicle_id)
        
        return self.records[vehicle_id]
    
    def _generate_mock_history(self, vehicle_id: str) -> List[Dict[str, Any]]:
        """Generate mock maintenance history"""
        history = []
        base_date = datetime.now() - timedelta(days=365)
        
        for i in range(4):  # 4 maintenance events in past year
            history.append({
                'date': (base_date + timedelta(days=i*90)).isoformat(),
                'service_type': ['oil_change', 'brake_inspection', 'tire_rotation', 'battery_test'][i],
                'mileage': 30000 + i * 5000,
                'issues_found': ['none', 'minor_wear', 'none', 'low_voltage'][i],
                'parts_replaced': [[], ['brake_pads'], [], []][i]
            })
        
        return history
    
    def add_maintenance_record(self, vehicle_id: str, record: Dict[str, Any]):
        """Add new maintenance record"""
        if vehicle_id not in self.records:
            self.records[vehicle_id] = []
        self.records[vehicle_id].append(record)


class DataAnalysisAgent:
    """
    Data Analysis Agent for Real-Time Vehicle Telematics
    
    Responsibilities:
    - Subscribe to real-time telematics streams
    - Compare against historical baselines
    - Detect anomalies using ML model
    - Enrich with maintenance history
    - Generate structured analysis reports
    """
    
    def __init__(
        self,
        model_path: str = 'deep_vae_full_model',
        scaler_path: str = 'scaler.pkl',
        baseline_window: int = 100,
        anomaly_threshold: float = 0.05
    ):
        """
        Initialize Data Analysis Agent
        
        Args:
            model_path: Path to anomaly detection model
            scaler_path: Path to feature scaler
            baseline_window: Number of readings for baseline calculation
            anomaly_threshold: Threshold for anomaly detection
        """
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.baseline_window = baseline_window
        self.anomaly_threshold = anomaly_threshold
        
        # Load models
        self.model = None
        self.scaler = None
        self._load_models()
        
        # Vehicle baselines (historical data)
        self.baselines: Dict[str, VehicleBaseline] = {}
        
        # Historical readings buffer for each vehicle
        self.reading_buffers: Dict[str, deque] = {}
        
        # Maintenance record server
        self.maintenance_server = MaintenanceRecordServer()
        
        # Streaming queue
        self.stream_queue = queue.Queue(maxsize=1000)
        
        # Processing thread
        self.processing_thread = None
        self.running = False
        
        # Statistics
        self.stats = {
            'total_readings': 0,
            'anomalies_detected': 0,
            'corrupted_readings': 0,
            'vehicles_monitored': 0
        }
        
        # Sensor normal ranges (for validation)
        self.sensor_ranges = {
            'engine_temp': (60, 120),
            'oil_pressure': (20, 80),
            'battery_voltage': (11.5, 14.5),
            'fuel_efficiency': (5, 50),
            'coolant_temp': (60, 110),
            'rpm': (0, 8000),
            'speed': (0, 200),
            'brake_pressure': (0, 150),
            'tire_pressure_fl': (28, 40),
            'tire_pressure_fr': (28, 40),
            'tire_pressure_rl': (28, 40),
            'tire_pressure_rr': (28, 40),
            'transmission_temp': (60, 100),
            'throttle_position': (0, 100),
            'mileage': (0, 500000)
        }
        
        logger.info("Data Analysis Agent initialized")
    
    def _load_models(self):
        """Load anomaly detection model and scaler"""
        try:
            if keras:
                self.model = keras.models.load_model(self.model_path)
                logger.info(f"Loaded anomaly detection model from {self.model_path}")
            else:
                logger.warning("TensorFlow not available - using fallback detection")
        except Exception as e:
            logger.error(f"Could not load model: {e}")
            self.model = None
        
        try:
            with open(self.scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            logger.info(f"Loaded scaler from {self.scaler_path}")
        except Exception as e:
            logger.error(f"Could not load scaler: {e}")
            self.scaler = None
    
    def subscribe_to_stream(self, reading: TelematicsReading):
        """
        Subscribe to real-time telematics stream
        
        Args:
            reading: Telematics reading from vehicle
        """
        try:
            self.stream_queue.put(reading, timeout=1)
        except queue.Full:
            logger.warning(f"Stream queue full, dropping reading for {reading.vehicle_id}")
            self.stats['corrupted_readings'] += 1
    
    def start_processing(self):
        """Start processing telematics stream"""
        if self.running:
            logger.warning("Agent already running")
            return
        
        self.running = True
        self.processing_thread = threading.Thread(target=self._process_stream)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        logger.info("Started processing telematics stream")
    
    def stop_processing(self):
        """Stop processing stream"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
        logger.info("Stopped processing telematics stream")
    
    def _process_stream(self):
        """Process telematics stream in real-time"""
        while self.running:
            try:
                # Get reading from queue with timeout
                reading = self.stream_queue.get(timeout=0.1)
                
                # Process reading
                report = self.analyze_reading(reading)
                
                # Log report
                logger.info(f"Analysis complete for {reading.vehicle_id}: "
                          f"Risk={report.risk_level.value}, "
                          f"Anomaly={report.anomaly_score:.3f}")
                
                # Update statistics
                self.stats['total_readings'] += 1
                if report.anomaly_score > self.anomaly_threshold:
                    self.stats['anomalies_detected'] += 1
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing reading: {e}")
    
    def analyze_reading(self, reading: TelematicsReading) -> AnalysisReport:
        """
        Analyze a single telematics reading
        
        Args:
            reading: Telematics reading
            
        Returns:
            AnalysisReport: Structured analysis report
        """
        vehicle_id = reading.vehicle_id
        
        # Step 1: Validate and clean data
        cleaned_reading, data_quality = self._validate_and_clean(reading)
        
        # Step 2: Update historical baseline
        self._update_baseline(cleaned_reading)
        
        # Step 3: Compare against baseline
        baseline_comparison = self._compare_to_baseline(cleaned_reading)
        
        # Step 4: Detect anomalies using ML model
        anomaly_score, anomaly_details = self._detect_anomalies(cleaned_reading)
        
        # Step 5: Identify trending parameters
        trending_params = self._identify_trends(vehicle_id, cleaned_reading)
        
        # Step 6: Enrich with maintenance history
        maintenance_history = self.maintenance_server.get_maintenance_history(vehicle_id)
        historical_context = self._build_historical_context(
            vehicle_id, 
            maintenance_history,
            baseline_comparison
        )
        
        # Step 7: Assess risk level
        risk_level = self._assess_risk_level(
            anomaly_score,
            baseline_comparison,
            trending_params,
            maintenance_history
        )
        
        # Step 8: Generate recommendations
        recommendations = self._generate_recommendations(
            risk_level,
            anomaly_details,
            trending_params,
            maintenance_history
        )
        
        # Step 9: Assess sensor health
        sensor_health = self._assess_sensor_health(reading, cleaned_reading)
        
        # Step 10: Calculate confidence
        confidence = self._calculate_confidence(data_quality, anomaly_score)
        
        # Create report
        report = AnalysisReport(
            vehicle_id=vehicle_id,
            timestamp=reading.timestamp,
            anomaly_score=anomaly_score,
            risk_level=risk_level,
            trending_parameters=trending_params,
            historical_context=historical_context,
            detected_anomalies=anomaly_details,
            sensor_health=sensor_health,
            recommendations=recommendations,
            confidence_score=confidence,
            data_quality_score=data_quality
        )
        
        return report
    
    def _validate_and_clean(self, reading: TelematicsReading) -> Tuple[TelematicsReading, float]:
        """
        Validate and clean sensor data, handle missing/corrupted values
        
        Returns:
            Tuple of (cleaned_reading, data_quality_score)
        """
        cleaned = TelematicsReading(
            vehicle_id=reading.vehicle_id,
            timestamp=reading.timestamp
        )
        
        valid_sensors = 0
        total_sensors = 0
        
        # Validate each sensor
        for sensor_name, (min_val, max_val) in self.sensor_ranges.items():
            total_sensors += 1
            value = getattr(reading, sensor_name, None)
            
            if value is None:
                # Missing data - use baseline if available
                if reading.vehicle_id in self.baselines:
                    baseline = self.baselines[reading.vehicle_id]
                    if sensor_name in baseline.mean_values:
                        setattr(cleaned, sensor_name, baseline.mean_values[sensor_name])
                        valid_sensors += 0.5  # Partial credit for imputed value
                continue
            
            # Check if value is in valid range
            if min_val <= value <= max_val:
                setattr(cleaned, sensor_name, value)
                valid_sensors += 1
            else:
                # Corrupted data - log and use baseline
                logger.warning(f"Corrupted {sensor_name} for {reading.vehicle_id}: "
                             f"{value} (valid range: {min_val}-{max_val})")
                self.stats['corrupted_readings'] += 1
                
                # Use baseline if available
                if reading.vehicle_id in self.baselines:
                    baseline = self.baselines[reading.vehicle_id]
                    if sensor_name in baseline.mean_values:
                        setattr(cleaned, sensor_name, baseline.mean_values[sensor_name])
                        valid_sensors += 0.3  # Lower credit for corrupted data
        
        data_quality = valid_sensors / total_sensors if total_sensors > 0 else 0.0
        
        return cleaned, data_quality
    
    def _update_baseline(self, reading: TelematicsReading):
        """Update historical baseline for vehicle"""
        vehicle_id = reading.vehicle_id
        
        # Initialize buffer if needed
        if vehicle_id not in self.reading_buffers:
            self.reading_buffers[vehicle_id] = deque(maxlen=self.baseline_window)
            self.stats['vehicles_monitored'] += 1
        
        # Add reading to buffer
        self.reading_buffers[vehicle_id].append(reading)
        
        # Calculate baseline if we have enough data
        if len(self.reading_buffers[vehicle_id]) >= 10:
            self._calculate_baseline(vehicle_id)
    
    def _calculate_baseline(self, vehicle_id: str):
        """Calculate baseline statistics from historical readings"""
        readings = list(self.reading_buffers[vehicle_id])
        
        # Extract sensor data
        sensor_data = {}
        for sensor_name in self.sensor_ranges.keys():
            values = [getattr(r, sensor_name) for r in readings 
                     if getattr(r, sensor_name) is not None]
            if values:
                sensor_data[sensor_name] = values
        
        # Calculate statistics
        mean_values = {k: np.mean(v) for k, v in sensor_data.items()}
        std_values = {k: np.std(v) for k, v in sensor_data.items()}
        min_values = {k: np.min(v) for k, v in sensor_data.items()}
        max_values = {k: np.max(v) for k, v in sensor_data.items()}
        
        # Update baseline
        self.baselines[vehicle_id] = VehicleBaseline(
            vehicle_id=vehicle_id,
            mean_values=mean_values,
            std_values=std_values,
            min_values=min_values,
            max_values=max_values,
            sample_count=len(readings),
            last_updated=datetime.now()
        )
    
    def _compare_to_baseline(self, reading: TelematicsReading) -> Dict[str, Any]:
        """Compare current reading to historical baseline"""
        vehicle_id = reading.vehicle_id
        
        if vehicle_id not in self.baselines:
            return {'status': 'no_baseline', 'deviations': []}
        
        baseline = self.baselines[vehicle_id]
        deviations = []
        
        for sensor_name in self.sensor_ranges.keys():
            current_value = getattr(reading, sensor_name)
            
            if current_value is None or sensor_name not in baseline.mean_values:
                continue
            
            mean = baseline.mean_values[sensor_name]
            std = baseline.std_values.get(sensor_name, 1.0)
            
            # Calculate z-score
            z_score = abs((current_value - mean) / std) if std > 0 else 0
            
            if z_score > 2.0:  # More than 2 standard deviations
                deviations.append({
                    'sensor': sensor_name,
                    'current_value': current_value,
                    'baseline_mean': mean,
                    'baseline_std': std,
                    'z_score': z_score,
                    'deviation_percent': ((current_value - mean) / mean * 100) if mean != 0 else 0
                })
        
        return {
            'status': 'compared',
            'deviations': deviations,
            'baseline_age_hours': (datetime.now() - baseline.last_updated).total_seconds() / 3600
        }
    
    def _detect_anomalies(self, reading: TelematicsReading) -> Tuple[float, List[str]]:
        """
        Detect anomalies using ML model
        
        Returns:
            Tuple of (anomaly_score, list_of_anomaly_descriptions)
        """
        anomaly_details = []
        
        # Prepare features
        features = self._prepare_features(reading)
        
        if self.model and self.scaler and features is not None:
            try:
                # Scale features
                scaled_features = self.scaler.transform([features])
                
                # Get reconstruction from VAE
                reconstruction = self.model.predict(scaled_features, verbose=0)
                
                # Calculate reconstruction error (MSE)
                mse = np.mean(np.square(scaled_features - reconstruction))
                anomaly_score = float(mse)
                
                # Identify which sensors contribute most to anomaly
                sensor_errors = np.square(scaled_features - reconstruction)[0]
                sensor_names = list(self.sensor_ranges.keys())[:len(sensor_errors)]
                
                # Find top anomalous sensors
                top_indices = np.argsort(sensor_errors)[-3:]  # Top 3
                for idx in top_indices:
                    if idx < len(sensor_names) and sensor_errors[idx] > 0.1:
                        anomaly_details.append(
                            f"Anomalous {sensor_names[idx]}: error={sensor_errors[idx]:.3f}"
                        )
                
            except Exception as e:
                logger.error(f"Error in ML anomaly detection: {e}")
                anomaly_score = self._fallback_anomaly_detection(reading)
        else:
            # Fallback: rule-based anomaly detection
            anomaly_score = self._fallback_anomaly_detection(reading)
            anomaly_details = self._fallback_anomaly_details(reading)
        
        return anomaly_score, anomaly_details
    
    def _prepare_features(self, reading: TelematicsReading) -> Optional[np.ndarray]:
        """Prepare features for ML model"""
        features = []
        
        for sensor_name in self.sensor_ranges.keys():
            value = getattr(reading, sensor_name, None)
            if value is None:
                # Use mean from baseline or default
                if reading.vehicle_id in self.baselines:
                    baseline = self.baselines[reading.vehicle_id]
                    value = baseline.mean_values.get(sensor_name, 0)
                else:
                    value = 0
            features.append(value)
        
        return np.array(features) if features else None
    
    def _fallback_anomaly_detection(self, reading: TelematicsReading) -> float:
        """Rule-based anomaly detection fallback"""
        score = 0.0
        checks = 0
        
        # Check critical thresholds
        if reading.engine_temp and reading.engine_temp > 105:
            score += 0.3
            checks += 1
        
        if reading.battery_voltage and reading.battery_voltage < 11.8:
            score += 0.2
            checks += 1
        
        if reading.oil_pressure and reading.oil_pressure < 25:
            score += 0.3
            checks += 1
        
        if reading.coolant_temp and reading.coolant_temp > 105:
            score += 0.2
            checks += 1
        
        return min(score, 1.0)
    
    def _fallback_anomaly_details(self, reading: TelematicsReading) -> List[str]:
        """Generate anomaly details for fallback mode"""
        details = []
        
        if reading.engine_temp and reading.engine_temp > 105:
            details.append(f"High engine temperature: {reading.engine_temp}°C")
        
        if reading.battery_voltage and reading.battery_voltage < 11.8:
            details.append(f"Low battery voltage: {reading.battery_voltage}V")
        
        if reading.oil_pressure and reading.oil_pressure < 25:
            details.append(f"Low oil pressure: {reading.oil_pressure} PSI")
        
        return details

    def _identify_trends(self, vehicle_id: str, reading: TelematicsReading) -> List[Dict[str, Any]]:
        """Identify trending parameters from historical data"""
        if vehicle_id not in self.reading_buffers or len(self.reading_buffers[vehicle_id]) < 5:
            return []
        
        trends = []
        readings = list(self.reading_buffers[vehicle_id])
        
        # Analyze trends for key sensors
        key_sensors = ['engine_temp', 'battery_voltage', 'oil_pressure', 'fuel_efficiency']
        
        for sensor_name in key_sensors:
            values = [getattr(r, sensor_name) for r in readings 
                     if getattr(r, sensor_name) is not None]
            
            if len(values) < 5:
                continue
            
            # Calculate trend (simple linear regression slope)
            x = np.arange(len(values))
            y = np.array(values)
            
            if len(x) > 1:
                slope = np.polyfit(x, y, 1)[0]
                
                # Determine trend direction and significance
                mean_value = np.mean(y)
                relative_slope = (slope / mean_value * 100) if mean_value != 0 else 0
                
                if abs(relative_slope) > 1:  # More than 1% change per reading
                    trend_direction = 'increasing' if slope > 0 else 'decreasing'
                    
                    trends.append({
                        'parameter': sensor_name,
                        'direction': trend_direction,
                        'slope': float(slope),
                        'relative_change_percent': float(relative_slope),
                        'current_value': float(values[-1]),
                        'mean_value': float(mean_value),
                        'concern_level': self._assess_trend_concern(
                            sensor_name, trend_direction, relative_slope
                        )
                    })
        
        return trends
    
    def _assess_trend_concern(self, sensor: str, direction: str, change_percent: float) -> str:
        """Assess concern level for a trend"""
        # Define concerning trends
        concerning_trends = {
            'engine_temp': ('increasing', 2),
            'battery_voltage': ('decreasing', 2),
            'oil_pressure': ('decreasing', 2),
            'fuel_efficiency': ('decreasing', 5)
        }
        
        if sensor in concerning_trends:
            concern_direction, threshold = concerning_trends[sensor]
            if direction == concern_direction and abs(change_percent) > threshold:
                return 'high' if abs(change_percent) > threshold * 2 else 'medium'
        
        return 'low'
    
    def _build_historical_context(
        self,
        vehicle_id: str,
        maintenance_history: List[Dict[str, Any]],
        baseline_comparison: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build historical context from maintenance records and baselines"""
        context = {
            'vehicle_id': vehicle_id,
            'maintenance_records_count': len(maintenance_history),
            'last_maintenance': None,
            'recurring_issues': [],
            'baseline_status': baseline_comparison.get('status', 'unknown')
        }
        
        if maintenance_history:
            # Get most recent maintenance
            sorted_history = sorted(
                maintenance_history,
                key=lambda x: x.get('date', ''),
                reverse=True
            )
            context['last_maintenance'] = sorted_history[0]
            
            # Identify recurring issues
            issue_counts = {}
            for record in maintenance_history:
                issues = record.get('issues_found', [])
                if isinstance(issues, str):
                    issues = [issues]
                for issue in issues:
                    if issue and issue != 'none':
                        issue_counts[issue] = issue_counts.get(issue, 0) + 1
            
            context['recurring_issues'] = [
                {'issue': issue, 'occurrences': count}
                for issue, count in issue_counts.items()
                if count > 1
            ]
        
        # Add baseline deviation summary
        if baseline_comparison.get('deviations'):
            context['significant_deviations'] = len(baseline_comparison['deviations'])
            context['most_deviated_sensor'] = max(
                baseline_comparison['deviations'],
                key=lambda x: x['z_score']
            )['sensor'] if baseline_comparison['deviations'] else None
        
        return context
    
    def _assess_risk_level(
        self,
        anomaly_score: float,
        baseline_comparison: Dict[str, Any],
        trending_params: List[Dict[str, Any]],
        maintenance_history: List[Dict[str, Any]]
    ) -> RiskLevel:
        """
        Assess overall risk level based on multiple factors
        
        Risk assessment matrix:
        - CRITICAL: Immediate safety concern
        - HIGH: Likely failure within days
        - MEDIUM: Attention needed within weeks
        - LOW: Normal operation
        """
        risk_score = 0.0
        
        # Factor 1: Anomaly score (0-40 points)
        if anomaly_score > 0.1:
            risk_score += min(anomaly_score * 100, 40)
        
        # Factor 2: Baseline deviations (0-30 points)
        deviations = baseline_comparison.get('deviations', [])
        if deviations:
            max_z_score = max(d['z_score'] for d in deviations)
            risk_score += min(max_z_score * 5, 30)
        
        # Factor 3: Concerning trends (0-20 points)
        high_concern_trends = [t for t in trending_params if t.get('concern_level') == 'high']
        risk_score += len(high_concern_trends) * 10
        
        # Factor 4: Maintenance history (0-10 points)
        if maintenance_history:
            last_maintenance = max(maintenance_history, key=lambda x: x.get('date', ''))
            last_date = datetime.fromisoformat(last_maintenance['date'])
            days_since = (datetime.now() - last_date).days
            
            if days_since > 180:  # More than 6 months
                risk_score += 10
            elif days_since > 90:  # More than 3 months
                risk_score += 5
        
        # Classify risk level
        if risk_score >= 70:
            return RiskLevel.CRITICAL
        elif risk_score >= 50:
            return RiskLevel.HIGH
        elif risk_score >= 30:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _generate_recommendations(
        self,
        risk_level: RiskLevel,
        anomaly_details: List[str],
        trending_params: List[Dict[str, Any]],
        maintenance_history: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Risk-based recommendations
        if risk_level == RiskLevel.CRITICAL:
            recommendations.append("URGENT: Schedule immediate inspection")
            recommendations.append("Advise customer to avoid driving until inspection")
        elif risk_level == RiskLevel.HIGH:
            recommendations.append("Schedule inspection within 48 hours")
            recommendations.append("Monitor vehicle closely")
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.append("Schedule maintenance within 2 weeks")
        
        # Anomaly-specific recommendations
        for anomaly in anomaly_details:
            if 'engine_temp' in anomaly.lower():
                recommendations.append("Check cooling system and thermostat")
            elif 'battery' in anomaly.lower():
                recommendations.append("Test battery and charging system")
            elif 'oil_pressure' in anomaly.lower():
                recommendations.append("Check oil level and pressure sensor")
        
        # Trend-based recommendations
        for trend in trending_params:
            if trend.get('concern_level') in ['high', 'medium']:
                param = trend['parameter']
                direction = trend['direction']
                
                if param == 'fuel_efficiency' and direction == 'decreasing':
                    recommendations.append("Investigate fuel system efficiency")
                elif param == 'battery_voltage' and direction == 'decreasing':
                    recommendations.append("Battery replacement may be needed soon")
        
        # Maintenance history recommendations
        if maintenance_history:
            last_maintenance = max(maintenance_history, key=lambda x: x.get('date', ''))
            days_since = (datetime.now() - datetime.fromisoformat(last_maintenance['date'])).days
            
            if days_since > 180:
                recommendations.append("Overdue for routine maintenance")
        
        return recommendations if recommendations else ["Continue normal monitoring"]
    
    def _assess_sensor_health(
        self,
        original_reading: TelematicsReading,
        cleaned_reading: TelematicsReading
    ) -> Dict[str, str]:
        """Assess health of each sensor"""
        sensor_health = {}
        
        for sensor_name in self.sensor_ranges.keys():
            original_value = getattr(original_reading, sensor_name)
            cleaned_value = getattr(cleaned_reading, sensor_name)
            
            if original_value is None:
                sensor_health[sensor_name] = 'missing'
            elif original_value != cleaned_value:
                sensor_health[sensor_name] = 'corrupted'
            else:
                sensor_health[sensor_name] = 'healthy'
        
        return sensor_health
    
    def _calculate_confidence(self, data_quality: float, anomaly_score: float) -> float:
        """Calculate confidence in the analysis"""
        # Base confidence on data quality
        confidence = data_quality * 0.7
        
        # Adjust based on anomaly score clarity
        if anomaly_score < 0.01 or anomaly_score > 0.1:
            # Clear signal (very normal or very anomalous)
            confidence += 0.3
        else:
            # Ambiguous signal
            confidence += 0.15
        
        return min(confidence, 1.0)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            **self.stats,
            'queue_size': self.stream_queue.qsize(),
            'vehicles_with_baselines': len(self.baselines),
            'is_running': self.running
        }
    
    def export_baseline(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        """Export baseline for a vehicle"""
        if vehicle_id not in self.baselines:
            return None
        
        baseline = self.baselines[vehicle_id]
        return {
            'vehicle_id': baseline.vehicle_id,
            'mean_values': baseline.mean_values,
            'std_values': baseline.std_values,
            'min_values': baseline.min_values,
            'max_values': baseline.max_values,
            'sample_count': baseline.sample_count,
            'last_updated': baseline.last_updated.isoformat()
        }
    
    def import_baseline(self, baseline_data: Dict[str, Any]):
        """Import baseline for a vehicle"""
        vehicle_id = baseline_data['vehicle_id']
        
        self.baselines[vehicle_id] = VehicleBaseline(
            vehicle_id=vehicle_id,
            mean_values=baseline_data['mean_values'],
            std_values=baseline_data['std_values'],
            min_values=baseline_data['min_values'],
            max_values=baseline_data['max_values'],
            sample_count=baseline_data['sample_count'],
            last_updated=datetime.fromisoformat(baseline_data['last_updated'])
        )
        
        logger.info(f"Imported baseline for vehicle {vehicle_id}")


# Integration with Master Orchestrator
def create_data_analysis_handler(agent: DataAnalysisAgent):
    """
    Create handler function for Master Orchestrator integration
    
    Args:
        agent: DataAnalysisAgent instance
        
    Returns:
        Handler function compatible with orchestrator
    """
    def handler(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handler for Master Orchestrator
        
        Args:
            payload: Contains vehicle_id and telemetry_data
            
        Returns:
            Analysis results dictionary
        """
        vehicle_id = payload['vehicle_id']
        telemetry_data = payload['telemetry_data']
        
        # Convert telemetry dict to TelematicsReading
        reading = TelematicsReading(
            vehicle_id=vehicle_id,
            timestamp=datetime.fromisoformat(telemetry_data.get('timestamp', datetime.now().isoformat())),
            engine_temp=telemetry_data.get('engine_temp'),
            oil_pressure=telemetry_data.get('oil_pressure'),
            battery_voltage=telemetry_data.get('battery_voltage'),
            fuel_efficiency=telemetry_data.get('fuel_efficiency'),
            coolant_temp=telemetry_data.get('coolant_temp'),
            rpm=telemetry_data.get('rpm'),
            speed=telemetry_data.get('speed'),
            brake_pressure=telemetry_data.get('brake_pressure'),
            tire_pressure_fl=telemetry_data.get('tire_pressure_fl'),
            tire_pressure_fr=telemetry_data.get('tire_pressure_fr'),
            tire_pressure_rl=telemetry_data.get('tire_pressure_rl'),
            tire_pressure_rr=telemetry_data.get('tire_pressure_rr'),
            transmission_temp=telemetry_data.get('transmission_temp'),
            throttle_position=telemetry_data.get('throttle_position'),
            mileage=telemetry_data.get('mileage')
        )
        
        # Analyze reading
        report = agent.analyze_reading(reading)
        
        # Convert report to dict for orchestrator
        return report.to_dict()
    
    return handler


# Example usage and testing
if __name__ == "__main__":
    import time
    
    # Initialize agent
    agent = DataAnalysisAgent(
        model_path='deep_vae_full_model',
        scaler_path='scaler.pkl',
        baseline_window=100,
        anomaly_threshold=0.05
    )
    
    # Start processing
    agent.start_processing()
    
    print("Data Analysis Agent started\n")
    
    # Example 1: Normal reading
    print("=== Example 1: Normal Vehicle Reading ===")
    normal_reading = TelematicsReading(
        vehicle_id='VEH001',
        timestamp=datetime.now(),
        engine_temp=92.0,
        oil_pressure=45.0,
        battery_voltage=12.6,
        fuel_efficiency=28.5,
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
    
    agent.subscribe_to_stream(normal_reading)
    time.sleep(0.5)
    
    # Example 2: Anomalous reading
    print("\n=== Example 2: Anomalous Vehicle Reading ===")
    anomalous_reading = TelematicsReading(
        vehicle_id='VEH002',
        timestamp=datetime.now(),
        engine_temp=115.0,  # High!
        oil_pressure=22.0,  # Low!
        battery_voltage=11.5,  # Low!
        fuel_efficiency=15.0,  # Poor
        coolant_temp=108.0,  # High!
        rpm=3500.0,
        speed=45.0,
        brake_pressure=35.0,
        tire_pressure_fl=28.0,  # Low
        tire_pressure_fr=32.0,
        tire_pressure_rl=31.0,
        tire_pressure_rr=32.0,
        transmission_temp=95.0,
        throttle_position=60.0,
        mileage=85000.0
    )
    
    agent.subscribe_to_stream(anomalous_reading)
    time.sleep(0.5)
    
    # Example 3: Reading with missing data
    print("\n=== Example 3: Reading with Missing Sensors ===")
    incomplete_reading = TelematicsReading(
        vehicle_id='VEH003',
        timestamp=datetime.now(),
        engine_temp=95.0,
        oil_pressure=None,  # Missing
        battery_voltage=12.4,
        fuel_efficiency=None,  # Missing
        coolant_temp=90.0,
        rpm=2200.0,
        speed=None,  # Missing
        brake_pressure=32.0,
        tire_pressure_fl=32.0,
        tire_pressure_fr=32.0,
        tire_pressure_rl=None,  # Missing
        tire_pressure_rr=32.0,
        transmission_temp=87.0,
        throttle_position=45.0,
        mileage=52000.0
    )
    
    agent.subscribe_to_stream(incomplete_reading)
    time.sleep(0.5)
    
    # Example 4: Reading with corrupted data
    print("\n=== Example 4: Reading with Corrupted Data ===")
    corrupted_reading = TelematicsReading(
        vehicle_id='VEH004',
        timestamp=datetime.now(),
        engine_temp=250.0,  # Impossible value!
        oil_pressure=45.0,
        battery_voltage=-5.0,  # Impossible value!
        fuel_efficiency=28.0,
        coolant_temp=90.0,
        rpm=15000.0,  # Impossible value!
        speed=60.0,
        brake_pressure=30.0,
        tire_pressure_fl=32.0,
        tire_pressure_fr=32.0,
        tire_pressure_rl=32.0,
        tire_pressure_rr=32.0,
        transmission_temp=85.0,
        throttle_position=40.0,
        mileage=48000.0
    )
    
    agent.subscribe_to_stream(corrupted_reading)
    time.sleep(0.5)
    
    # Wait for processing
    time.sleep(2)
    
    # Get statistics
    print("\n=== Agent Statistics ===")
    stats = agent.get_statistics()
    print(json.dumps(stats, indent=2))
    
    # Test direct analysis (synchronous)
    print("\n=== Direct Analysis Test ===")
    test_reading = TelematicsReading(
        vehicle_id='VEH005',
        timestamp=datetime.now(),
        engine_temp=98.0,
        oil_pressure=42.0,
        battery_voltage=12.3,
        fuel_efficiency=26.0,
        coolant_temp=92.0,
        rpm=2500.0,
        speed=70.0,
        brake_pressure=28.0,
        tire_pressure_fl=32.0,
        tire_pressure_fr=32.0,
        tire_pressure_rl=32.0,
        tire_pressure_rr=32.0,
        transmission_temp=88.0,
        throttle_position=50.0,
        mileage=60000.0
    )
    
    report = agent.analyze_reading(test_reading)
    print(f"\nAnalysis Report for {report.vehicle_id}:")
    print(f"Risk Level: {report.risk_level.value}")
    print(f"Anomaly Score: {report.anomaly_score:.4f}")
    print(f"Confidence: {report.confidence_score:.2f}")
    print(f"Data Quality: {report.data_quality_score:.2f}")
    print(f"Detected Anomalies: {report.detected_anomalies}")
    print(f"Recommendations: {report.recommendations}")
    
    # Stop agent
    agent.stop_processing()
    print("\nData Analysis Agent stopped")
