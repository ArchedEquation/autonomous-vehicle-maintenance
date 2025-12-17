"""
UEBA Baseline Profiles Configuration
Defines normal behavior patterns for each agent type
"""
from ueba_monitor import BaselineProfile, AgentAction


def get_data_analysis_agent_profile() -> BaselineProfile:
    """Baseline profile for Data Analysis Agent"""
    return BaselineProfile(
        agent_id="data_analysis_agent",
        authorized_resources={
            "vehicle_data",
            "sensor_data",
            "historical_data",
            "ml_models",
            "analysis_results"
        },
        authorized_actions={
            AgentAction.API_CALL.value,
            AgentAction.DATA_ACCESS.value,
            AgentAction.DATA_WRITE.value,
            AgentAction.MESSAGE_SEND.value,
            AgentAction.MESSAGE_RECEIVE.value
        },
        avg_api_calls_per_minute=15.0,
        std_api_calls_per_minute=5.0,
        avg_data_accesses_per_hour=200.0,
        std_data_accesses_per_hour=50.0,
        typical_active_hours={0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23},  # 24/7
        max_concurrent_operations=50,
        allowed_data_scopes={
            "vehicle_telemetry",
            "sensor_readings",
            "maintenance_history",
            "failure_predictions"
        }
    )


def get_customer_engagement_agent_profile() -> BaselineProfile:
    """Baseline profile for Customer Engagement Agent"""
    return BaselineProfile(
        agent_id="customer_engagement_agent",
        authorized_resources={
            "customer_data",
            "customer_preferences",
            "communication_channels",
            "notification_templates",
            "sentiment_models"
        },
        authorized_actions={
            AgentAction.API_CALL.value,
            AgentAction.DATA_ACCESS.value,
            AgentAction.MESSAGE_SEND.value,
            AgentAction.MESSAGE_RECEIVE.value
        },
        avg_api_calls_per_minute=10.0,
        std_api_calls_per_minute=3.0,
        avg_data_accesses_per_hour=100.0,
        std_data_accesses_per_hour=30.0,
        typical_active_hours={6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20},  # Business hours
        max_concurrent_operations=30,
        allowed_data_scopes={
            "customer_profile",
            "customer_preferences",
            "communication_history",
            "sentiment_data"
        }
    )


def get_scheduling_agent_profile() -> BaselineProfile:
    """Baseline profile for Scheduling Agent"""
    return BaselineProfile(
        agent_id="scheduling_agent",
        authorized_resources={
            "appointment_data",
            "service_center_data",
            "availability_data",
            "booking_system",
            "calendar_data"
        },
        authorized_actions={
            AgentAction.API_CALL.value,
            AgentAction.DATA_ACCESS.value,
            AgentAction.DATA_WRITE.value,
            AgentAction.MESSAGE_SEND.value,
            AgentAction.MESSAGE_RECEIVE.value,
            AgentAction.BOOKING_CREATE.value,
            AgentAction.BOOKING_CANCEL.value
        },
        avg_api_calls_per_minute=8.0,
        std_api_calls_per_minute=3.0,
        avg_data_accesses_per_hour=80.0,
        std_data_accesses_per_hour=25.0,
        typical_active_hours={6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20},  # Business hours
        max_concurrent_operations=20,
        allowed_data_scopes={
            "appointment_schedule",
            "service_center_capacity",
            "technician_availability",
            "customer_appointments"
        }
    )


def get_master_orchestrator_profile() -> BaselineProfile:
    """Baseline profile for Master Orchestrator"""
    return BaselineProfile(
        agent_id="master_orchestrator",
        authorized_resources={
            "all_agents",
            "workflow_data",
            "system_metrics",
            "configuration",
            "audit_logs"
        },
        authorized_actions={
            AgentAction.API_CALL.value,
            AgentAction.DATA_ACCESS.value,
            AgentAction.DATA_WRITE.value,
            AgentAction.MESSAGE_SEND.value,
            AgentAction.MESSAGE_RECEIVE.value,
            AgentAction.AUTHORIZATION.value
        },
        avg_api_calls_per_minute=20.0,
        std_api_calls_per_minute=8.0,
        avg_data_accesses_per_hour=300.0,
        std_data_accesses_per_hour=100.0,
        typical_active_hours={0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23},  # 24/7
        max_concurrent_operations=100,
        allowed_data_scopes={
            "all_scopes"  # Orchestrator has access to all data
        }
    )


def get_all_baseline_profiles() -> dict:
    """Get all baseline profiles"""
    return {
        "data_analysis_agent": get_data_analysis_agent_profile(),
        "customer_engagement_agent": get_customer_engagement_agent_profile(),
        "scheduling_agent": get_scheduling_agent_profile(),
        "master_orchestrator": get_master_orchestrator_profile()
    }


# Configurable thresholds for anomaly detection
ANOMALY_DETECTION_CONFIG = {
    "volume_spike_threshold_std": 3.0,  # Standard deviations from mean
    "failed_auth_threshold": 3,  # Number of failed attempts before alert
    "auto_block_threshold": 5,  # Number of alerts before auto-block
    "suspicious_cancellation_threshold": 5,  # Repeated cancellations
    "rapid_access_threshold": 8,  # Unique resources accessed rapidly
    "error_rate_threshold": 0.3,  # 30% error rate
    "stale_agent_hours": 24,  # Hours of inactivity
    "monitoring_window_minutes": 60  # Time window for metrics
}


# Security rules for data access
DATA_ACCESS_RULES = {
    "data_analysis_agent": {
        "allowed_scopes": [
            "vehicle_telemetry",
            "sensor_readings",
            "maintenance_history",
            "failure_predictions"
        ],
        "forbidden_scopes": [
            "customer_payment_info",
            "employee_data",
            "manufacturing_secrets"
        ]
    },
    "customer_engagement_agent": {
        "allowed_scopes": [
            "customer_profile",
            "customer_preferences",
            "communication_history",
            "sentiment_data"
        ],
        "forbidden_scopes": [
            "vehicle_telemetry",
            "manufacturing_data",
            "employee_data",
            "financial_data"
        ]
    },
    "scheduling_agent": {
        "allowed_scopes": [
            "appointment_schedule",
            "service_center_capacity",
            "technician_availability",
            "customer_appointments"
        ],
        "forbidden_scopes": [
            "vehicle_telemetry",
            "manufacturing_data",
            "employee_data",
            "customer_payment_info"
        ]
    },
    "master_orchestrator": {
        "allowed_scopes": ["all"],
        "forbidden_scopes": []
    }
}


# Rate limits per agent type
RATE_LIMITS = {
    "data_analysis_agent": {
        "api_calls_per_minute": 30,
        "data_accesses_per_hour": 500,
        "concurrent_operations": 50
    },
    "customer_engagement_agent": {
        "api_calls_per_minute": 20,
        "data_accesses_per_hour": 200,
        "concurrent_operations": 30
    },
    "scheduling_agent": {
        "api_calls_per_minute": 15,
        "data_accesses_per_hour": 150,
        "concurrent_operations": 20
    },
    "master_orchestrator": {
        "api_calls_per_minute": 50,
        "data_accesses_per_hour": 1000,
        "concurrent_operations": 100
    }
}
