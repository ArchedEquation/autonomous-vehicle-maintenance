# Scheduling Agent Documentation

## Overview

The Scheduling Agent is an intelligent appointment optimization system that handles booking, rescheduling, load balancing, and emergency scheduling for vehicle maintenance services. It uses ML models for load prediction and multi-factor optimization to find the best appointment slots.

## Key Features

### 1. ML-Based Load Prediction
- Uses LSTM model to forecast service center capacity
- Predicts future workload patterns
- Enables proactive load balancing
- Prevents bottlenecks

### 2. Multi-Factor Optimization
Considers 6 key factors with configurable weights:
- **Urgency** (30%): Matches slot timing to urgency level
- **Customer Preference** (20%): Preferred center, time of day
- **Distance** (15%): Proximity to customer location
- **Load Balance** (15%): Distributes workload evenly
- **Expertise Match** (10%): Technician skill requirements
- **Parts Availability** (10%): Required parts in stock

### 3. Emergency Override Logic
- Bypasses normal scheduling rules
- Uses reserved emergency slots
- Can bump non-urgent appointments
- Immediate notification system
- Priority technician assignment

### 4. Intelligent Load Balancing
- Distributes appointments across centers
- Prevents overloading single locations
- Considers predicted future load
- Optimizes resource utilization

### 5. Comprehensive Booking Management
- Appointment creation
- Rescheduling with reason tracking
- Cancellation with inventory release
- Status tracking (6 states)
- Multi-channel notifications

### 6. Service Center Integration
- Real-time slot availability
- Technician expertise matching
- Parts inventory management
- Operating hours compliance
- Capacity management

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│           Booking Request (from Customer Engagement)         │
│  • Urgency Level                                             │
│  • Services Required                                         │
│  • Customer Preferences                                      │
│  • Parts Needed                                              │
│  • Expertise Requirements                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Scheduling Agent                           │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ 1. Emergency Check (override if needed)               │ │
│  │ 2. Get Eligible Centers (expertise, parts)            │ │
│  │ 3. Predict Center Loads (LSTM model)                  │ │
│  │ 4. Get Available Slots (API query)                    │ │
│  │ 5. Multi-Factor Optimization                          │ │
│  │ 6. Create Appointment                                 │ │
│  │ 7. Book & Reserve Resources                           │ │
│  │ 8. Send Notifications                                 │ │
│  └───────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Scheduling Result                               │
│  • Appointment Details                                       │
│  • Alternative Options                                       │
│  • Optimization Score                                        │
│  • Service Center Notifications                             │
└─────────────────────────────────────────────────────────────┘
```

## Data Structures

### BookingRequest
```python
@dataclass
class BookingRequest:
    request_id: str
    vehicle_id: str
    customer_id: str
    urgency_level: UrgencyLevel
    services_required: List[str]
    estimated_duration: float
    diagnostic_details: Dict[str, Any]
    customer_preferences: Dict[str, Any]
    parts_needed: List[str]
    required_expertise: Optional[str]
    preferred_date: Optional[datetime]
    preferred_time: Optional[str]
    preferred_center: Optional[str]
    customer_location: Optional[Dict[str, float]]
```

### Appointment
```python
@dataclass
class Appointment:
    appointment_id: str
    request_id: str
    vehicle_id: str
    customer_id: str
    center_id: str
    center_name: str
    slot: TimeSlot
    services: List[str]
    estimated_duration: float
    estimated_cost: float
    status: AppointmentStatus
    diagnostic_details: Dict[str, Any]
    technician_assigned: str
    parts_reserved: List[str]
    created_at: datetime
    confirmed_at: Optional[datetime]
    completed_at: Optional[datetime]
    notes: str
```

## Usage

### Basic Setup

```python
from scheduling_agent import SchedulingAgent, BookingRequest, UrgencyLevel

# Initialize agent
agent = SchedulingAgent(
    load_model_path='weights_and_metadata/service_load_lstm_model.weights.h5',
    scheduling_model_path='best_model.keras'
)
```

### Schedule Appointment

```python
# Create booking request
request = BookingRequest(
    request_id="REQ001",
    vehicle_id="VEH001",
    customer_id="CUST001",
    urgency_level=UrgencyLevel.HIGH,
    services_required=['brake_repair', 'inspection'],
    estimated_duration=2.5,
    diagnostic_details={'issue': 'brake_wear', 'severity': 'high'},
    customer_preferences={'preferred_time': 'morning'},
    parts_needed=['brake_pads'],
    required_expertise='brakes',
    customer_location={'lat': 40.7128, 'lon': -74.0060}
)

