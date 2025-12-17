# Data Analysis Agent - Real-Time Vehicle Telematics Processing

## Overview

The Data Analysis Agent is a sophisticated real-time processing system that subscribes to vehicle telematics streams, detects anomalies using ML models, compares readings against historical baselines, and generates enriched analysis reports for the Master Orchestrator.

## Key Features

### 1. Real-Time Stream Processing
- Subscribes to continuous telematics streams from multiple vehicles
- Near-real-time processing with queue-based architecture
- Thread-safe concurrent processing
- Configurable processing capacity

### 2. Comprehensive Sensor Monitoring
Monitors 15+ sensor parameters:
- **Engine**: Temperature, RPM, throttle position
- **Fluids**: Oil pressure, coolant temperature, fuel efficiency
- **Electrical**: Battery voltage
- **Brakes**: Brake pressure
- **Tires**: Individual tire pressures (FL, FR, RL, RR)
- **Transmission**: Temperature
- **Vehicle**: Speed, mileage

### 3. Intelligent Data Validation
- Validates sensor readings against normal ranges
- Detects corrupted/impossible values
- Handles missing sensor data gracefully
- Imputes missing values using historical baselines
- Calculates data quality scores

### 4. Historical Baseline Management
- Maintains rolling baseline for each vehicle
- Calculates mean, std, min, max for all sensors
- Configurable baseline window (default: 100 readings)
- Automatic baseline updates
- Baseline import/export for persistence

### 5. Multi-Method Anomaly Detection

#### ML-Based Detection (Primary)
- Uses pre-trained VAE (Variational Autoencoder) model
- Calculates reconstruction error for anomaly scoring
- Identifies specific anomalous sensors
- Confidence-based scoring

#### Rule-Based Detection (Fallback)
- Critical threshold checks
- Works when ML model unavailable
- Ensures system reliability

### 6. Trend Analysis
- Identifies trending parameters over time
- Linear regression for trend detection
- Calculates relative change percentages
- Assesses trend concern levels (low/medium/high)
- Tracks concerning trends (e.g., decreasing battery voltage)

### 7. Maintenance History Enrichment
- Integrates with maintenance record server
- Retrieves historical service records
- Identifies recurring issues
- Calculates time since last maintenance
- Provides historical context for analysis

### 8. Risk Assessment
Multi-factor risk scoring based on:
- Anomaly score (0-40 points)
- Baseline deviations (0-30 points)
- Concerning trends (0-20 points)
- Maintenance history (0-10 points)

**Risk Levels:**
- **CRITICAL** (70+ points): Immediate safety concern
- **HIGH** (50-69 points): Likely failure within days
- **MEDIUM** (30-49 points): Attention needed within weeks
- **LOW** (0-29 points): Normal operation

### 9. Actionable Recommendations
Generates specific recommendations based on:
- Risk level
- Detected anomalies
- Trending parameters
- Maintenance history

### 10. Sensor Health Monitoring
Tracks health status of each sensor:
- **Healthy**: Normal operation
- **Missing**: No data received
- **Corrupted**: Invalid/out-of-range values

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Telematics Stream Input                     │
│              (Real-time vehicle sensor data)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Stream Queue (1000 max)                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Processing Thread (Real-time)                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Validate & Clean Data                             │  │
│  │ 2. Update Historical Baseline                        │  │
│  │ 3. Compare to Baseline                               │  │
│  │ 4. Detect Anomalies (ML + Rules)                     │  │
│  │ 5. Identify Trends                                   │  │
│  │ 6. Enrich with Maintenance History                   │  │
│  │ 7. Assess Risk Level                                 │  │
│  │ 8. Generate Recommendations                          │  │
│  │ 9. Assess Sensor Health                              │  │
│  │ 10. Calculate Confidence                             │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Structured Analysis Report                      │
│  • Vehicle ID                                                │
│  • Anomaly Score                                             │
│  • Risk Level                                                │
│  • Trending Parameters                                       │
│  • Historical Context                                        │
│  • Detected Anomalies                                        │
│  • Sensor Health                                             │
│  • Recommendations                                           │
│  • Confidence Score                                          │
│  • Data Quality Score                                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Master Orchestrator Integration                 │
└─────────────────────────────────────────────────────────────┘
```

## Data Structures

### TelematicsReading
```python
@dataclass
class TelematicsReading:
    vehicle_id: str
    timestamp: datetime
    engine_temp: Optional[float]
    oil_pressure: Optional[float]
    battery_voltage: Optional[float]
    fuel_efficiency: Optional[float]
    coolant_temp: Optional[float]
    rpm: Optional[float]
    speed: Optional[float]
    brake_pressure: Optional[float]
    tire_pressure_fl: Optional[float]
    tire_pressure_fr: Optional[float]
    tire_pressure_rl: Optional[float]
    tire_pressure_rr: Optional[float]
    transmission_temp: Optional[float]
    throttle_position: Optional[float]
    mileage: Optional[float]
