"""
Message Schemas for Inter-Agent Communication System
Defines standardized message formats for all agent interactions
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import uuid


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class MessageType(Enum):
    """Types of messages in the system"""
    VEHICLE_DATA = "vehicle_data"
    ANALYSIS_REQUEST = "analysis_request"
    ANALYSIS_RESULT = "analysis_result"
    DIAGNOSIS_REQUEST = "diagnosis_request"
    DIAGNOSIS_RESULT = "diagnosis_result"
    CUSTOMER_ENGAGEMENT = "customer_engagement"
    SCHEDULING_REQUEST = "scheduling_request"
    SCHEDULING_RESULT = "scheduling_result"
    FEEDBACK = "feedback"
    MANUFACTURING_INSIGHT = "manufacturing_insight"
    ERROR = "error"
    TIMEOUT = "timeout"
    ACK = "acknowledgment"


class AgentType(Enum):
    """Agent identifiers"""
    MASTER_ORCHESTRATOR = "master_orchestrator"
    DATA_ANALYSIS = "data_analysis_agent"
    CUSTOMER_ENGAGEMENT = "customer_engagement_agent"
    SCHEDULING = "scheduling_agent"
    EXTERNAL_SYSTEM = "external_system"


@dataclass
class MessageHeader:
    """Standard message header for all communications"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    sender: str = ""
    receiver: str = ""
    message_type: str = ""
    priority: int = MessagePriority.NORMAL.value
    reply_to: Optional[str] = None
    ttl: int = 300  # Time to live in seconds
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VehicleDataMessage:
    """Message containing vehicle sensor data"""
    header: MessageHeader
    payload: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.header.message_type = MessageType.VEHICLE_DATA.value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": self.header.to_dict(),
            "payload": self.payload
        }


@dataclass
class AnalysisRequestMessage:
    """Request for data analysis"""
    header: MessageHeader
    payload: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.header.message_type = MessageType.ANALYSIS_REQUEST.value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": self.header.to_dict(),
            "payload": self.payload
        }


@dataclass
class AnalysisResultMessage:
    """Results from data analysis"""
    header: MessageHeader
    payload: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.header.message_type = MessageType.ANALYSIS_RESULT.value
        self.payload.setdefault("anomaly_detected", False)
        self.payload.setdefault("failure_probability", 0.0)
        self.payload.setdefault("predicted_failures", [])
        self.payload.setdefault("confidence_score", 0.0)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": self.header.to_dict(),
            "payload": self.payload
        }


@dataclass
class CustomerEngagementMessage:
    """Message for customer engagement actions"""
    header: MessageHeader
    payload: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.header.message_type = MessageType.CUSTOMER_ENGAGEMENT.value
        self.payload.setdefault("customer_id", "")
        self.payload.setdefault("vehicle_id", "")
        self.payload.setdefault("message_content", "")
        self.payload.setdefault("channel", "email")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": self.header.to_dict(),
            "payload": self.payload
        }


@dataclass
class SchedulingRequestMessage:
    """Request for appointment scheduling"""
    header: MessageHeader
    payload: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.header.message_type = MessageType.SCHEDULING_REQUEST.value
        self.payload.setdefault("customer_id", "")
        self.payload.setdefault("vehicle_id", "")
        self.payload.setdefault("service_type", "")
        self.payload.setdefault("urgency", "normal")
        self.payload.setdefault("preferred_dates", [])
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": self.header.to_dict(),
            "payload": self.payload
        }


@dataclass
class SchedulingResultMessage:
    """Result of scheduling operation"""
    header: MessageHeader
    payload: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.header.message_type = MessageType.SCHEDULING_RESULT.value
        self.payload.setdefault("appointment_id", "")
        self.payload.setdefault("scheduled_date", "")
        self.payload.setdefault("service_center", "")
        self.payload.setdefault("status", "")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": self.header.to_dict(),
            "payload": self.payload
        }


@dataclass
class FeedbackMessage:
    """Feedback message for system improvement"""
    header: MessageHeader
    payload: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.header.message_type = MessageType.FEEDBACK.value
        self.payload.setdefault("feedback_type", "")
        self.payload.setdefault("rating", 0)
        self.payload.setdefault("comments", "")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": self.header.to_dict(),
            "payload": self.payload
        }


@dataclass
class ManufacturingInsightMessage:
    """Manufacturing insights derived from feedback"""
    header: MessageHeader
    payload: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.header.message_type = MessageType.MANUFACTURING_INSIGHT.value
        self.payload.setdefault("insight_type", "")
        self.payload.setdefault("affected_components", [])
        self.payload.setdefault("recommendation", "")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": self.header.to_dict(),
            "payload": self.payload
        }


@dataclass
class ErrorMessage:
    """Error message for exception handling"""
    header: MessageHeader
    payload: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.header.message_type = MessageType.ERROR.value
        self.payload.setdefault("error_code", "")
        self.payload.setdefault("error_message", "")
        self.payload.setdefault("stack_trace", "")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": self.header.to_dict(),
            "payload": self.payload
        }


@dataclass
class AcknowledgmentMessage:
    """Acknowledgment message"""
    header: MessageHeader
    payload: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.header.message_type = MessageType.ACK.value
        self.payload.setdefault("ack_message_id", "")
        self.payload.setdefault("status", "received")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": self.header.to_dict(),
            "payload": self.payload
        }