# Schedule
result = agent.schedule_appointment(request)

if result.success:
    print(f"Scheduled at {result.appointment.center_name}")
    print(f"Time: {result.appointment.slot.start_time}")
    print(f"Optimization Score: {result.optimization_score}")
else:
    print(f"Failed: {result.reason}")
```

### Emergency Booking

```python
# Emergency request
emergency_request = BookingRequest(
    request_id="EMERG001",
    vehicle_id="VEH_EMERGENCY",
    customer_id="CUST_EMERGENCY",
    urgency_level=UrgencyLevel.EMERGENCY,  # Triggers override logic
    services_required=['brake_system_failure'],
    estimated_duration=2.0,
    diagnostic_details={'safety_risk': True},
    customer_preferences={},
    parts_needed=['brake_pads'],
    customer_location={'lat': 40.7128, 'lon': -74.0060}
)

result = agent.schedule_appointment(emergency_request)
# Will use emergency slots or bump non-urgent appointments
```

### Reschedule Appointment

```python
# Reschedule existing appointment
new_date = datetime.now() + timedelta(days=5)

result = agent.reschedule_appointment(
    appointment_id="APT001",
    new_preferred_date=new_date,
    reason="Customer requested different date"
)
```

### Cancel Appointment

```python
# Cancel appointment
success = agent.cancel_appointment(
    appointment_id="APT001",
    reason="Customer cancelled"
)
```

## Urgency Levels

| Level | Priority | Timeframe | Behavior |
|-------|----------|-----------|----------|
| EMERGENCY | 1 | Immediate | Override rules, use emergency slots |
| CRITICAL | 2 | Within 24h | High priority, fast scheduling |
| URGENT | 3 | Within 48h | Priority scheduling |
| HIGH | 4 | Within 1 week | Standard priority |
| NORMAL | 5 | Within 2 weeks | Normal scheduling |
| ROUTINE | 6 | Flexible | Batch processing |

## Optimization Algorithm

### Scoring Formula

```python
score = (
    urgency_score * 0.30 +
    preference_score * 0.20 +
    distance_score * 0.15 +
    load_balance_score * 0.15 +
    expertise_score * 0.10 +
    parts_score * 0.10
)
```

### Factor Details

#### 1. Urgency Score (0-1)
- CRITICAL: Prefers slots within 24 hours
- URGENT: Prefers slots within 48 hours
- HIGH: Prefers slots within 1 week
- NORMAL/ROUTINE: Flexible

#### 2. Customer Preference Score (0-1)
- Preferred center: +0.3
- Preferred time of day: +0.2
- Base score: 0.5

#### 3. Distance Score (0-1)
- < 5 miles: 1.0
- 5-10 miles: 0.8
- 10-20 miles: 0.6
- 20-50 miles: 0.4
- > 50 miles: 0.2

#### 4. Load Balance Score (0-1)
- Score = 1.0 - predicted_load
- Favors centers with lower load

#### 5. Expertise Score (0-1)
- Master: 1.0
- Senior: 0.8
- Intermediate: 0.6
- Junior: 0.4

#### 6. Parts Score (0-1)
- All parts available: 1.0
- Some parts missing: 0.5

## Emergency Override Logic

### Trigger Conditions
- `urgency_level == UrgencyLevel.EMERGENCY`
- Safety-critical issues
- Immediate service required

### Override Behavior
1. **Find Nearest Center**: Prioritizes proximity
2. **Check Emergency Slots**: Reserved first slots of day
3. **Override Normal Slots**: Can use any available slot
4. **Bump Non-Urgent**: Reschedules non-urgent appointments
5. **Immediate Notification**: Alerts all parties

### Emergency Slot Reservation
- First slot of each day reserved for emergencies
- One slot per technician
- Can be released if no emergencies

## Load Balancing

### Strategy
1. **Predict Future Load**: Use LSTM model
2. **Calculate Current Load**: Count confirmed appointments
3. **Distribute Evenly**: Favor centers with lower load
4. **Prevent Bottlenecks**: Avoid overloading single center

### Load Calculation
```python
current_load = confirmed_appointments / capacity
```

### Load Prediction
- Uses historical patterns
- Considers day of week
- Accounts for time of day
- Factors in seasonal trends

## Service Center Management

### Center Capabilities
- **Capacity**: Max appointments per day
- **Operating Hours**: Start and end times
- **Technicians**: List with expertise levels
- **Specializations**: Types of services offered
- **Parts Inventory**: Available parts and quantities

### Eligibility Criteria
1. Has required expertise
2. Has required parts in stock
3. Offers required services
4. Within operating hours
5. Has available capacity

## Notifications

### Customer Notifications
- Appointment confirmed
- Date and time
- Service center location
- Services to be performed
- Estimated cost and duration
- Preparation instructions

### Service Center Notifications
- New appointment details
- Vehicle information
- Diagnostic details
- Required services
- Parts needed
- Technician assignment
- Customer preferences

### Emergency Notifications
- Urgent priority flag
- Immediate attention required
- Safety concerns highlighted
- Direct communication channels

## Integration with Master Orchestrator

```python
from scheduling_agent import create_scheduling_handler
from master_orchestrator import MasterOrchestrator, AgentType

