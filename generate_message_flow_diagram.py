"""
Generate Visual Message Flow Diagram
Creates a detailed visualization of the inter-agent communication flow
"""
from channel_definitions import MessageFlow


def generate_detailed_diagram():
    """Generate detailed message flow diagram with all components"""
    
    diagram = """
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                    INTER-AGENT COMMUNICATION SYSTEM                                    ║
║                         Message Flow Diagram                                           ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                  EXTERNAL SYSTEMS                                        │
└──────────────────────────────┬──────────────────────────────────────────────────────────┘
                               │
                               │ Vehicle Sensor Data
                               │ (Real-time telemetry)
                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                          CHANNEL: vehicle.data.input                                     │
│  Message Type: VEHICLE_DATA                                                              │
│  Priority: NORMAL (2)                                                                    │
│  Payload: {vehicle_id, customer_id, sensor_data, timestamp}                              │
└──────────────────────────────┬──────────────────────────────────────────────────────────┘
                               │
                               │ Subscribe & Route
                               ▼
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                          MASTER ORCHESTRATOR                                           ║
║  - Subscribes to ALL agent output channels                                             ║
║  - Coordinates workflow between agents                                                 ║
║  - Tracks correlation IDs for end-to-end monitoring                                    ║
║  - Handles timeouts and errors                                                         ║
║  - Implements retry and escalation logic                                               ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝
                               │
                               │ Initiate Analysis
                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                       CHANNEL: data_analysis.request                                     │
│  Message Type: ANALYSIS_REQUEST                                                          │
│  Priority: NORMAL (2)                                                                    │
│  Timeout: 60 seconds                                                                     │
│  Payload: {vehicle_id, sensor_data, analysis_type}                                       │
└──────────────────────────────┬──────────────────────────────────────────────────────────┘
                               │
                               │ Subscribe & Process
                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                        DATA ANALYSIS AGENT                                               │
│  Subscriptions:                                                                          │
│    - channel.data_analysis.request                                                       │
│    - channel.orchestrator.command                                                        │
│    - channel.system.error                                                                │
│                                                                                          │
│  Processing:                                                                             │
│    1. Anomaly Detection (VAE Model)                                                      │
│    2. Failure Prediction (LSTM Model)                                                    │
│    3. Confidence Scoring                                                                 │
│    4. Recommendation Generation                                                          │
└──────────────────────────────┬──────────────────────────────────────────────────────────┘
                               │
                               │ Publish Results
                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                       CHANNEL: data_analysis.result                                      │
│  Message Type: ANALYSIS_RESULT                                                           │
│  Priority: HIGH (3) if anomaly detected, NORMAL (2) otherwise                            │
│  Payload: {anomaly_detected, failure_probability, predicted_failures,                    │
│            confidence_score, recommendations}                                            │
└──────────────────────────────┬──────────────────────────────────────────────────────────┘
                               │
                               │ Subscribe & Evaluate
                               ▼
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                          MASTER ORCHESTRATOR                                           ║
║  Decision Logic:                                                                       ║
║    IF anomaly_detected OR failure_probability > 0.3:                                   ║
║      → Trigger Customer Engagement                                                     ║
║    ELSE:                                                                               ║
║      → Complete workflow (no action needed)                                            ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝
                               │
                               │ Engage Customer (if needed)
                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                    CHANNEL: customer_engagement.request                                  │
│  Message Type: CUSTOMER_ENGAGEMENT                                                       │
│  Priority: HIGH (3) if critical, NORMAL (2) otherwise                                    │
│  Timeout: 30 seconds                                                                     │
│  Payload: {customer_id, vehicle_id, message_content, channel, analysis_result}           │
└──────────────────────────────┬──────────────────────────────────────────────────────────┘
                               │
                               │ Subscribe & Notify
                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                     CUSTOMER ENGAGEMENT AGENT                                            │
│  Subscriptions:                                                                          │
│    - channel.customer_engagement.request                                                 │
│    - channel.orchestrator.command                                                        │
│    - channel.system.error                                                                │
│                                                                                          │
│  Processing:                                                                             │
│    1. Generate personalized message                                                      │
│    2. Send notification (Email/SMS/Push)                                                 │
│    3. Track customer response                                                            │
│    4. Sentiment analysis on response                                                     │
└──────────────────────────────┬──────────────────────────────────────────────────────────┘
                               │
                               │ Publish Results
                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                    CHANNEL: customer_engagement.result                                   │
│  Message Type: CUSTOMER_ENGAGEMENT_RESULT                                                │
│  Priority: NORMAL (2)                                                                    │
│  Payload: {notification_sent, customer_response, preferred_dates, sentiment}             │
└──────────────────────────────┬──────────────────────────────────────────────────────────┘
                               │
                               │ Subscribe & Evaluate
                               ▼
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                          MASTER ORCHESTRATOR                                           ║
║  Decision Logic:                                                                       ║
║    IF customer_response == "accepted" OR "interested":                                 ║
║      → Trigger Scheduling                                                              ║
║    ELSE:                                                                               ║
║      → Complete workflow                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝
                               │
                               │ Schedule Appointment (if accepted)
                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                       CHANNEL: scheduling.request                                        │
│  Message Type: SCHEDULING_REQUEST                                                        │
│  Priority: NORMAL (2)                                                                    │
│  Timeout: 45 seconds                                                                     │
│  Payload: {customer_id, vehicle_id, service_type, urgency, preferred_dates}              │
└──────────────────────────────┬──────────────────────────────────────────────────────────┘
                               │
                               │ Subscribe & Schedule
                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                          SCHEDULING AGENT                                                │
│  Subscriptions:                                                                          │
│    - channel.scheduling.request                                                          │
│    - channel.orchestrator.command                                                        │
│    - channel.system.error                                                                │
│                                                                                          │
│  Processing:                                                                             │
│    1. Check service center availability                                                  │
│    2. Predict service center load                                                        │
│    3. Optimize appointment slot                                                          │
│    4. Book appointment                                                                   │
│    5. Send confirmation                                                                  │
└──────────────────────────────┬──────────────────────────────────────────────────────────┘
                               │
                               │ Publish Results
                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                       CHANNEL: scheduling.result                                         │
│  Message Type: SCHEDULING_RESULT                                                         │
│  Priority: NORMAL (2)                                                                    │
│  Payload: {appointment_id, scheduled_date, service_center, status}                       │
└──────────────────────────────┬──────────────────────────────────────────────────────────┘
                               │
                               │ Subscribe & Complete
                               ▼
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                          MASTER ORCHESTRATOR                                           ║
║  Workflow Complete:                                                                    ║
║    - Log completion                                                                    ║
║    - Update workflow status                                                            ║
║    - Archive workflow data                                                             ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              FEEDBACK LOOP                                               │
└─────────────────────────────────────────────────────────────────────────────────────────┘

                               ┌──────────────────┐
                               │  Customer        │
                               │  Feedback        │
                               └────────┬─────────┘
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │  CHANNEL: feedback.input      │
                        │  Message Type: FEEDBACK       │
                        └───────────┬───────────────────┘
                                    │
                                    ▼
                        ╔═══════════════════════════╗
                        ║  MASTER ORCHESTRATOR      ║
                        ║  Process Feedback         ║
                        ╚═══════════┬═══════════════╝
                                    │
                                    ▼
                        ┌───────────────────────────────────┐
                        │  CHANNEL: manufacturing.insights  │
                        │  Message Type: MANUFACTURING_     │
                        │                INSIGHT            │
                        └───────────┬───────────────────────┘
                                    │
                                    ▼
                        ┌───────────────────────────┐
                        │  Manufacturing System     │
                        │  (Quality Improvement)    │
                        └───────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════════════════
                                ERROR HANDLING FLOW
═══════════════════════════════════════════════════════════════════════════════════════════

    ┌──────────────┐         ┌──────────────┐         ┌──────────────┐
    │ Agent Error  │         │   Timeout    │         │  Validation  │
    │              │         │   Detected   │         │    Error     │
    └──────┬───────┘         └──────┬───────┘         └──────┬───────┘
           │                        │                        │
           └────────────────────────┼────────────────────────┘
                                    │
                                    ▼
                        ┌───────────────────────────┐
                        │  CHANNEL: system.error    │
                        │  Message Type: ERROR      │
                        │  Priority: HIGH (3)       │
                        └───────────┬───────────────┘
                                    │
                                    ▼
                        ╔═══════════════════════════╗
                        ║  MASTER ORCHESTRATOR      ║
                        ║  Error Handler            ║
                        ╚═══════════┬═══════════════╝
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
            ┌──────────┐    ┌──────────┐    ┌──────────┐
            │  Retry   │    │ Fallback │    │  Manual  │
            │  Logic   │    │  Agent   │    │  Review  │
            └──────────┘    └──────────┘    └──────────┘

═══════════════════════════════════════════════════════════════════════════════════════════
                              MONITORING & LOGGING
═══════════════════════════════════════════════════════════════════════════════════════════

    All messages are logged to: CHANNEL: system.monitoring
    
    Log Entry Format:
    {
        "timestamp": "2024-01-15T10:30:00Z",
        "channel": "channel.data_analysis.request",
        "action": "published",
        "message_id": "uuid",
        "correlation_id": "uuid",
        "sender": "master_orchestrator",
        "receiver": "data_analysis_agent",
        "message_type": "ANALYSIS_REQUEST",
        "priority": 2
    }
    
    UEBA Monitoring:
    - Track message patterns
    - Detect anomalies in agent behavior
    - Monitor workflow completion rates
    - Analyze timeout patterns
    - Identify bottlenecks

═══════════════════════════════════════════════════════════════════════════════════════════
                                PRIORITY LEVELS
═══════════════════════════════════════════════════════════════════════════════════════════

    CRITICAL (4): System failures, safety-critical issues
                  → Processed immediately, bypass queue
    
    HIGH (3):     Predicted failures, urgent customer issues
                  → Processed before normal priority
    
    NORMAL (2):   Regular analysis, standard customer engagement
                  → Standard processing order
    
    LOW (1):      Feedback processing, insights generation
                  → Processed when queue is empty

═══════════════════════════════════════════════════════════════════════════════════════════
                              CORRELATION ID TRACKING
═══════════════════════════════════════════════════════════════════════════════════════════

    Correlation ID: Unique identifier for entire workflow
    
    Example Workflow Trace:
    
    correlation_id: "550e8400-e29b-41d4-a716-446655440000"
    
    1. [10:00:00] VEHICLE_DATA → vehicle.data.input
    2. [10:00:01] ANALYSIS_REQUEST → data_analysis.request
    3. [10:00:03] ANALYSIS_RESULT → data_analysis.result
    4. [10:00:04] CUSTOMER_ENGAGEMENT → customer_engagement.request
    5. [10:00:05] CUSTOMER_ENGAGEMENT_RESULT → customer_engagement.result
    6. [10:00:06] SCHEDULING_REQUEST → scheduling.request
    7. [10:00:08] SCHEDULING_RESULT → scheduling.result
    8. [10:00:09] WORKFLOW_COMPLETE
    
    Total Duration: 9 seconds
    Stages Completed: [data_analysis, customer_engagement, scheduling]

═══════════════════════════════════════════════════════════════════════════════════════════
"""
    
    return diagram


if __name__ == "__main__":
    print(generate_detailed_diagram())
    
    # Also print the workflow from channel_definitions
    print("\n\nWORKFLOW DEFINITIONS:")
    print("=" * 80)
    for workflow_name, workflow_info in MessageFlow.WORKFLOW.items():
        print(f"\n{workflow_name}:")
        print(f"  Input: {workflow_info['input']}")
        print(f"  Output: {workflow_info['output']}")
        print(f"  Description: {workflow_info['description']}")
