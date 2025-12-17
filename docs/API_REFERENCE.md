# API Reference

Complete API reference for all components of the Vehicle Maintenance Multi-Agent System.

## Master Orchestrator

### Class: `MasterOrchestrator`

Main workflow orchestrator for coordinating multi-agent workflows.

#### Constructor

```python
MasterOrchestrator(max_workers: int = 10)
```

**Parameters:**
- `max_workers` (int): Maximum concurrent task workers. Default: 10

**Example:**
```python
orchestrator = MasterOrchestrator(max_workers=10)
```

#### Methods

##### `register_agent(agent_type: AgentType, handler: Callable)`

Register a worker agent handler.

**Parameters:**
- `agent_type` (AgentType): Type of agent (DATA_ANALYSIS, DIAGNOSIS, etc.)
- `handler` (Callable): Handler function that processes agent tasks

**Returns:** None

**Example:**
```python
orchestrator.register_agent(AgentType.DATA_ANALYSIS, data_handler)
```

##### `start()`

Start the orchestrator task processing.

**Returns:** None

##### `receive_vehicle_telemetry(vehicle_id: str, telemetry_data: Dict[str, Any]) -> str`

Entry point for receiving vehicle telemetry and initiating workflow.

**Parameters:**
- `vehicle_id` (str): Unique vehicle identifier
- `telemetry_data` (Dict): Raw sensor and diagnostic data

**Returns:** str - Unique workflow identifier

**Example:**
```python
workflow_id = orchestrator.receive_vehicle_telemetry('VEH001', telemetry)
```

##### `get_workflow_status(workflow_id: str) -> Optional[Dict[str, Any]]`

Get current status of a workflow.

**Parameters:**
- `workflow_id` (str): Workflow identifier

**Returns:** Dict with workflow status or None if not found

**Response Structure:**
```python
{
    'workflow_id': str,
    'vehicle_id': str,
    'state': str,
    'priority': str,
    'urgency_score': float,
    'created_at': str,
    'updated_at': str,
    'retry_count': int,
    'has_errors': bool,
    'appointment_scheduled': bool
}
```

##### `get_statistics() -> Dict[str, Any]`

Get orchestrator statistics.

**Returns:** Dict with statistics

**Response Structure:**
```python
{
    'total_workflows': int,
    'completed': int,
    'failed': int,
    'urgent_handled': int,
    'active_workflows': int,
    'queue_size': int,
    'workflows_by_state': Dict[str, int],
    'average_completion_time': float
}
```

##### `shutdown()`

Gracefully shutdown the orchestrator.

**Returns:** None

---

## Data Analysis Agent

### Class: `DataAnalysisAgent`

Real-time vehicle telematics processing and anomaly detection.

#### Constructor

```python
DataAnalysisAgent(
    model_path: str = 'deep_vae_full_model',
    scaler_path: str = 'scaler.pkl',
    baseline_window: int = 100,
    anomaly_threshold: float = 0.05
)
```

**Parameters:**
- `model_path` (str): Path to anomaly detection model
- `scaler_path` (str): Path to feature scaler
- `baseline_window` (int): Number of readings for baseline calculation
- `anomaly_threshold` (float): Threshold for anomaly detection

#### Methods

##### `start_processing()`

Start processing telematics stream.

**Returns:** None

##### `stop_processing()`

Stop processing stream.

**Returns:** None

##### `subscribe_to_stream(reading: TelematicsReading)`

Subscribe to real-time telematics stream.

**Parameters:**
- `reading` (TelematicsReading): Telematics reading from vehicle

**Returns:** None

##### `analyze_reading(reading: TelematicsReading) -> AnalysisReport`

Analyze a single telematics reading.

**Parameters:**
- `reading` (TelematicsReading): Telematics reading

**Returns:** AnalysisReport - Structured analysis report

**Example:**
```python
report = agent.analyze_reading(reading)
print(f"Risk: {report.risk_level.value}")
print(f"Anomaly Score: {report.anomaly_score}")
```

##### `get_statistics() -> Dict[str, Any]`

Get agent statistics.

**Returns:** Dict with statistics

**Response Structure:**
```python
{
    'total_readings': int,
    'anomalies_detected': int,
    'corrupted_readings': int,
    'vehicles_monitored': int,
    'queue_size': int,
    'vehicles_with_baselines': int,
    'is_running': bool
}
```

##### `export_baseline(vehicle_id: str) -> Optional[Dict[str, Any]]`

Export baseline for a vehicle.

**Parameters:**
- `vehicle_id` (str): Vehicle identifier

**Returns:** Dict with baseline data or None

##### `import_baseline(baseline_data: Dict[str, Any])`

Import baseline for a vehicle.

**Parameters:**
- `baseline_data` (Dict): Baseline data to import

**Returns:** None

### Data Classes

#### `TelematicsReading`

```python
@dataclass
class TelematicsReading:
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
```

#### `AnalysisReport`

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

---

## Customer Engagement Agent

### Class: `CustomerEngagementAgent`

Voice/chat-capable customer communication system.

#### Constructor

```python
CustomerEngagementAgent(
    sentiment_model_path: str = 'sentiment_model_weights',
    confidence_threshold: float = 0.7,
    escalation_sentiment_threshold: float = -0.5
)
```

**Parameters:**
- `sentiment_model_path` (str): Path to sentiment analysis model
- `confidence_threshold` (float): Minimum confidence for autonomous operation
- `escalation_sentiment_threshold` (float): Sentiment below which to escalate

