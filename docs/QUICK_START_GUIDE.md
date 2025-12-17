# Quick Start Guide - Vehicle Maintenance Multi-Agent System

## System Components

1. **Master Orchestrator** (`master_orchestrator.py`)
   - Coordinates all agents
   - Manages workflow state machines
   - Priority-based task queue
   - Retry logic and error handling

2. **Data Analysis Agent** (`data_analysis_agent.py`)
   - Real-time telematics processing
   - Anomaly detection (ML + rules)
   - Historical baseline comparison
   - Risk assessment

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Full Integration Demo

```bash
# Run for 60 seconds
python data_analysis_integration_demo.py 60

# Or run scenario tests
python data_analysis_integration_demo.py test
```

### 3. Test Individual Components

**Data Analysis Agent:**
```bash
python data_analysis_agent.py
```

**Master Orchestrator:**
```bash
python orchestrator_integration_example.py
```

## Basic Usage Examples

### Example 1: Process Single Vehicle

```python
from data_analysis_agent import DataAnalysisAgent, TelematicsReading
from datetime import datetime

# Initialize
agent = DataAnalysisAgent()

# Create reading
reading = TelematicsReading(
    vehicle_id='VEH001',
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

# Analyze
report = agent.analyze_reading(reading)

# View results
print(f"Risk: {report.risk_level.value}")
print(f"Anomaly Score: {report.anomaly_score:.4f}")
print(f"Recommendations: {report.recommendations}")
```

### Example 2: Stream Processing

```python
from data_analysis_agent import DataAnalysisAgent

# Initialize and start
agent = DataAnalysisAgent()
agent.start_processing()

# Subscribe to stream
agent.subscribe_to_stream(reading)

# Get statistics
stats = agent.get_statistics()
print(stats)

# Stop when done
agent.stop_processing()
```

### Example 3: Full System Integration

```python
from data_analysis_integration_demo import IntegratedMaintenanceSystem

# Initialize complete system
system = IntegratedMaintenanceSystem()

# Start all components
system.start()

# System runs automatically...

# Get status
status = system.get_system_status()
print(status)

# Stop when done
system.stop()
```

## Understanding the Output

### Analysis Report Structure

```json
{
  "vehicle_id": "VEH001",
  "timestamp": "2024-12-17T10:30:00",
  "anomaly_score": 0.045,
  "risk_level": "medium",
  "trending_parameters": [
    {
      "parameter": "battery_voltage",
      "direction": "decreasing",
      "relative_change_percent": -2.5,
      "concern_level": "medium"
    }
  ],
  "historical_context": {
    "last_maintenance": {
      "date": "2024-09-15",
      "service_type": "oil_change"
    },
    "recurring_issues": []
  },
  "detected_anomalies": [
    "Anomalous engine_temp: error=0.125"
  ],
  "sensor_health": {
    "engine_temp": "healthy",
    "oil_pressure": "healthy",
    "battery_voltage": "healthy"
  },
  "recommendations": [
    "Schedule maintenance within 2 weeks",
    "Battery replacement may be needed soon"
  ],
  "confidence_score": 0.85,
  "data_quality_score": 0.93
}
```

### Risk Levels

- **CRITICAL**: Immediate action required (stop driving)
- **HIGH**: Schedule within 48 hours
- **MEDIUM**: Schedule within 2 weeks
- **LOW**: Normal monitoring

## Common Scenarios

### Scenario 1: Critical Engine Overheating

**Input:**
```python
reading = TelematicsReading(
    vehicle_id='VEH001',
    timestamp=datetime.now(),
    engine_temp=118.0,  # CRITICAL!
    coolant_temp=112.0,  # CRITICAL!
    # ... other sensors
)
```

**Output:**
- Risk Level: CRITICAL
- Recommendations: "URGENT: Schedule immediate inspection"
- Workflow: Immediate customer engagement

### Scenario 2: Battery Degradation

**Input:** Multiple readings showing declining battery voltage

**Output:**
- Risk Level: MEDIUM
- Trending: battery_voltage decreasing
- Recommendations: "Battery replacement may be needed soon"
- Workflow: Standard scheduling

### Scenario 3: Missing Sensors

**Input:** Some sensors return None

**Output:**
- Data Quality Score: < 1.0
- Sensor Health: Shows "missing" sensors
- Behavior: Uses baseline imputation
- Processing: Continues normally

## Monitoring & Statistics

### Data Analysis Agent Stats

```python
stats = agent.get_statistics()
```

Returns:
- `total_readings`: Readings processed
- `anomalies_detected`: Anomalies found
- `corrupted_readings`: Bad data count
- `vehicles_monitored`: Unique vehicles
- `vehicles_with_baselines`: Baselines created

### Master Orchestrator Stats