# Create orchestrator
orchestrator = MasterOrchestrator()

# Create and register handler
handler = create_scheduling_handler(agent)
orchestrator.register_agent(AgentType.SCHEDULING, handler)

# Start orchestrator
orchestrator.start()
```

## Statistics & Monitoring

```python
stats = agent.get_statistics()
```

Returns:
- `total_requests`: Total booking requests
- `successful_bookings`: Successfully scheduled
- `emergency_bookings`: Emergency appointments
- `rescheduled`: Rescheduled appointments
- `cancelled`: Cancelled appointments
- `success_rate`: Booking success rate
- `average_optimization_score`: Average optimization quality

## Service Center Status

```python
status = agent.get_center_status('SC001')
```

Returns:
- `center_id`: Center identifier
- `name`: Center name
- `current_load`: Current workload (0-1)
- `capacity`: Maximum capacity
- `upcoming_appointments`: Number of upcoming appointments
- `available_technicians`: Technician count
- `parts_inventory`: Parts availability

## Running Demos

### All Demos
```bash
python scheduling_demo.py
```

### Specific Scenarios
```bash
# Emergency override
python scheduling_demo.py emergency

# Load balancing
python scheduling_demo.py loadbalance

# Multi-factor optimization
python scheduling_demo.py optimization

# Rescheduling
python scheduling_demo.py reschedule

# Parts availability
python scheduling_demo.py parts

# Expertise matching
python scheduling_demo.py expertise
```

### Standalone Agent Test
```bash
python scheduling_agent.py
```

## Best Practices

### 1. Emergency Handling
- Always prioritize safety-critical issues
- Use emergency override sparingly
- Document all emergency decisions
- Follow up with affected customers

### 2. Load Balancing
- Monitor center loads regularly
- Distribute appointments evenly
- Consider predicted future load
- Avoid last-minute overloading

### 3. Customer Preferences
- Honor preferences when possible
- Provide alternatives if unavailable
- Explain scheduling decisions
- Offer flexibility

### 4. Resource Management
- Track parts inventory
- Match expertise to complexity
- Reserve resources upon booking
- Release resources upon cancellation

### 5. Optimization
- Tune weights based on business goals
- Monitor optimization scores
- Analyze failed bookings
- Continuously improve algorithm

## Troubleshooting

### Issue: No available slots

**Solutions:**
- Extend search timeframe
- Consider additional service centers
- Check capacity constraints
- Review operating hours

### Issue: Low optimization scores

**Solutions:**
- Adjust optimization weights
- Review eligibility criteria
- Check load prediction accuracy
- Analyze customer preferences

### Issue: Emergency slots unavailable

**Solutions:**
- Implement appointment bumping
- Add emergency capacity
- Extend operating hours
- Add mobile service units

## Future Enhancements

1. **Dynamic Pricing**
   - Peak/off-peak pricing
   - Urgency-based pricing
   - Demand-based optimization

2. **Advanced ML**
   - Reinforcement learning for optimization
   - Customer no-show prediction
   - Service duration prediction

3. **Mobile Service**
   - On-site repairs
   - Mobile technician dispatch
   - Route optimization

4. **Predictive Scheduling**
   - Proactive appointment suggestions
   - Maintenance reminders
   - Seasonal optimization

## License

[Your License Here]

## Support

For issues or questions, contact [Your Contact Info]
