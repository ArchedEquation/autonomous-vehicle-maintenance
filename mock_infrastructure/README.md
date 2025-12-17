# Mock Infrastructure for Vehicle Maintenance System

## Overview

This mock infrastructure provides a complete simulation environment for testing the vehicle predictive maintenance system. It includes synthetic vehicle data, streaming telematics, maintenance records, service scheduling, and customer interaction simulation.

## Components

### 1. Synthetic Vehicle Dataset (`synthetic_vehicle_data.py`)

Generates 10 realistic vehicles with:
- **Vehicle Information**: VIN, model, year, manufacturing batch
- **Owner Details**: Name, email, phone, address
- **Current State**: Mileage, registration, insurance
- **Maintenance History**: Past services, parts replaced, costs
- **Telematics Baseline**: Engine temp, oil pressure, battery, brake pads, etc.
- **Failure Scenarios**: Realistic issues with predicted failure dates

**Usage:**
```bash
python mock_infrastructure/synthetic_vehicle_data.py
```

**Output:** `synthetic_vehicles.json`

### 2. Telematics API (`telematics_api.py`)

REST API that streams vehicle sensor data every 5 seconds with realistic fluctuations.

**Features:**
- Real-time telemetry updates
- Driving cycle simulation
- Failure scenario effects
- WebSocket streaming support

**Endpoints:**
- `GET /api/vehicles` - List all vehicles
- `GET /api/telemetry/{vin}` - Get current telemetry
- `GET /api/telemetry/all` - Get all vehicle telemetry
- `WS /api/stream/{vin}` - Stream telemetry via WebSocket

**Start Server:**
```bash
python mock_infrastructure/telematics_api.py
```

**Access:** http://localhost:8000

### 3. Maintenance Records Database (`maintenance_database.py`)

SQLite database storing complete service history.

**Tables:**
- `vehicles` - Vehicle information
- `service_records` - Service appointments
- `services_performed` - Services in each appointment
- `parts_replaced` - Parts replaced with costs

**Initialize:**
```bash
python mock_infrastructure/maintenance_database.py
```

**Output:** `maintenance_records.db`

**Query Example:**
```python
from maintenance_database import MaintenanceDatabase

db = MaintenanceDatabase()
db.connect()

# Get service history
history = db.get_service_history("1HGBH41JXMN000000")

# Get vehicles needing service
vehicles = db.get_vehicles_needing_service(mileage_threshold=5000)

db.close()
```

### 4. Service Scheduler API (`service_scheduler_api.py`)

REST API for appointment scheduling.

**Features:**
- 3 service centers with different capacities
- Hourly appointment slots
- Availability checking
- Booking and confirmation

**Endpoints:**
- `GET /api/centers` - List service centers
- `GET /api/availability` - Get available slots
- `POST /api/book` - Book an appointment
- `GET /api/appointments/{vin}` - Get vehicle appointments

**Start Server:**
```bash
python mock_infrastructure/service_scheduler_api.py
```

**Access:** http://localhost:8001

### 5. Customer Interaction Simulator (`customer_interaction_simulator.py`)

Simulates customer responses to service notifications.

**Features:**
- 4 personality types (cooperative, busy, skeptical, enthusiastic)
- Realistic response times
- Acceptance/decline decisions
- Chat conversation simulation
- Voice call simulation

**Personality Types:**
- **Cooperative**: 80% acceptance, 30min response, positive sentiment
- **Busy**: 50% acceptance, 180min response, neutral sentiment
- **Skeptical**: 30% acceptance, 60min response, negative sentiment
- **Enthusiastic**: 90% acceptance, 15min response, positive sentiment

**Usage:**
```python
from customer_interaction_simulator import CustomerInteractionSimulator

customer = CustomerInteractionSimulator("John Smith", "cooperative")

response = customer.receive_notification(
    notification_type="maintenance_alert",
    message="Your brake pads need service",
    urgency="high"
)

print(response['response']['decision'])  # 'accepted' or 'declined'
```

## Failure Scenarios

Each vehicle has a realistic failure scenario:

| Vehicle | Component | Issue | Severity | Condition | Days to Failure |
|---------|-----------|-------|----------|-----------|-----------------|
| 0 | Engine | Coolant leak | MEDIUM | 75% | 21 |
| 1 | Battery | Degradation | LOW | 60% | 45 |
| 2 | Brake System | Pads worn 85% | HIGH | 15% | 14 |
| 3 | Transmission | Fluid degradation | MEDIUM | 50% | 30 |
| 4 | Tire | Uneven wear | LOW | 40% | 60 |
| 5 | Electrical | Alternator bearing | MEDIUM | 55% | 25 |
| 6 | Suspension | Strut deterioration | LOW | 45% | 50 |
| 7 | Fuel System | Pump efficiency | MEDIUM | 65% | 35 |
| 8 | Cooling System | Radiator clogging | HIGH | 30% | 18 |
| 9 | Brake System | Fluid contamination | MEDIUM | 50% | 28 |