```python
stats = orchestrator.get_statistics()
```

Returns:
- `total_workflows`: Total created
- `completed`: Successfully completed
- `failed`: Failed workflows
- `urgent_handled`: Critical cases
- `active_workflows`: Currently processing
- `workflows_by_state`: State breakdown

## Configuration Options

### Data Analysis Agent

```python
DataAnalysisAgent(
    model_path='deep_vae_full_model',  # VAE model path
    scaler_path='scaler.pkl',           # Scaler path
    baseline_window=100,                # Baseline size
    anomaly_threshold=0.05              # Detection threshold
)
```

### Master Orchestrator

```python
MasterOrchestrator(
    max_workers=10  # Concurrent task limit
)
```

## Troubleshooting

### Issue: Model not loading

**Solution:**
- Check model files exist in `deep_vae_full_model/`
- Check `scaler.pkl` exists
- System falls back to rule-based detection automatically

### Issue: Queue full warnings

**Solution:**
- Increase processing speed
- Reduce stream rate
- Increase queue size in code

### Issue: Low data quality scores

**Solution:**
- Check sensor connections
- Verify data format
- Review sensor ranges
- System handles gracefully with imputation

## File Structure

```
.
├── master_orchestrator.py              # Main orchestrator
├── data_analysis_agent.py              # Data analysis agent
├── orchestrator_integration_example.py # Orchestrator demo
├── data_analysis_integration_demo.py   # Full system demo
├── ORCHESTRATOR_README.md              # Orchestrator docs
├── DATA_ANALYSIS_AGENT_README.md       # Agent docs
├── QUICK_START_GUIDE.md                # This file
├── requirements.txt                    # Dependencies
├── deep_vae_full_model/                # Anomaly detection model
├── scaler.pkl                          # Feature scaler
└── data/                               # Sample data
```

## Next Steps

1. **Customize Sensor Ranges**: Edit `sensor_ranges` in `DataAnalysisAgent`
2. **Adjust Risk Thresholds**: Modify `_assess_risk_level()` method
3. **Add Custom Agents**: Implement and register with orchestrator
4. **Connect Real Data**: Replace simulator with actual telematics feed
5. **Deploy**: Set up production environment with monitoring

## Production Deployment Checklist

- [ ] Configure logging to production system
- [ ] Set up database for baselines persistence
- [ ] Connect to actual telematics platform
- [ ] Integrate with real maintenance record system
- [ ] Set up monitoring and alerting
- [ ] Configure backup and recovery
- [ ] Load test with expected vehicle count
- [ ] Set up CI/CD pipeline
- [ ] Document API endpoints
- [ ] Train operations team

## Support & Resources

- **Documentation**: See README files for each component
- **Examples**: Check demo files for usage patterns
- **Logs**: Review `*.log` files for debugging
- **Models**: Ensure ML models are properly trained

## Performance Tips

1. **Baseline Management**: Export/import baselines for persistence
2. **Batch Processing**: Use for non-urgent cases
3. **Queue Monitoring**: Watch queue size to prevent overflow
4. **Model Optimization**: Use TensorFlow Lite for edge deployment
5. **Caching**: Cache maintenance records for frequently accessed vehicles

## Common Commands

```bash
# Run full demo (30 seconds)
python data_analysis_integration_demo.py 30

# Run full demo (60 seconds)
python data_analysis_integration_demo.py 60

# Test specific scenarios
python data_analysis_integration_demo.py test

# Test data analysis agent only
python data_analysis_agent.py

# Test orchestrator only
python orchestrator_integration_example.py
```

## API Quick Reference

### Data Analysis Agent

```python
# Initialize
agent = DataAnalysisAgent()

# Start/stop processing
agent.start_processing()
agent.stop_processing()

# Analyze reading
report = agent.analyze_reading(reading)

# Subscribe to stream
agent.subscribe_to_stream(reading)

# Get statistics
stats = agent.get_statistics()

# Export/import baseline
baseline = agent.export_baseline('VEH001')
agent.import_baseline(baseline)
```

### Master Orchestrator

```python
# Initialize
orchestrator = MasterOrchestrator()

# Register agent
orchestrator.register_agent(AgentType.DATA_ANALYSIS, handler)

# Start
orchestrator.start()

# Process vehicle
workflow_id = orchestrator.receive_vehicle_telemetry(vehicle_id, data)

# Get status
status = orchestrator.get_workflow_status(workflow_id)
stats = orchestrator.get_statistics()

# Shutdown
orchestrator.shutdown()
```

## Getting Help

1. Check the detailed README files
2. Review example code in demo files
3. Check log files for errors
4. Verify configuration settings
5. Test with known good data

---

**Ready to start?** Run the demo:
```bash
python data_analysis_integration_demo.py 60
```
