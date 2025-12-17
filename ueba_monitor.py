"""
UEBA (User and Entity Behavior Analytics) Monitoring System
Tracks agent behaviors, detects anomalies, and generates security audit logs
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import numpy as np
from scipy import stats


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security alert levels"""
    INFO = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5


class AgentAction(Enum):
    """Types of agent actions to track"""
    API_CALL = "api_call"
    DATA_ACCESS = "data_access"
    DATA_WRITE = "data_write"
    MESSAGE_SEND = "message_send"
    MESSAGE_RECEIVE = "message_receive"
    BOOKING_CREATE = "booking_create"
    BOOKING_CANCEL = "booking_cancel"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    ERROR = "error"


class AnomalyType(Enum):
    """Types of anomalies detected"""
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    VOLUME_SPIKE = "volume_spike"
    TIMING_ANOMALY = "timing_anomaly"
    FAILED_AUTH = "failed_auth"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    DATA_SCOPE_VIOLATION = "data_scope_violation"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNUSUAL_HOURS = "unusual_hours"


@dataclass
class AgentBehaviorEvent:
    """Single behavior event for an agent"""
    timestamp: str
    agent_id: str
    action_type: str
    resource_type: str
    resource_id: str
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BaselineProfile:
    """Baseline behavior profile for an agent"""
    agent_id: str
    authorized_resources: Set[str] = field(default_factory=set)
    authorized_actions: Set[str] = field(default_factory=set)
    avg_api_calls_per_minute: float = 0.0
    std_api_calls_per_minute: float = 0.0
    avg_data_accesses_per_hour: float = 0.0
    std_data_accesses_per_hour: float = 0.0
    typical_active_hours: Set[int] = field(default_factory=set)
    max_concurrent_operations: int = 10
    allowed_data_scopes: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Convert sets to lists for JSON serialization
        data['authorized_resources'] = list(self.authorized_resources)
        data['authorized_actions'] = list(self.authorized_actions)
        data['typical_active_hours'] = list(self.typical_active_hours)
        data['allowed_data_scopes'] = list(self.allowed_data_scopes)
        return data


