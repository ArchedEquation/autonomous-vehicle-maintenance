"""
UEBA Integration with Async Agent System
Connects UEBA monitoring to the message queue and agents
"""
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from ueba_monitor import UEBAMonitor, AgentBehaviorEvent, AgentAction, SecurityAlert
from ueba_baseline_profiles import get_all_baseline_profiles, ANOMALY_DETECTION_CONFIG
from message_queue import InMemoryMessageQueue
from message_schemas import MessageType


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UEBAIntegration:
    """
    Integrates UEBA monitoring with the async agent system
    Automatically tracks agent behaviors from message queue
    """
    
    def __init__(
        self,
        ueba_monitor: UEBAMonitor,
        message_queue: InMemoryMessageQueue
    ):
        self.ueba_monitor = ueba_monitor
        self.message_queue = message_queue
        self.is_running = False
        
        # Register baseline profiles
        self._register_baseline_profiles()
        
        # Register alert callback
        self.ueba_monitor.register_alert_callback(self._handle_security_alert)
    
    def _register_baseline_profiles(self):
        """Register all baseline profiles"""
        profiles = get_all_baseline_profiles()
        
        for agent_id, profile in profiles.items():
            self.ueba_monitor.register_baseline_profile(profile)
            logger.info(f"Registered UEBA profile for: {agent_id}")
    
    async def start(self):
        """Start UEBA integration"""
        self.is_running = True
        
        # Start UEBA monitor
        await self.ueba_monitor.start()
        
        # Subscribe to monitoring channel
        await self.message_queue.subscribe(
            "channel.system.monitoring",
            self._process_monitoring_message
        )
        
        logger.info("UEBA Integration started")
    
    async def stop(self):
        """Stop UEBA integration"""
        self.is_running = False
        await self.ueba_monitor.stop()
        logger.info("UEBA Integration stopped")
    
    async def _process_monitoring_message(self, message: Dict[str, Any]):
        """Process monitoring messages from the queue"""
        try:
            header = message.get("header", {})
            
            # Extract event details
            sender = header.get("sender", "unknown")
            receiver = header.get("receiver", "unknown")
            message_type = header.get("message_type", "unknown")
            timestamp = header.get("timestamp", datetime.utcnow().isoformat())
            correlation_id = header.get("correlation_id")
            
            # Determine action type based on message type
            action_type = self._map_message_type_to_action(message_type)
            
            # Track sender behavior
            if sender != "unknown":
                await self._track_agent_behavior(
                    agent_id=sender,
                    action_type=action_type,
                    resource_type=receiver,
                    resource_id=header.get("message_id", ""),
                    success=True,
                    timestamp=timestamp,
                    correlation_id=correlation_id,
                    metadata={
                        "message_type": message_type,
                        "priority": header.get("priority", 2)
                    }
                )
            
            # Track receiver behavior
            if receiver != "unknown" and message_type == MessageType.ACK.value:
                await self._track_agent_behavior(
                    agent_id=receiver,
                    action_type=AgentAction.MESSAGE_RECEIVE.value,
                    resource_type=sender,
                    resource_id=header.get("message_id", ""),
                    success=True,
                    timestamp=timestamp,
                    correlation_id=correlation_id,
                    metadata={
                        "message_type": message_type
                    }
                )
            
        except Exception as e:
            logger.error(f"Error processing monitoring message: {e}")
    
    def _map_message_type_to_action(self, message_type: str) -> str:
        """Map message type to agent action"""
        mapping = {
            MessageType.VEHICLE_DATA.value: AgentAction.DATA_ACCESS.value,
            MessageType.ANALYSIS_REQUEST.value: AgentAction.API_CALL.value,
            MessageType.ANALYSIS_RESULT.value: AgentAction.DATA_WRITE.value,
            MessageType.CUSTOMER_ENGAGEMENT.value: AgentAction.MESSAGE_SEND.value,
            MessageType.SCHEDULING_REQUEST.value: AgentAction.API_CALL.value,
            MessageType.SCHEDULING_RESULT.value: AgentAction.BOOKING_CREATE.value,
            MessageType.ERROR.value: AgentAction.ERROR.value,
            MessageType.ACK.value: AgentAction.MESSAGE_RECEIVE.value
        }
        
        return mapping.get(message_type, AgentAction.API_CALL.value)
    
    async def _track_agent_behavior(
        self,
        agent_id: str,
        action_type: str,
        resource_type: str,
        resource_id: str,
        success: bool,
        timestamp: str,
        correlation_id: str = None,
        metadata: Dict[str, Any] = None
    ):
        """Track agent behavior event"""
        event = AgentBehaviorEvent(
            timestamp=timestamp,
            agent_id=agent_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            success=success,
            metadata=metadata or {},
            correlation_id=correlation_id
        )
        
        await self.ueba_monitor.track_event(event)
    
    async def _handle_security_alert(self, alert: SecurityAlert):
        """Handle security alerts"""
        logger.warning(f"SECURITY ALERT: {alert.severity} - {alert.description}")
        
        # If agent was auto-blocked, notify the system
        if alert.auto_blocked:
            logger.critical(f"AGENT AUTO-BLOCKED: {alert.agent_id}")
            
            # Could send notification to admin here
            # Could also trigger circuit breaker in message queue
    
    async def track_data_access(
        self,
        agent_id: str,
        data_type: str,
        data_id: str,
        data_scope: str,
        success: bool = True
    ):
        """Manually track data access event"""
        event = AgentBehaviorEvent(
            timestamp=datetime.utcnow().isoformat(),
            agent_id=agent_id,
            action_type=AgentAction.DATA_ACCESS.value,
            resource_type=data_type,
            resource_id=data_id,
            success=success,
            metadata={"data_scope": data_scope}
        )
        
        await self.ueba_monitor.track_event(event)
    
    async def track_api_call(
        self,
        agent_id: str,
        api_endpoint: str,
        success: bool = True,
        response_code: int = 200
    ):
        """Manually track API call event"""
        event = AgentBehaviorEvent(
            timestamp=datetime.utcnow().isoformat(),
            agent_id=agent_id,
            action_type=AgentAction.API_CALL.value,
            resource_type="api",
            resource_id=api_endpoint,
            success=success,
            metadata={"response_code": response_code}
        )
        
        await self.ueba_monitor.track_event(event)
    
    async def track_booking_action(
        self,
        agent_id: str,
        action: str,  # "create" or "cancel"
        booking_id: str,
        success: bool = True
    ):
        """Manually track booking action"""
        action_type = (
            AgentAction.BOOKING_CREATE.value 
            if action == "create" 
            else AgentAction.BOOKING_CANCEL.value
        )
        
        event = AgentBehaviorEvent(
            timestamp=datetime.utcnow().isoformat(),
            agent_id=agent_id,
            action_type=action_type,
            resource_type="booking",
            resource_id=booking_id,
            success=success,
            metadata={"action": action}
        )
        
        await self.ueba_monitor.track_event(event)
    
    async def track_authentication(
        self,
        agent_id: str,
        success: bool,
        auth_method: str = "token"
    ):
        """Manually track authentication attempt"""
        event = AgentBehaviorEvent(
            timestamp=datetime.utcnow().isoformat(),
            agent_id=agent_id,
            action_type=AgentAction.AUTHENTICATION.value,
            resource_type="auth_system",
            resource_id=agent_id,
            success=success,
            metadata={"auth_method": auth_method}
        )
        
        await self.ueba_monitor.track_event(event)
    
    def get_agent_security_report(self, agent_id: str) -> Dict[str, Any]:
        """Get comprehensive security report for an agent"""
        stats = self.ueba_monitor.get_agent_statistics(agent_id)
        alerts = self.ueba_monitor.get_all_alerts(agent_id=agent_id)
        audit_log = self.ueba_monitor.get_audit_log(agent_id=agent_id, limit=50)
        
        return {
            "agent_id": agent_id,
            "statistics": stats,
            "recent_alerts": [alert.to_dict() for alert in alerts[-10:]],
            "recent_activity": audit_log[-20:],
            "is_blocked": agent_id in self.ueba_monitor.blocked_agents,
            "risk_level": self._calculate_risk_level(stats, alerts)
        }
    
    def _calculate_risk_level(
        self,
        stats: Dict[str, Any],
        alerts: list
    ) -> str:
        """Calculate risk level for an agent"""
        if stats.get("is_blocked"):
            return "CRITICAL"
        
        recent_alerts = alerts[-10:]
        critical_alerts = sum(1 for a in recent_alerts if a.severity == "CRITICAL")
        high_alerts = sum(1 for a in recent_alerts if a.severity == "HIGH")
        
        if critical_alerts > 0:
            return "HIGH"
        elif high_alerts >= 3:
            return "MEDIUM"
        elif len(recent_alerts) > 5:
            return "LOW"
        else:
            return "NORMAL"
    
    def get_system_security_dashboard(self) -> Dict[str, Any]:
        """Get system-wide security dashboard"""
        all_agents = ["data_analysis_agent", "customer_engagement_agent", 
                      "scheduling_agent", "master_orchestrator"]
        
        agent_stats = {}
        for agent_id in all_agents:
            agent_stats[agent_id] = self.ueba_monitor.get_agent_statistics(agent_id)
        
        all_alerts = self.ueba_monitor.get_all_alerts(limit=100)
        
        # Count alerts by severity
        alert_counts = {
            "CRITICAL": sum(1 for a in all_alerts if a.severity == "CRITICAL"),
            "HIGH": sum(1 for a in all_alerts if a.severity == "HIGH"),
            "MEDIUM": sum(1 for a in all_alerts if a.severity == "MEDIUM"),
            "LOW": sum(1 for a in all_alerts if a.severity == "LOW"),
            "INFO": sum(1 for a in all_alerts if a.severity == "INFO")
        }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_agents": len(all_agents),
            "blocked_agents": len(self.ueba_monitor.blocked_agents),
            "total_alerts": len(all_alerts),
            "alert_counts_by_severity": alert_counts,
            "agent_statistics": agent_stats,
            "recent_critical_alerts": [
                a.to_dict() for a in all_alerts 
                if a.severity == "CRITICAL"
            ][-5:],
            "system_health": self._calculate_system_health(agent_stats, all_alerts)
        }
    
    def _calculate_system_health(
        self,
        agent_stats: Dict[str, Any],
        alerts: list
    ) -> str:
        """Calculate overall system health"""
        if len(self.ueba_monitor.blocked_agents) > 0:
            return "DEGRADED"
        
        recent_critical = sum(
            1 for a in alerts[-20:] 
            if a.severity == "CRITICAL"
        )
        
        if recent_critical > 0:
            return "WARNING"
        
        recent_high = sum(
            1 for a in alerts[-20:] 
            if a.severity == "HIGH"
        )
        
        if recent_high >= 5:
            return "CAUTION"
        
        return "HEALTHY"