## Complete Workflow Demo

Run the integrated demo to see all components working together:

```bash
python mock_infrastructure/integrated_demo.py
```

This demonstrates:
1. Vehicle data generation
2. Telematics streaming
3. Maintenance database queries
4. Failure prediction
5. Customer notification
6. Response simulation
7. Appointment scheduling

## Quick Start

### 1. Generate All Data

```bash
# Generate vehicles
python mock_infrastructure/synthetic_vehicle_data.py

# Initialize database
python mock_infrastructure/maintenance_database.py
```

### 2. Start APIs

**Terminal 1 - Telematics API:**
```bash
python mock_infrastructure/telematics_api.py
```

**Terminal 2 - Scheduler API:**
```bash
python mock_infrastructure/service_scheduler_api.py
```

### 3. Test APIs

**Get all vehicles:**
```bash
curl http://localhost:8000/api/vehicles
```

**Get telemetry:**
```bash
curl http://localhost:8000/api/telemetry/1HGBH41JXMN000002
```

**Get available slots:**
```bash
curl "http://localhost:8001/api/availability?center_id=SC001"
```

**Book appointment:**
```bash
curl -X POST http://localhost:8001/api/book \
  -H "Content-Type: application/json" \
  -d '{
    "vin": "1HGBH41JXMN000002",
    "center_id": "SC001",
    "datetime": "2024-01-20T09:00:00",
    "service_type": "Brake Inspection"
  }'
```

## Data Files

After running the setup scripts, you'll have:

- `synthetic_vehicles.json` - Complete vehicle dataset
- `maintenance_records.db` - SQLite database with service history

## Integration with Main System

### Data Analysis Agent

```python
import requests

# Get telemetry
response = requests.get("http://localhost:8000/api/telemetry/1HGBH41JXMN000002")
telemetry = response.json()

# Analyze for anomalies
if telemetry['telemetry']['brake_pad_thickness']['front_left'] < 3.0:
    # Trigger alert
    pass
```

### Customer Engagement Agent

```python
from customer_interaction_simulator import CustomerInteractionSimulator

customer = CustomerInteractionSimulator(owner_name, "cooperative")

response = customer.receive_notification(
    notification_type="maintenance_alert",
    message=alert_message,
    urgency="high"
)

if response['response']['decision'] == 'accepted':
    # Schedule appointment
    pass
```

### Scheduling Agent

```python
import requests

# Get availability
response = requests.get(
    "http://localhost:8001/api/availability",
    params={"center_id": "SC001", "start_date": "2024-01-20"}
)

slots = response.json()['slots']

# Book appointment
booking = {
    "vin": vehicle_vin,
    "center_id": "SC001",
    "datetime": slots[0]['datetime'],
    "service_type": "Brake Inspection"
}

response = requests.post("http://localhost:8001/api/book", json=booking)
appointment = response.json()
```

## Realistic Patterns

### Telematics Fluctuations

- **Engine Temperature**: Rises during driving (195-210°F), cools when idle
- **Oil Pressure**: Correlates with RPM (0 when idle, 30-50 PSI when driving)
- **Battery Voltage**: 12.6V when off, 13.8V when running, degrades over time
- **Speed**: Varies 30-70 mph during driving cycles
- **Brake Pads**: Wear down gradually, critical at <3mm

### Failure Effects

- **Coolant Leak**: Engine temp increases over time
- **Battery Degradation**: Voltage drops, fluctuates
- **Brake Wear**: Pad thickness decreases
- **Alternator Issue**: Battery voltage fluctuates

### Customer Behavior

- **Response Time**: 15-180 minutes depending on personality
- **Acceptance Rate**: 30-90% depending on personality and urgency
- **Sentiment**: Positive, neutral, or negative based on personality

## Requirements

```bash
pip install fastapi uvicorn websockets
```

Or use the main requirements.txt:
```bash
pip install -r requirements.txt
```

## Troubleshooting

### Port Already in Use

If ports 8000 or 8001 are in use, modify the port in the respective API file:

```python
uvicorn.run(app, host="0.0.0.0", port=8002)  # Change port
```

### Database Locked

If you get "database is locked" error, ensure only one connection is open:

```python
db = MaintenanceDatabase()
db.connect()
# ... do work ...
db.close()  # Always close!
```

### Missing Data Files

Run the data generation scripts first:
```bash
python mock_infrastructure/synthetic_vehicle_data.py
python mock_infrastructure/maintenance_database.py
```

## Future Enhancements

- [ ] Add more vehicle models and manufacturers
- [ ] Implement real-time failure progression
- [ ] Add weather effects on vehicle performance
- [ ] Simulate traffic patterns affecting driving cycles
- [ ] Add multi-language support for customer interactions
- [ ] Implement voice recognition simulation
- [ ] Add payment processing simulation
- [ ] Create web dashboard for visualization

## License

Part of the Vehicle Predictive Maintenance Multi-Agent System