@dataclass
class SecurityAlert:
    """Security alert for anomalous behavior"""
    alert_id: str
    timestamp: str
    agent_id: str
    anomaly_type: str
    severity: str
    description: str
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    recommended_action: str = ""
    auto_blocked: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class UEBAMonitor:
    """
    UEBA Monitoring System
    Tracks agent behaviors, detects anomalies, and manages security
    """
    
    def __init__(
        self,
        window_size_minutes: int = 60,
        anomaly_threshold_std: float = 3.0,
        auto_block_threshold: int = 5
    ):
        self.window_size_minutes = window_size_minutes
        self.anomaly_threshold_std = anomaly_threshold_std
        self.auto_block_threshold = auto_block_threshold
        
        # Behavior tracking
        self.behavior_events: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=10000)
        )
        
        # Baseline profiles
        self.baseline_profiles: Dict[str, BaselineProfile] = {}
        
        # Security alerts
        self.security_alerts: List[SecurityAlert] = []
        
        # Blocked agents
        self.blocked_agents: Set[str] = set()
        
        # Real-time metrics
        self.agent_metrics: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "api_calls_last_minute": 0,
                "data_accesses_last_hour": 0,
                "failed_auth_attempts": 0,
                "concurrent_operations": 0,
                "last_activity": None
            }
        )
        
        # Audit log
        self.audit_log: List[Dict[str, Any]] = []
        
        # Alert callbacks
        self.alert_callbacks: List[callable] = []
        
        # Running state
        self.is_running = False
        self._monitoring_task = None
    
    async def start(self):
        """Start the UEBA monitoring system"""
        self.is_running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("UEBA Monitor started")
    
    async def stop(self):
        """Stop the UEBA monitoring system"""
        self.is_running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
        logger.info("UEBA Monitor stopped")
    
    def register_baseline_profile(self, profile: BaselineProfile):
        """Register a baseline behavior profile for an agent"""
        self.baseline_profiles[profile.agent_id] = profile
        logger.info(f"Registered baseline profile for agent: {profile.agent_id}")
    
    def register_alert_callback(self, callback: callable):
        """Register a callback for security alerts"""
        self.alert_callbacks.append(callback)
    
    async def track_event(self, event: AgentBehaviorEvent):
        """
        Track an agent behavior event
        
        Args:
            event: AgentBehaviorEvent to track
        """
        # Check if agent is blocked
        if event.agent_id in self.blocked_agents:
            logger.warning(f"Blocked agent {event.agent_id} attempted action: {event.action_type}")
            await self._create_alert(
                agent_id=event.agent_id,
                anomaly_type=AnomalyType.UNAUTHORIZED_ACCESS,
                severity=SecurityLevel.CRITICAL,
                description=f"Blocked agent attempted action: {event.action_type}",
                evidence=[event.to_dict()]
            )
            return
        
        # Store event
        self.behavior_events[event.agent_id].append(event)
        
        # Update real-time metrics
        self._update_metrics(event)
        
        # Log to audit trail
        self._log_to_audit(event)
        
        # Check for anomalies
        await self._check_for_anomalies(event)
    
    def _update_metrics(self, event: AgentBehaviorEvent):
        """Update real-time metrics for an agent"""
        metrics = self.agent_metrics[event.agent_id]
        
        # Update last activity
        metrics["last_activity"] = event.timestamp
        
        # Count API calls in last minute
        if event.action_type == AgentAction.API_CALL.value:
            metrics["api_calls_last_minute"] += 1
        
        # Count data accesses in last hour
        if event.action_type == AgentAction.DATA_ACCESS.value:
            metrics["data_accesses_last_hour"] += 1
        
        # Track failed auth attempts
        if event.action_type == AgentAction.AUTHENTICATION.value and not event.success:
            metrics["failed_auth_attempts"] += 1
    
    def _log_to_audit(self, event: AgentBehaviorEvent):
        """Log event to audit trail"""
        audit_entry = {
            "timestamp": event.timestamp,
            "agent_id": event.agent_id,
            "action_type": event.action_type,
            "resource_type": event.resource_type,
            "resource_id": event.resource_id,
            "success": event.success,
            "correlation_id": event.correlation_id,
            "metadata": event.metadata
        }
        
        self.audit_log.append(audit_entry)
        
        # Keep audit log manageable
        if len(self.audit_log) > 100000:
            self.audit_log = self.audit_log[-50000:]
    
    async def _check_for_anomalies(self, event: AgentBehaviorEvent):
        """Check for anomalous behavior"""
        agent_id = event.agent_id
        
        # Get baseline profile
        if agent_id not in self.baseline_profiles:
            logger.warning(f"No baseline profile for agent: {agent_id}")
            return
        
        profile = self.baseline_profiles[agent_id]
        
        # Check 1: Unauthorized resource access
        if event.resource_type not in profile.authorized_resources:
            await self._create_alert(
                agent_id=agent_id,
                anomaly_type=AnomalyType.UNAUTHORIZED_ACCESS,
                severity=SecurityLevel.HIGH,
                description=f"Agent accessed unauthorized resource: {event.resource_type}",
                evidence=[event.to_dict()],
                recommended_action="Review agent permissions and block if necessary"
            )
        
        # Check 2: Unauthorized action
        if event.action_type not in profile.authorized_actions:
            await self._create_alert(
                agent_id=agent_id,
                anomaly_type=AnomalyType.UNAUTHORIZED_ACCESS,
                severity=SecurityLevel.HIGH,
                description=f"Agent performed unauthorized action: {event.action_type}",
                evidence=[event.to_dict()],
                recommended_action="Review agent capabilities and restrict if necessary"
            )
        
        # Check 3: Data scope violation
        if event.action_type == AgentAction.DATA_ACCESS.value:
            data_scope = event.metadata.get("data_scope", "")
            if data_scope and data_scope not in profile.allowed_data_scopes:
                await self._create_alert(
                    agent_id=agent_id,
                    anomaly_type=AnomalyType.DATA_SCOPE_VIOLATION,
                    severity=SecurityLevel.CRITICAL,
                    description=f"Agent accessed data outside allowed scope: {data_scope}",
                    evidence=[event.to_dict()],
                    recommended_action="Immediately review and potentially block agent"
                )
        
        # Check 4: Failed authentication
        if event.action_type == AgentAction.AUTHENTICATION.value and not event.success:
            failed_attempts = self.agent_metrics[agent_id]["failed_auth_attempts"]
            if failed_attempts >= 3:
                await self._create_alert(
                    agent_id=agent_id,
                    anomaly_type=AnomalyType.FAILED_AUTH,
                    severity=SecurityLevel.CRITICAL,
                    description=f"Multiple failed authentication attempts: {failed_attempts}",
                    evidence=[event.to_dict()],
                    recommended_action="Block agent and investigate",
                    auto_block=True
                )
        
        # Check 5: Unusual activity hours
        event_hour = datetime.fromisoformat(event.timestamp).hour
        if event_hour not in profile.typical_active_hours:
            await self._create_alert(
                agent_id=agent_id,
                anomaly_type=AnomalyType.UNUSUAL_HOURS,
                severity=SecurityLevel.MEDIUM,
                description=f"Agent active during unusual hours: {event_hour}:00",
                evidence=[event.to_dict()],
                recommended_action="Monitor for additional suspicious activity"
            )
        
        # Check 6: Volume anomalies
        await self._check_volume_anomalies(agent_id, event)
        
        # Check 7: Suspicious patterns
        await self._check_suspicious_patterns(agent_id, event)
    
    async def _check_volume_anomalies(self, agent_id: str, event: AgentBehaviorEvent):
        """Check for volume-based anomalies"""
        profile = self.baseline_profiles[agent_id]
        metrics = self.agent_metrics[agent_id]
        
        # Check API call rate
        if event.action_type == AgentAction.API_CALL.value:
            current_rate = metrics["api_calls_last_minute"]
            expected_rate = profile.avg_api_calls_per_minute
            std_rate = profile.std_api_calls_per_minute
            
            if std_rate > 0:
                z_score = (current_rate - expected_rate) / std_rate
                
                if abs(z_score) > self.anomaly_threshold_std:
                    await self._create_alert(
                        agent_id=agent_id,
                        anomaly_type=AnomalyType.VOLUME_SPIKE,
                        severity=SecurityLevel.HIGH if z_score > 0 else SecurityLevel.MEDIUM,
                        description=f"Unusual API call volume: {current_rate}/min (expected: {expected_rate:.1f}±{std_rate:.1f})",
                        evidence=[event.to_dict()],
                        recommended_action="Investigate cause of volume spike"
                    )
        
        # Check data access rate
        if event.action_type == AgentAction.DATA_ACCESS.value:
            current_accesses = metrics["data_accesses_last_hour"]
            expected_accesses = profile.avg_data_accesses_per_hour
            std_accesses = profile.std_data_accesses_per_hour
            
            if std_accesses > 0:
                z_score = (current_accesses - expected_accesses) / std_accesses
                
                if abs(z_score) > self.anomaly_threshold_std:
                    await self._create_alert(
                        agent_id=agent_id,
                        anomaly_type=AnomalyType.VOLUME_SPIKE,
                        severity=SecurityLevel.HIGH,
                        description=f"Unusual data access volume: {current_accesses}/hour (expected: {expected_accesses:.1f}±{std_accesses:.1f})",
                        evidence=[event.to_dict()],
                        recommended_action="Review data access patterns"
                    )
    
    async def _check_suspicious_patterns(self, agent_id: str, event: AgentBehaviorEvent):
        """Check for suspicious behavior patterns"""
        # Get recent events for this agent
        recent_events = list(self.behavior_events[agent_id])[-100:]
        
        # Pattern 1: Repeated cancellations
        if event.action_type == AgentAction.BOOKING_CANCEL.value:
            recent_cancellations = [
                e for e in recent_events 
                if e.action_type == AgentAction.BOOKING_CANCEL.value
            ]
            
            if len(recent_cancellations) >= 5:
                await self._create_alert(
                    agent_id=agent_id,
                    anomaly_type=AnomalyType.SUSPICIOUS_PATTERN,
                    severity=SecurityLevel.MEDIUM,
                    description=f"Repeated booking cancellations: {len(recent_cancellations)} in recent history",
                    evidence=[e.to_dict() for e in recent_cancellations[-5:]],
                    recommended_action="Investigate cancellation pattern"
                )
        
        # Pattern 2: Rapid sequential access to different resources
        if event.action_type == AgentAction.DATA_ACCESS.value:
            recent_accesses = [
                e for e in recent_events[-10:]
                if e.action_type == AgentAction.DATA_ACCESS.value
            ]
            
            unique_resources = set(e.resource_id for e in recent_accesses)
            
            if len(unique_resources) >= 8:  # Accessing many different resources quickly
                await self._create_alert(
                    agent_id=agent_id,
                    anomaly_type=AnomalyType.SUSPICIOUS_PATTERN,
                    severity=SecurityLevel.MEDIUM,
                    description=f"Rapid access to multiple resources: {len(unique_resources)} unique resources",
                    evidence=[e.to_dict() for e in recent_accesses],
                    recommended_action="Verify legitimate use case"
                )
        
        # Pattern 3: High error rate
        recent_errors = [e for e in recent_events[-20:] if not e.success]
        error_rate = len(recent_errors) / len(recent_events[-20:]) if recent_events else 0
        
        if error_rate > 0.3:  # More than 30% errors
            await self._create_alert(
                agent_id=agent_id,
                anomaly_type=AnomalyType.SUSPICIOUS_PATTERN,
                severity=SecurityLevel.MEDIUM,
                description=f"High error rate: {error_rate*100:.1f}% of recent operations failed",
                evidence=[e.to_dict() for e in recent_errors[-5:]],
                recommended_action="Investigate cause of errors"
            )
    
    async def _create_alert(
        self,
        agent_id: str,
        anomaly_type: AnomalyType,
        severity: SecurityLevel,
        description: str,
        evidence: List[Dict[str, Any]],
        recommended_action: str = "",
        auto_block: bool = False
    ):
        """Create a security alert"""
        alert = SecurityAlert(
            alert_id=f"ALERT-{len(self.security_alerts)+1:06d}",
            timestamp=datetime.utcnow().isoformat(),
            agent_id=agent_id,
            anomaly_type=anomaly_type.value,
            severity=severity.name,
            description=description,
            evidence=evidence,
            recommended_action=recommended_action,
            auto_blocked=False
        )
        
        # Auto-block if threshold exceeded or explicitly requested
        agent_alerts = [a for a in self.security_alerts if a.agent_id == agent_id]
        
        if auto_block or len(agent_alerts) >= self.auto_block_threshold:
            self.blocked_agents.add(agent_id)
            alert.auto_blocked = True
            alert.recommended_action = "Agent automatically blocked due to high-risk behavior"
            logger.critical(f"AGENT BLOCKED: {agent_id} - {description}")
        
        self.security_alerts.append(alert)
        
        # Log alert
        logger.warning(f"Security Alert [{severity.name}]: {agent_id} - {description}")
        
        # Trigger callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.is_running:
            try:
                # Reset minute/hour counters
                await self._reset_time_based_metrics()
                
                # Check for stale agents
                await self._check_stale_agents()
                
                # Sleep for 1 minute
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
    
    async def _reset_time_based_metrics(self):
        """Reset time-based metrics (called every minute)"""
        current_time = datetime.utcnow()
        
        for agent_id, metrics in self.agent_metrics.items():
            # Reset per-minute counters
            metrics["api_calls_last_minute"] = 0
            
            # Reset per-hour counters (every 60 minutes)
            if current_time.minute == 0:
                metrics["data_accesses_last_hour"] = 0
    
    async def _check_stale_agents(self):
        """Check for agents that haven't been active recently"""
        current_time = datetime.utcnow()
        stale_threshold = timedelta(hours=24)
        
        for agent_id, metrics in self.agent_metrics.items():
            last_activity = metrics.get("last_activity")
            
            if last_activity:
                last_activity_time = datetime.fromisoformat(last_activity)
                
                if current_time - last_activity_time > stale_threshold:
                    logger.info(f"Agent {agent_id} has been inactive for >24 hours")
    
    def get_agent_statistics(self, agent_id: str) -> Dict[str, Any]:
        """Get statistics for a specific agent"""
        events = list(self.behavior_events.get(agent_id, []))
        
        if not events:
            return {"agent_id": agent_id, "total_events": 0}
        
        # Calculate statistics
        total_events = len(events)
        successful_events = sum(1 for e in events if e.success)
        failed_events = total_events - successful_events
        
        action_counts = defaultdict(int)
        for event in events:
            action_counts[event.action_type] += 1
        
        resource_counts = defaultdict(int)
        for event in events:
            resource_counts[event.resource_type] += 1
        
        # Get alerts
        agent_alerts = [a for a in self.security_alerts if a.agent_id == agent_id]
        
        return {
            "agent_id": agent_id,
            "total_events": total_events,
            "successful_events": successful_events,
            "failed_events": failed_events,
            "success_rate": successful_events / total_events if total_events > 0 else 0,
            "action_counts": dict(action_counts),
            "resource_counts": dict(resource_counts),
            "total_alerts": len(agent_alerts),
            "is_blocked": agent_id in self.blocked_agents,
            "current_metrics": self.agent_metrics.get(agent_id, {})
        }
    
    def get_all_alerts(
        self,
        severity: Optional[SecurityLevel] = None,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[SecurityAlert]:
        """Get security alerts with optional filtering"""
        alerts = self.security_alerts
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity.name]
        
        if agent_id:
            alerts = [a for a in alerts if a.agent_id == agent_id]
        
        return alerts[-limit:]
    
    def get_audit_log(
        self,
        agent_id: Optional[str] = None,
        action_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit log entries with optional filtering"""
        log = self.audit_log
        
        if agent_id:
            log = [entry for entry in log if entry["agent_id"] == agent_id]
        
        if action_type:
            log = [entry for entry in log if entry["action_type"] == action_type]
        
        return log[-limit:]
    
    def block_agent(self, agent_id: str, reason: str):
        """Manually block an agent"""
        self.blocked_agents.add(agent_id)
        logger.critical(f"Agent manually blocked: {agent_id} - Reason: {reason}")
        
        # Create alert
        asyncio.create_task(self._create_alert(
            agent_id=agent_id,
            anomaly_type=AnomalyType.UNAUTHORIZED_ACCESS,
            severity=SecurityLevel.CRITICAL,
            description=f"Agent manually blocked: {reason}",
            evidence=[],
            recommended_action="Manual intervention required",
            auto_block=True
        ))
    
    def unblock_agent(self, agent_id: str):
        """Unblock an agent"""
        if agent_id in self.blocked_agents:
            self.blocked_agents.remove(agent_id)
            logger.info(f"Agent unblocked: {agent_id}")
    
    def export_audit_log(self, filepath: str):
        """Export audit log to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.audit_log, f, indent=2)
        logger.info(f"Audit log exported to {filepath}")
    
    def export_alerts(self, filepath: str):
        """Export security alerts to JSON file"""
        alerts_data = [alert.to_dict() for alert in self.security_alerts]
        with open(filepath, 'w') as f:
            json.dump(alerts_data, f, indent=2)
        logger.info(f"Security alerts exported to {filepath}")