```

### AnalysisReport
```python
@dataclass
class AnalysisReport:
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
```

## Usage

### Basic Setup

```python
from data_analysis_agent import DataAnalysisAgent, TelematicsReading

# Initialize agent
agent = DataAnalysisAgent(
    model_path='deep_vae_full_model',
    scaler_path='scaler.pkl',
    baseline_window=100,
    anomaly_threshold=0.05
)

# Start processing
agent.start_processing()
```

### Stream Processing

```python
# Subscribe to telematics stream
reading = TelematicsReading(
    vehicle_id='VEH001',
    timestamp=datetime.now(),
    engine_temp=95.0,
    oil_pressure=45.0,
    battery_voltage=12.6,
    # ... other sensors
)

agent.subscribe_to_stream(reading)
```

### Direct Analysis (Synchronous)

```python
# Analyze reading directly
report = agent.analyze_reading(reading)

print(f"Risk Level: {report.risk_level.value}")
print(f"Anomaly Score: {report.anomaly_score:.4f}")
print(f"Recommendations: {report.recommendations}")
```

### Integration with Master Orchestrator

```python
from data_analysis_agent import create_data_analysis_handler
from master_orchestrator import MasterOrchestrator, AgentType

# Create orchestrator
orchestrator = MasterOrchestrator()

# Create and register handler
handler = create_data_analysis_handler(agent)
orchestrator.register_agent(AgentType.DATA_ANALYSIS, handler)

# Start orchestrator
orchestrator.start()
```

## Sensor Validation Ranges

| Sensor | Min | Max | Unit |
|--------|-----|-----|------|
| Engine Temperature | 60 | 120 | °C |
| Oil Pressure | 20 | 80 | PSI |
| Battery Voltage | 11.5 | 14.5 | V |
| Fuel Efficiency | 5 | 50 | MPG |
| Coolant Temperature | 60 | 110 | °C |
| RPM | 0 | 8000 | RPM |
| Speed | 0 | 200 | MPH |
| Brake Pressure | 0 | 150 | PSI |
| Tire Pressure | 28 | 40 | PSI |
| Transmission Temp | 60 | 100 | °C |
| Throttle Position | 0 | 100 | % |
| Mileage | 0 | 500000 | Miles |

## Anomaly Detection

### ML-Based (VAE Model)

1. Extract sensor features
2. Scale features using pre-trained scaler
3. Pass through VAE model
4. Calculate reconstruction error (MSE)
5. Compare against threshold (default: 0.05)
6. Identify contributing sensors

### Rule-Based (Fallback)

Critical thresholds:
- Engine temp > 105°C: +0.3 score
- Battery voltage < 11.8V: +0.2 score
- Oil pressure < 25 PSI: +0.3 score
- Coolant temp > 105°C: +0.2 score

## Trend Detection

Analyzes key sensors over time:
- Engine temperature
- Battery voltage
- Oil pressure
- Fuel efficiency

**Trend Significance**: > 1% relative change per reading

**Concern Assessment**:
- **High**: Concerning direction + > 2x threshold change
- **Medium**: Concerning direction + > threshold change
- **Low**: Normal variation

## Risk Assessment Formula

```python
risk_score = (
    min(anomaly_score * 100, 40) +           # 0-40 points
    min(max_z_score * 5, 30) +               # 0-30 points
    (high_concern_trends * 10) +             # 0-20 points
    maintenance_overdue_score                # 0-10 points
)