#### Methods

##### `engage_customer(diagnostic_report: DiagnosticReport, customer_profile: CustomerProfile) -> EngagementResult`

Main entry point: Engage customer based on diagnostic report.

**Parameters:**
- `diagnostic_report` (DiagnosticReport): Diagnostic information
- `customer_profile` (CustomerProfile): Customer information

**Returns:** EngagementResult - Outcome of engagement

**Example:**
```python
result = agent.engage_customer(report, customer)
print(f"Outcome: {result.outcome.value}")
print(f"Scheduled: {result.appointment_scheduled}")
```

##### `get_conversation_transcript(conversation_id: str) -> Optional[List[Dict[str, str]]]`

Get conversation transcript.

**Parameters:**
- `conversation_id` (str): Conversation identifier

**Returns:** List of messages or None

##### `get_statistics() -> Dict[str, Any]`

Get agent statistics.

**Returns:** Dict with statistics

**Response Structure:**
```python
{
    'total_engagements': int,
    'successful_schedules': int,
    'escalations': int,
    'declined': int,
    'average_sentiment': float,
    'success_rate': float,
    'escalation_rate': float
}
```

### Data Classes

#### `DiagnosticReport`

```python
@dataclass
class DiagnosticReport:
    vehicle_id: str
    customer_id: str
    urgency_level: UrgencyLevel
    issues_detected: List[str]
    recommended_services: List[str]
    estimated_cost: float
    risk_description: str
    time_to_failure_days: Optional[int] = None
    safety_critical: bool = False
```

#### `CustomerProfile`

```python
@dataclass
class CustomerProfile:
    customer_id: str
    name: str
    phone: str
    email: str
    preferred_channel: CommunicationChannel
    preferred_time: str
    preferred_location: Optional[str] = None
    language: str = "en"
    communication_style: str = "formal"
    previous_interactions: List[Dict[str, Any]] = None
    sentiment_history: List[float] = None
```

#### `EngagementResult`

```python
@dataclass
class EngagementResult:
    conversation_id: str
    customer_id: str
    vehicle_id: str
    outcome: CustomerResponse
    appointment_scheduled: bool
    appointment_details: Optional[Dict[str, Any]] = None
    customer_preferences: Dict[str, Any] = None
    sentiment_score: float = 0.0
    escalated_to_human: bool = False
    conversation_transcript: List[Dict[str, str]] = None
```

---

## Enumerations

### `AgentType`

```python
class AgentType(Enum):
    DATA_ANALYSIS = "data_analysis_agent"
    DIAGNOSIS = "diagnosis_agent"
    CUSTOMER_ENGAGEMENT = "customer_engagement_agent"
    SCHEDULING = "scheduling_agent"
    FEEDBACK = "feedback_agent"
    MANUFACTURING_QUALITY = "manufacturing_quality_agent"
```

### `WorkflowState`

```python
class WorkflowState(Enum):
    PENDING = "pending"
    DATA_ANALYSIS = "data_analysis"
    DIAGNOSIS = "diagnosis"
    URGENCY_ASSESSMENT = "urgency_assessment"
    CUSTOMER_ENGAGEMENT = "customer_engagement"
    SCHEDULING = "scheduling"
    SCHEDULED = "scheduled"
    IN_SERVICE = "in_service"
    FEEDBACK = "feedback"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"
```

### `TaskPriority`

```python
class TaskPriority(Enum):
    URGENT = 1
    HIGH = 2
    SCHEDULED = 3
    ROUTINE = 4
```

### `RiskLevel`

```python
class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
```

### `UrgencyLevel`

```python
class UrgencyLevel(Enum):
    CRITICAL = "critical"
    URGENT = "urgent"
    PREVENTIVE = "preventive"
    ROUTINE = "routine"
```

### `CommunicationChannel`

```python
class CommunicationChannel(Enum):
    PHONE_CALL = "phone_call"
    SMS = "sms"
    EMAIL = "email"
    APP_NOTIFICATION = "app_notification"
    CHAT = "chat"
```

### `CustomerResponse`

```python
class CustomerResponse(Enum):
    ACCEPT = "accept"
    DECLINE = "decline"
    RESCHEDULE = "reschedule"
    NEED_INFO = "need_info"
    FRUSTRATED = "frustrated"
    UNCERTAIN = "uncertain"
```

---

## Helper Functions

### `create_data_analysis_handler(agent: DataAnalysisAgent) -> Callable`

Create handler function for Master Orchestrator integration.

**Parameters:**
- `agent` (DataAnalysisAgent): Agent instance

**Returns:** Handler function compatible with orchestrator

### `create_customer_engagement_handler(agent: CustomerEngagementAgent) -> Callable`

Create handler function for Master Orchestrator integration.

**Parameters:**
- `agent` (CustomerEngagementAgent): Agent instance

**Returns:** Handler function compatible with orchestrator

---

## Error Handling

All methods may raise:
- `ValueError`: Invalid parameters
- `RuntimeError`: System state errors
- `Exception`: General errors (logged and handled gracefully)

## Thread Safety

- `MasterOrchestrator`: Thread-safe
- `DataAnalysisAgent`: Thread-safe
- `CustomerEngagementAgent`: Thread-safe

## Performance Considerations

- **Orchestrator**: Supports 100+ concurrent workflows
- **Data Analysis**: Processes 100+ readings/second
- **Customer Engagement**: Handles multiple conversations concurrently

---

**Version**: 1.0.0  
**Last Updated**: December 2024
