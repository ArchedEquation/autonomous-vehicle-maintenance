"""
Channel Definitions for Inter-Agent Communication
Defines all communication channels and their routing rules
"""
from enum import Enum


class Channel(Enum):
    """Communication channels in the system"""
    
    # Input channels
    VEHICLE_DATA_INPUT = "channel.vehicle.data.input"
    EXTERNAL_REQUEST = "channel.external.request"
    
    # Data Analysis channels
    DATA_ANALYSIS_REQUEST = "channel.data_analysis.request"
    DATA_ANALYSIS_RESULT = "channel.data_analysis.result"
    
    # Customer Engagement channels
    CUSTOMER_ENGAGEMENT_REQUEST = "channel.customer_engagement.request"
    CUSTOMER_ENGAGEMENT_RESULT = "channel.customer_engagement.result"
    
    # Scheduling channels
    SCHEDULING_REQUEST = "channel.scheduling.request"
    SCHEDULING_RESULT = "channel.scheduling.result"
    
    # Feedback channels
    FEEDBACK_INPUT = "channel.feedback.input"
    FEEDBACK_PROCESSED = "channel.feedback.processed"
    
    # Manufacturing Insights
    MANUFACTURING_INSIGHTS = "channel.manufacturing.insights"
    
    # System channels
    ERROR_CHANNEL = "channel.system.error"
    TIMEOUT_CHANNEL = "channel.system.timeout"
    MONITORING_CHANNEL = "channel.system.monitoring"
    
    # Master orchestrator channels
    ORCHESTRATOR_COMMAND = "channel.orchestrator.command"
    ORCHESTRATOR_STATUS = "channel.orchestrator.status"


class ChannelSubscriptions:
    """
    Defines which agents subscribe to which channels
    """
    
    MASTER_ORCHESTRATOR = [
        Channel.VEHICLE_DATA_INPUT.value,
        Channel.EXTERNAL_REQUEST.value,
        Channel.DATA_ANALYSIS_RESULT.value,
        Channel.CUSTOMER_ENGAGEMENT_RESULT.value,
        Channel.SCHEDULING_RESULT.value,
        Channel.FEEDBACK_PROCESSED.value,
        Channel.MANUFACTURING_INSIGHTS.value,
        Channel.ERROR_CHANNEL.value,
        Channel.TIMEOUT_CHANNEL.value,
        Channel.MONITORING_CHANNEL.value,
    ]
    
    DATA_ANALYSIS_AGENT = [
        Channel.DATA_ANALYSIS_REQUEST.value,
        Channel.ORCHESTRATOR_COMMAND.value,
        Channel.ERROR_CHANNEL.value,
    ]
    
    CUSTOMER_ENGAGEMENT_AGENT = [
        Channel.CUSTOMER_ENGAGEMENT_REQUEST.value,
        Channel.ORCHESTRATOR_COMMAND.value,
        Channel.ERROR_CHANNEL.value,
    ]
    
    SCHEDULING_AGENT = [
        Channel.SCHEDULING_REQUEST.value,
        Channel.ORCHESTRATOR_COMMAND.value,
        Channel.ERROR_CHANNEL.value,
    ]
    
    @classmethod
    def get_subscriptions(cls, agent_type: str) -> list:
        """Get channel subscriptions for an agent type"""
        subscriptions_map = {
            "master_orchestrator": cls.MASTER_ORCHESTRATOR,
            "data_analysis_agent": cls.DATA_ANALYSIS_AGENT,
            "customer_engagement_agent": cls.CUSTOMER_ENGAGEMENT_AGENT,
            "scheduling_agent": cls.SCHEDULING_AGENT,
        }
        return subscriptions_map.get(agent_type, [])