if risk_score >= 70: CRITICAL
elif risk_score >= 50: HIGH
elif risk_score >= 30: MEDIUM
else: LOW
```

## Handling Missing/Corrupted Data

### Missing Data
1. Check if baseline exists for vehicle
2. Use baseline mean value for imputation
3. Assign partial data quality credit (0.5)
4. Mark sensor as "missing" in health report

### Corrupted Data
1. Validate against sensor ranges
2. Log corruption warning
3. Use baseline mean value for imputation
4. Assign low data quality credit (0.3)
5. Mark sensor as "corrupted" in health report
6. Increment corruption counter

### Data Quality Score
```python
data_quality = valid_sensors / total_sensors
```

## Maintenance History Integration

### Retrieved Information
- Service dates
- Service types
- Mileage at service
- Issues found
- Parts replaced

### Historical Context
- Last maintenance date
- Days since last service
- Recurring issues (appears > 1 time)
- Significant baseline deviations
- Most deviated sensor

## Performance Characteristics

### Throughput
- Queue capacity: 1000 readings
- Processing time: ~10-50ms per reading (with ML)
- Concurrent processing: Thread-based
- Baseline calculation: O(n) where n = baseline_window

### Memory
- Per-vehicle baseline: ~2KB
- Reading buffer: ~100KB per vehicle (100 readings)
- Model memory: ~50MB (VAE + scaler)

### Scalability
- Supports multiple vehicles concurrently
- Thread-safe operations
- Configurable worker capacity
- Queue-based backpressure handling

## Configuration

```python
DataAnalysisAgent(
    model_path='deep_vae_full_model',    # Path to VAE model
    scaler_path='scaler.pkl',             # Path to feature scaler
    baseline_window=100,                  # Readings for baseline
    anomaly_threshold=0.05                # Anomaly detection threshold
)
```

## Statistics & Monitoring

```python
stats = agent.get_statistics()
```

Returns:
- `total_readings`: Total readings processed
- `anomalies_detected`: Anomalies found
- `corrupted_readings`: Corrupted data count
- `vehicles_monitored`: Unique vehicles
- `queue_size`: Current queue size
- `vehicles_with_baselines`: Baselines created
- `is_running`: Processing status

## Example Scenarios

### Scenario 1: Normal Operation
```
Input: All sensors within normal ranges
Output:
  - Risk Level: LOW
  - Anomaly Score: 0.01
  - Recommendations: ["Continue normal monitoring"]
```

### Scenario 2: Engine Overheating
```
Input: engine_temp=115°C, coolant_temp=108°C
Output:
  - Risk Level: CRITICAL
  - Anomaly Score: 0.35
  - Detected Anomalies: ["High engine temperature: 115°C"]
  - Recommendations: [
      "URGENT: Schedule immediate inspection",
      "Check cooling system and thermostat"
    ]
```

### Scenario 3: Battery Degradation Trend
```
Input: battery_voltage declining over 5 readings (12.8V → 11.8V)
Output:
  - Risk Level: MEDIUM
  - Trending Parameters: [{
      "parameter": "battery_voltage",
      "direction": "decreasing",
      "concern_level": "high"
    }]
  - Recommendations: ["Battery replacement may be needed soon"]
```

### Scenario 4: Missing Sensors
```
Input: 5 of 15 sensors missing data
Output:
  - Data Quality Score: 0.67
  - Sensor Health: {
      "oil_pressure": "missing",
      "fuel_efficiency": "missing",
      ...
    }
  - Uses baseline imputation for missing values
```

## Running the Demo

### Full Integration Demo
```bash
python data_analysis_integration_demo.py 60
```
Runs for 60 seconds, showing:
- Real-time telematics processing
- Anomaly detection
- Workflow creation
- System statistics

### Scenario Testing
```bash
python data_analysis_integration_demo.py test
```
Tests specific scenarios:
- Critical overheating
- Gradual battery degradation
- Detailed report output

### Standalone Agent Test
```bash
python data_analysis_agent.py
```
Tests agent with:
- Normal readings
- Anomalous readings
- Missing data
- Corrupted data

## Integration Points

### Input
- Telematics streams (IoT/vehicle systems)
- Maintenance record server
- Historical baselines

### Output
- Structured analysis reports
- Master Orchestrator (workflow creation)
- Audit logs
- Statistics/monitoring

## Error Handling

- **Queue Full**: Drops reading, logs warning, increments counter
- **Model Load Failure**: Falls back to rule-based detection
- **Corrupted Data**: Imputes from baseline, logs warning
- **Missing Baseline**: Creates new baseline, uses defaults
- **Processing Error**: Logs error, continues processing

## Logging

All events logged to:
- `data_analysis_agent.log` (file)
- Console output

Log levels:
- INFO: Normal operations
- WARNING: Data quality issues
- ERROR: Processing failures

## Future Enhancements

1. **Distributed Processing**
   - Kafka/RabbitMQ integration
   - Multi-node processing
   - Load balancing

2. **Advanced ML**
   - LSTM for temporal patterns
   - Ensemble models
   - Online learning

3. **Enhanced Baselines**
   - Seasonal adjustments
   - Driving pattern recognition
   - Weather correlation

4. **Real-time Dashboards**
   - Live monitoring
   - Alert visualization
   - Fleet overview

## Dependencies

See `requirements.txt`:
- TensorFlow (ML models)
- NumPy (numerical processing)
- Pandas (data handling)
- scikit-learn (preprocessing)

## License

[Your License Here]

## Support

For issues or questions, contact [Your Contact Info]