class MessageFlow:
    """
    Defines the message flow between agents
    """
    
    WORKFLOW = {
        "vehicle_data_ingestion": {
            "input": Channel.VEHICLE_DATA_INPUT.value,
            "output": Channel.DATA_ANALYSIS_REQUEST.value,
            "description": "Vehicle data enters system and triggers analysis"
        },
        "data_analysis": {
            "input": Channel.DATA_ANALYSIS_REQUEST.value,
            "output": Channel.DATA_ANALYSIS_RESULT.value,
            "description": "Analyze vehicle data for anomalies and predictions"
        },
        "diagnosis_and_engagement": {
            "input": Channel.DATA_ANALYSIS_RESULT.value,
            "output": Channel.CUSTOMER_ENGAGEMENT_REQUEST.value,
            "description": "Based on analysis, engage customer if issues detected"
        },
        "customer_engagement": {
            "input": Channel.CUSTOMER_ENGAGEMENT_REQUEST.value,
            "output": Channel.CUSTOMER_ENGAGEMENT_RESULT.value,
            "description": "Send notifications and communications to customer"
        },
        "scheduling": {
            "input": Channel.SCHEDULING_REQUEST.value,
            "output": Channel.SCHEDULING_RESULT.value,
            "description": "Schedule service appointments"
        },
        "feedback_processing": {
            "input": Channel.FEEDBACK_INPUT.value,
            "output": Channel.FEEDBACK_PROCESSED.value,
            "description": "Process customer feedback"
        },
        "manufacturing_insights": {
            "input": Channel.FEEDBACK_PROCESSED.value,
            "output": Channel.MANUFACTURING_INSIGHTS.value,
            "description": "Generate insights for manufacturing improvements"
        }
    }
    
    @classmethod
    def get_workflow_diagram(cls) -> str:
        """Generate ASCII workflow diagram"""
        diagram = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                    INTER-AGENT MESSAGE FLOW DIAGRAM                       ║
╚═══════════════════════════════════════════════════════════════════════════╝

┌─────────────────┐
│  Vehicle Data   │
│   (External)    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        VEHICLE_DATA_INPUT                                │
│                    (channel.vehicle.data.input)                          │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │     Master     │◄──────────────────┐
                    │  Orchestrator  │                   │
                    └────────┬───────┘                   │
                             │                           │
                             ▼                           │
┌─────────────────────────────────────────────────────────────────────────┐
│                     DATA_ANALYSIS_REQUEST                                │
│                  (channel.data_analysis.request)                         │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │  Data Analysis │
                    │     Agent      │
                    └────────┬───────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     DATA_ANALYSIS_RESULT                                 │
│                  (channel.data_analysis.result)                          │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │     Master     │
                    │  Orchestrator  │
                    │   (Diagnosis)  │
                    └────────┬───────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  CUSTOMER_ENGAGEMENT_REQUEST                             │
│               (channel.customer_engagement.request)                      │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │   Customer     │
                    │  Engagement    │
                    │     Agent      │
                    └────────┬───────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  CUSTOMER_ENGAGEMENT_RESULT                              │
│               (channel.customer_engagement.result)                       │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │     Master     │
                    │  Orchestrator  │
                    └────────┬───────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      SCHEDULING_REQUEST                                  │
│                   (channel.scheduling.request)                           │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │   Scheduling   │
                    │     Agent      │
                    └────────┬───────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      SCHEDULING_RESULT                                   │
│                   (channel.scheduling.result)                            │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │     Master     │
                    │  Orchestrator  │
                    └────────┬───────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        FEEDBACK_INPUT                                    │
│                     (channel.feedback.input)                             │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │     Master     │
                    │  Orchestrator  │
                    │   (Process)    │
                    └────────┬───────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      FEEDBACK_PROCESSED                                  │
│                   (channel.feedback.processed)                           │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    MANUFACTURING_INSIGHTS                                │
│                 (channel.manufacturing.insights)                         │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ Manufacturing  │
                    │    System      │
                    │   (External)   │
                    └────────────────┘

═══════════════════════════════════════════════════════════════════════════
                            ERROR HANDLING
═══════════════════════════════════════════════════════════════════════════

    Any Agent Error ──────────────────────────────────────┐
                                                           │
    Timeout Detected ─────────────────────────────────────┤
                                                           │
                                                           ▼
                                                  ┌────────────────┐
                                                  │     Master     │
                                                  │  Orchestrator  │
                                                  │  (Error/Retry) │
                                                  └────────────────┘

═══════════════════════════════════════════════════════════════════════════
                          PRIORITY LEVELS
═══════════════════════════════════════════════════════════════════════════

    CRITICAL (4): System failures, safety issues
    HIGH (3):     Predicted failures, urgent scheduling
    NORMAL (2):   Regular analysis, customer engagement
    LOW (1):      Feedback processing, insights generation

═══════════════════════════════════════════════════════════════════════════
"""
        return diagram
