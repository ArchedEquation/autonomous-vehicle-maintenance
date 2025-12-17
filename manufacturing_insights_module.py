"""
Manufacturing Quality Insights Module
Aggregates feedback and diagnosis data to identify quality issues and generate CAPA reports
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import statistics


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FailureSeverity(Enum):
    """Failure severity levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ActionStatus(Enum):
    """CAPA action status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"
    REJECTED = "rejected"


@dataclass
class FailureRecord:
    """Individual failure record"""
    record_id: str
    timestamp: str
    vehicle_id: str
    vehicle_model: str
    vehicle_year: int
    manufacturing_batch: str
    component: str
    failure_mode: str
    severity: str
    mileage: int
    diagnosis_data: Dict[str, Any] = field(default_factory=dict)
    customer_feedback: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)



@dataclass
class ComponentAnalysis:
    """Analysis results for a specific component"""
    component_name: str
    total_failures: int
    failure_rate: float
    common_failure_modes: List[Tuple[str, int]]
    affected_models: List[str]
    affected_years: List[int]
    affected_batches: List[str]
    avg_mileage_at_failure: float
    severity_distribution: Dict[str, int]
    trend: str  # "increasing", "stable", "decreasing"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CAPAReport:
    """Corrective and Preventive Action Report"""
    report_id: str
    created_date: str
    component: str
    defect_description: str
    root_cause: str
    frequency: int
    severity: str
    affected_vehicle_models: List[str]
    affected_vehicle_years: List[int]
    affected_batches: List[str]
    estimated_vehicles_affected: int
    recommended_actions: List[str]
    priority: str
    status: str
    assigned_to: Optional[str] = None
    implementation_date: Optional[str] = None
    verification_date: Optional[str] = None
    impact_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)



class ManufacturingInsightsModule:
    """
    Manufacturing Quality Insights Module
    Performs RCA, generates CAPA reports, and tracks quality improvements
    """
    
    def __init__(
        self,
        urgent_failure_threshold: int = 10,
        critical_failure_rate: float = 0.05,
        batch_analysis_schedule: str = "weekly"
    ):
        self.urgent_failure_threshold = urgent_failure_threshold
        self.critical_failure_rate = critical_failure_rate
        self.batch_analysis_schedule = batch_analysis_schedule
        
        # Data storage
        self.failure_records: List[FailureRecord] = []
        self.capa_reports: List[CAPAReport] = []
        self.component_analyses: Dict[str, ComponentAnalysis] = {}
        
        # Tracking
        self.action_tracking: Dict[str, Dict[str, Any]] = {}
        self.impact_measurements: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Callbacks
        self.urgent_alert_callbacks: List[callable] = []
        self.report_callbacks: List[callable] = []
        
        # Running state
        self.is_running = False
        self._batch_task = None
    
    async def start(self):
        """Start the manufacturing insights module"""
        self.is_running = True
        self._batch_task = asyncio.create_task(self._batch_analysis_loop())
        logger.info("Manufacturing Insights Module started")
    
    async def stop(self):
        """Stop the manufacturing insights module"""
        self.is_running = False
        if self._batch_task:
            self._batch_task.cancel()
        logger.info("Manufacturing Insights Module stopped")


    
    async def ingest_failure_data(
        self,
        vehicle_id: str,
        vehicle_model: str,
        vehicle_year: int,
        manufacturing_batch: str,
        component: str,
        failure_mode: str,
        severity: FailureSeverity,
        mileage: int,
        diagnosis_data: Dict[str, Any] = None,
        customer_feedback: Dict[str, Any] = None
    ):
        """
        Ingest failure data from diagnosis and feedback agents
        
        Args:
            vehicle_id: Vehicle identifier
            vehicle_model: Model name
            vehicle_year: Manufacturing year
            manufacturing_batch: Batch identifier
            component: Failed component
            failure_mode: Type of failure
            severity: Failure severity
            mileage: Mileage at failure
            diagnosis_data: Data from diagnosis agent
            customer_feedback: Data from feedback agent
        """
        record = FailureRecord(
            record_id=f"FR-{len(self.failure_records)+1:06d}",
            timestamp=datetime.utcnow().isoformat(),
            vehicle_id=vehicle_id,
            vehicle_model=vehicle_model,
            vehicle_year=vehicle_year,
            manufacturing_batch=manufacturing_batch,
            component=component,
            failure_mode=failure_mode,
            severity=severity.name,
            mileage=mileage,
            diagnosis_data=diagnosis_data or {},
            customer_feedback=customer_feedback or {}
        )
        
        self.failure_records.append(record)
        logger.info(f"Ingested failure record: {record.record_id} - {component}/{failure_mode}")
        
        # Check for urgent issues
        await self._check_urgent_issues(component, failure_mode)


    
    async def _check_urgent_issues(self, component: str, failure_mode: str):
        """Check if component/failure mode requires immediate attention"""
        # Count recent failures (last 7 days)
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        
        recent_failures = [
            r for r in self.failure_records
            if r.component == component
            and r.failure_mode == failure_mode
            and datetime.fromisoformat(r.timestamp) > cutoff_date
        ]
        
        if len(recent_failures) >= self.urgent_failure_threshold:
            logger.critical(
                f"URGENT: {component}/{failure_mode} has {len(recent_failures)} "
                f"failures in last 7 days (threshold: {self.urgent_failure_threshold})"
            )
            
            # Generate immediate CAPA report
            await self._generate_urgent_capa(component, failure_mode, recent_failures)
            
            # Trigger callbacks
            for callback in self.urgent_alert_callbacks:
                try:
                    await callback(component, failure_mode, len(recent_failures))
                except Exception as e:
                    logger.error(f"Error in urgent alert callback: {e}")


    
    async def perform_root_cause_analysis(
        self,
        time_window_days: int = 90
    ) -> Dict[str, ComponentAnalysis]:
        """
        Perform comprehensive root cause analysis
        
        Args:
            time_window_days: Analysis time window
            
        Returns:
            Dictionary of component analyses
        """
        logger.info(f"Performing RCA for last {time_window_days} days")
        
        cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)
        
        # Filter records within time window
        recent_records = [
            r for r in self.failure_records
            if datetime.fromisoformat(r.timestamp) > cutoff_date
        ]
        
        if not recent_records:
            logger.warning("No failure records in time window")
            return {}
        
        # Group by component
        component_failures = defaultdict(list)
        for record in recent_records:
            component_failures[record.component].append(record)
        
        # Analyze each component
        analyses = {}
        
        for component, failures in component_failures.items():
            analysis = self._analyze_component(component, failures, recent_records)
            analyses[component] = analysis
            self.component_analyses[component] = analysis
        
        logger.info(f"RCA complete: Analyzed {len(analyses)} components")
        
        return analyses


    
    def _analyze_component(
        self,
        component: str,
        failures: List[FailureRecord],
        all_records: List[FailureRecord]
    ) -> ComponentAnalysis:
        """Analyze a specific component"""
        
        # Calculate failure rate
        total_vehicles = len(set(r.vehicle_id for r in all_records))
        affected_vehicles = len(set(f.vehicle_id for f in failures))
        failure_rate = affected_vehicles / total_vehicles if total_vehicles > 0 else 0
        
        # Common failure modes
        failure_modes = Counter(f.failure_mode for f in failures)
        common_modes = failure_modes.most_common(5)
        
        # Affected models and years
        affected_models = list(set(f.vehicle_model for f in failures))
        affected_years = sorted(set(f.vehicle_year for f in failures))
        affected_batches = list(set(f.manufacturing_batch for f in failures))
        
        # Average mileage at failure
        mileages = [f.mileage for f in failures]
        avg_mileage = statistics.mean(mileages) if mileages else 0
        
        # Severity distribution
        severity_dist = Counter(f.severity for f in failures)
        
        # Trend analysis (compare last 30 days vs previous 30 days)
        trend = self._calculate_trend(component, failures)
        
        return ComponentAnalysis(
            component_name=component,
            total_failures=len(failures),
            failure_rate=failure_rate,
            common_failure_modes=common_modes,
            affected_models=affected_models,
            affected_years=affected_years,
            affected_batches=affected_batches,
            avg_mileage_at_failure=avg_mileage,
            severity_distribution=dict(severity_dist),
            trend=trend
        )


    
    def _calculate_trend(
        self,
        component: str,
        failures: List[FailureRecord]
    ) -> str:
        """Calculate failure trend"""
        now = datetime.utcnow()
        last_30_days = now - timedelta(days=30)
        previous_30_days = now - timedelta(days=60)
        
        recent_failures = [
            f for f in failures
            if datetime.fromisoformat(f.timestamp) > last_30_days
        ]
        
        previous_failures = [
            f for f in failures
            if previous_30_days < datetime.fromisoformat(f.timestamp) <= last_30_days
        ]
        
        recent_count = len(recent_failures)
        previous_count = len(previous_failures)
        
        if previous_count == 0:
            return "stable" if recent_count == 0 else "increasing"
        
        change_ratio = recent_count / previous_count
        
        if change_ratio > 1.2:
            return "increasing"
        elif change_ratio < 0.8:
            return "decreasing"
        else:
            return "stable"


    
    async def generate_capa_reports(
        self,
        analyses: Dict[str, ComponentAnalysis]
    ) -> List[CAPAReport]:
        """
        Generate CAPA reports based on component analyses
        
        Args:
            analyses: Component analysis results
            
        Returns:
            List of CAPA reports
        """
        logger.info("Generating CAPA reports")
        
        reports = []
        
        for component, analysis in analyses.items():
            # Generate report if failure rate exceeds threshold or trend is increasing
            if (analysis.failure_rate >= self.critical_failure_rate or
                analysis.trend == "increasing" or
                analysis.severity_distribution.get("CRITICAL", 0) > 0):
                
                report = await self._create_capa_report(component, analysis)
                reports.append(report)
                self.capa_reports.append(report)
        
        logger.info(f"Generated {len(reports)} CAPA reports")
        
        # Trigger callbacks
        for report in reports:
            for callback in self.report_callbacks:
                try:
                    await callback(report)
                except Exception as e:
                    logger.error(f"Error in report callback: {e}")
        
        return reports


    
    async def _create_capa_report(
        self,
        component: str,
        analysis: ComponentAnalysis
    ) -> CAPAReport:
        """Create a CAPA report for a component"""
        
        # Determine root cause
        root_cause = self._determine_root_cause(component, analysis)
        
        # Generate defect description
        defect_description = self._generate_defect_description(component, analysis)
        
        # Generate recommended actions
        recommended_actions = self._generate_recommended_actions(component, analysis)
        
        # Determine priority
        priority = self._determine_priority(analysis)
        
        # Estimate affected vehicles
        estimated_affected = self._estimate_affected_vehicles(analysis)
        
        report = CAPAReport(
            report_id=f"CAPA-{len(self.capa_reports)+1:06d}",
            created_date=datetime.utcnow().isoformat(),
            component=component,
            defect_description=defect_description,
            root_cause=root_cause,
            frequency=analysis.total_failures,
            severity=self._get_dominant_severity(analysis.severity_distribution),
            affected_vehicle_models=analysis.affected_models,
            affected_vehicle_years=analysis.affected_years,
            affected_batches=analysis.affected_batches,
            estimated_vehicles_affected=estimated_affected,
            recommended_actions=recommended_actions,
            priority=priority,
            status=ActionStatus.PENDING.value
        )
        
        logger.info(f"Created CAPA report: {report.report_id} for {component}")
        
        return report


    
    def _determine_root_cause(
        self,
        component: str,
        analysis: ComponentAnalysis
    ) -> str:
        """Determine root cause based on analysis"""
        
        # Analyze failure patterns
        if len(analysis.affected_batches) == 1:
            return f"Manufacturing defect in batch {analysis.affected_batches[0]}"
        
        if len(analysis.affected_models) == 1:
            return f"Design issue specific to {analysis.affected_models[0]} model"
        
        if len(analysis.affected_years) == 1:
            return f"Manufacturing process issue in {analysis.affected_years[0]} production year"
        
        if analysis.avg_mileage_at_failure < 20000:
            return "Early-life failure indicating manufacturing or material defect"
        
        if analysis.avg_mileage_at_failure > 100000:
            return "Wear-out failure indicating design life limitation"
        
        # Check for common failure mode
        if analysis.common_failure_modes:
            dominant_mode = analysis.common_failure_modes[0][0]
            return f"Systematic {dominant_mode} across multiple batches/models"
        
        return "Multiple contributing factors - requires detailed investigation"
    
    def _generate_defect_description(
        self,
        component: str,
        analysis: ComponentAnalysis
    ) -> str:
        """Generate defect description"""
        
        top_failure_mode = analysis.common_failure_modes[0][0] if analysis.common_failure_modes else "unknown"
        
        description = (
            f"{component} experiencing {top_failure_mode} failures. "
            f"Total failures: {analysis.total_failures}. "
            f"Failure rate: {analysis.failure_rate*100:.2f}%. "
            f"Average mileage at failure: {analysis.avg_mileage_at_failure:,.0f} miles. "
            f"Trend: {analysis.trend}."
        )
        
        return description


    
    def _generate_recommended_actions(
        self,
        component: str,
        analysis: ComponentAnalysis
    ) -> List[str]:
        """Generate recommended corrective and preventive actions"""
        
        actions = []
        
        # Immediate actions
        if analysis.severity_distribution.get("CRITICAL", 0) > 0:
            actions.append("IMMEDIATE: Issue safety recall for affected vehicles")
            actions.append("IMMEDIATE: Stop production until root cause identified")
        
        # Investigation actions
        actions.append(f"Conduct detailed failure analysis on {component} samples")
        actions.append("Review manufacturing process for affected batches")
        actions.append("Inspect incoming materials and supplier quality")
        
        # Corrective actions based on root cause
        if len(analysis.affected_batches) <= 3:
            actions.append(f"Quarantine and inspect vehicles from batches: {', '.join(analysis.affected_batches)}")
        
        if analysis.avg_mileage_at_failure < 20000:
            actions.append("Review and improve manufacturing quality controls")
            actions.append("Implement enhanced testing procedures")
        
        if analysis.trend == "increasing":
            actions.append("Implement immediate containment actions")
            actions.append("Increase inspection frequency for this component")
        
        # Preventive actions
        actions.append(f"Update design specifications for {component}")
        actions.append("Implement predictive maintenance alerts for this component")
        actions.append("Enhance supplier quality requirements")
        actions.append("Update field service procedures")
        
        # Long-term actions
        actions.append("Consider design redesign if failure rate remains high")
        actions.append("Implement continuous monitoring of this component")
        
        return actions


    
    def _determine_priority(self, analysis: ComponentAnalysis) -> str:
        """Determine CAPA priority"""
        
        critical_count = analysis.severity_distribution.get("CRITICAL", 0)
        high_count = analysis.severity_distribution.get("HIGH", 0)
        
        if critical_count > 0:
            return "CRITICAL"
        
        if analysis.failure_rate >= 0.10:  # 10% failure rate
            return "CRITICAL"
        
        if high_count > 10 or analysis.trend == "increasing":
            return "HIGH"
        
        if analysis.failure_rate >= 0.05:  # 5% failure rate
            return "HIGH"
        
        if analysis.total_failures > 20:
            return "MEDIUM"
        
        return "LOW"
    
    def _get_dominant_severity(self, severity_dist: Dict[str, int]) -> str:
        """Get dominant severity level"""
        if not severity_dist:
            return "MEDIUM"
        
        if severity_dist.get("CRITICAL", 0) > 0:
            return "CRITICAL"
        
        if severity_dist.get("HIGH", 0) > severity_dist.get("MEDIUM", 0):
            return "HIGH"
        
        return "MEDIUM"
    
    def _estimate_affected_vehicles(self, analysis: ComponentAnalysis) -> int:
        """Estimate total vehicles affected"""
        # Simple estimation based on batches and models
        vehicles_per_batch = 1000  # Assumption
        return len(analysis.affected_batches) * vehicles_per_batch


    
    async def _generate_urgent_capa(
        self,
        component: str,
        failure_mode: str,
        failures: List[FailureRecord]
    ):
        """Generate urgent CAPA report"""
        
        # Create quick analysis
        affected_models = list(set(f.vehicle_model for f in failures))
        affected_years = sorted(set(f.vehicle_year for f in failures))
        affected_batches = list(set(f.manufacturing_batch for f in failures))
        
        severity_dist = Counter(f.severity for f in failures)
        dominant_severity = self._get_dominant_severity(dict(severity_dist))
        
        report = CAPAReport(
            report_id=f"CAPA-URGENT-{len(self.capa_reports)+1:06d}",
            created_date=datetime.utcnow().isoformat(),
            component=component,
            defect_description=f"URGENT: {component} experiencing {failure_mode} - {len(failures)} failures in 7 days",
            root_cause="Under investigation - urgent issue",
            frequency=len(failures),
            severity=dominant_severity,
            affected_vehicle_models=affected_models,
            affected_vehicle_years=affected_years,
            affected_batches=affected_batches,
            estimated_vehicles_affected=len(affected_batches) * 1000,
            recommended_actions=[
                "IMMEDIATE: Investigate root cause",
                "IMMEDIATE: Implement containment actions",
                "IMMEDIATE: Notify affected customers",
                "Review recent manufacturing changes",
                "Inspect affected vehicle batches"
            ],
            priority="CRITICAL",
            status=ActionStatus.PENDING.value
        )
        
        self.capa_reports.append(report)
        logger.critical(f"Generated urgent CAPA report: {report.report_id}")
        
        # Trigger callbacks
        for callback in self.report_callbacks:
            try:
                await callback(report)
            except Exception as e:
                logger.error(f"Error in report callback: {e}")


    
    async def track_action_implementation(
        self,
        report_id: str,
        action_description: str,
        status: ActionStatus,
        assigned_to: Optional[str] = None,
        completion_date: Optional[str] = None,
        notes: Optional[str] = None
    ):
        """
        Track implementation of CAPA actions
        
        Args:
            report_id: CAPA report ID
            action_description: Description of action
            status: Current status
            assigned_to: Person/team assigned
            completion_date: Date completed
            notes: Additional notes
        """
        
        if report_id not in self.action_tracking:
            self.action_tracking[report_id] = {
                "actions": [],
                "overall_status": ActionStatus.PENDING.value
            }
        
        action_record = {
            "action": action_description,
            "status": status.value,
            "assigned_to": assigned_to,
            "completion_date": completion_date,
            "notes": notes,
            "updated": datetime.utcnow().isoformat()
        }
        
        self.action_tracking[report_id]["actions"].append(action_record)
        
        # Update overall status
        self._update_capa_status(report_id)
        
        logger.info(f"Tracked action for {report_id}: {action_description} - {status.value}")


    
    def _update_capa_status(self, report_id: str):
        """Update overall CAPA report status based on actions"""
        
        tracking = self.action_tracking.get(report_id)
        if not tracking or not tracking["actions"]:
            return
        
        actions = tracking["actions"]
        
        # Check if all actions completed
        all_completed = all(
            a["status"] in [ActionStatus.COMPLETED.value, ActionStatus.VERIFIED.value]
            for a in actions
        )
        
        if all_completed:
            tracking["overall_status"] = ActionStatus.COMPLETED.value
            
            # Update CAPA report
            for report in self.capa_reports:
                if report.report_id == report_id:
                    report.status = ActionStatus.COMPLETED.value
                    report.implementation_date = datetime.utcnow().isoformat()
                    break
        
        # Check if any in progress
        elif any(a["status"] == ActionStatus.IN_PROGRESS.value for a in actions):
            tracking["overall_status"] = ActionStatus.IN_PROGRESS.value
            
            for report in self.capa_reports:
                if report.report_id == report_id:
                    report.status = ActionStatus.IN_PROGRESS.value
                    break


    
    async def measure_impact(
        self,
        report_id: str,
        measurement_period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Measure impact of implemented CAPA actions
        
        Args:
            report_id: CAPA report ID
            measurement_period_days: Period to measure
            
        Returns:
            Impact metrics
        """
        
        # Find the CAPA report
        report = None
        for r in self.capa_reports:
            if r.report_id == report_id:
                report = r
                break
        
        if not report:
            logger.error(f"CAPA report {report_id} not found")
            return {}
        
        if not report.implementation_date:
            logger.warning(f"CAPA report {report_id} not yet implemented")
            return {}
        
        implementation_date = datetime.fromisoformat(report.implementation_date)
        measurement_end = implementation_date + timedelta(days=measurement_period_days)
        
        # Get failures before and after implementation
        before_failures = [
            f for f in self.failure_records
            if f.component == report.component
            and datetime.fromisoformat(f.timestamp) < implementation_date
            and datetime.fromisoformat(f.timestamp) > (implementation_date - timedelta(days=measurement_period_days))
        ]
        
        after_failures = [
            f for f in self.failure_records
            if f.component == report.component
            and implementation_date < datetime.fromisoformat(f.timestamp) < measurement_end
        ]
        
        before_count = len(before_failures)
        after_count = len(after_failures)
        
        # Calculate improvement
        if before_count > 0:
            reduction_pct = ((before_count - after_count) / before_count) * 100
        else:
            reduction_pct = 0
        
        impact = {
            "report_id": report_id,
            "component": report.component,
            "measurement_period_days": measurement_period_days,
            "failures_before": before_count,
            "failures_after": after_count,
            "reduction_count": before_count - after_count,
            "reduction_percentage": reduction_pct,
            "implementation_date": report.implementation_date,
            "measurement_date": datetime.utcnow().isoformat(),
            "effectiveness": "high" if reduction_pct > 50 else "medium" if reduction_pct > 25 else "low"
        }
        
        # Store impact measurement
        self.impact_measurements[report_id].append(impact)
        
        # Update report
        report.impact_metrics = impact
        
        logger.info(
            f"Impact measurement for {report_id}: "
            f"{reduction_pct:.1f}% reduction in failures"
        )
        
        return impact


    
    async def _batch_analysis_loop(self):
        """Background loop for scheduled batch analysis"""
        
        # Determine interval
        if self.batch_analysis_schedule == "weekly":
            interval_seconds = 7 * 24 * 3600
        elif self.batch_analysis_schedule == "monthly":
            interval_seconds = 30 * 24 * 3600
        else:
            interval_seconds = 7 * 24 * 3600  # Default to weekly
        
        while self.is_running:
            try:
                logger.info("Starting scheduled batch analysis")
                
                # Perform RCA
                analyses = await self.perform_root_cause_analysis()
                
                # Generate CAPA reports
                reports = await self.generate_capa_reports(analyses)
                
                # Measure impact of completed CAPAs
                for report in self.capa_reports:
                    if report.status == ActionStatus.COMPLETED.value and report.implementation_date:
                        await self.measure_impact(report.report_id)
                
                logger.info(f"Batch analysis complete: {len(reports)} new CAPA reports")
                
                # Wait for next interval
                await asyncio.sleep(interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batch analysis loop: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error


    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate summary report of all quality insights"""
        
        # Overall statistics
        total_failures = len(self.failure_records)
        total_capas = len(self.capa_reports)
        
        # CAPA status breakdown
        capa_status = Counter(r.status for r in self.capa_reports)
        
        # Priority breakdown
        capa_priority = Counter(r.priority for r in self.capa_reports)
        
        # Top failing components
        component_failures = Counter(r.component for r in self.failure_records)
        top_components = component_failures.most_common(10)
        
        # Severity distribution
        severity_dist = Counter(r.severity for r in self.failure_records)
        
        # Impact summary
        total_reduction = 0
        measured_capas = 0
        for report_id, measurements in self.impact_measurements.items():
            if measurements:
                latest = measurements[-1]
                total_reduction += latest["reduction_count"]
                measured_capas += 1
        
        summary = {
            "generated_date": datetime.utcnow().isoformat(),
            "total_failure_records": total_failures,
            "total_capa_reports": total_capas,
            "capa_status_breakdown": dict(capa_status),
            "capa_priority_breakdown": dict(capa_priority),
            "top_failing_components": [
                {"component": comp, "failures": count}
                for comp, count in top_components
            ],
            "severity_distribution": dict(severity_dist),
            "impact_summary": {
                "measured_capas": measured_capas,
                "total_failure_reduction": total_reduction,
                "avg_reduction_per_capa": total_reduction / measured_capas if measured_capas > 0 else 0
            },
            "component_analyses": {
                comp: analysis.to_dict()
                for comp, analysis in self.component_analyses.items()
            }
        }
        
        return summary


    
    def export_capa_reports(self, filepath: str, status_filter: Optional[str] = None):
        """Export CAPA reports to JSON file"""
        
        reports_to_export = self.capa_reports
        
        if status_filter:
            reports_to_export = [
                r for r in self.capa_reports
                if r.status == status_filter
            ]
        
        data = {
            "export_date": datetime.utcnow().isoformat(),
            "total_reports": len(reports_to_export),
            "reports": [r.to_dict() for r in reports_to_export]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported {len(reports_to_export)} CAPA reports to {filepath}")
    
    def export_failure_records(self, filepath: str, days: Optional[int] = None):
        """Export failure records to JSON file"""
        
        records_to_export = self.failure_records
        
        if days:
            cutoff = datetime.utcnow() - timedelta(days=days)
            records_to_export = [
                r for r in self.failure_records
                if datetime.fromisoformat(r.timestamp) > cutoff
            ]
        
        data = {
            "export_date": datetime.utcnow().isoformat(),
            "total_records": len(records_to_export),
            "records": [r.to_dict() for r in records_to_export]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported {len(records_to_export)} failure records to {filepath}")
    
    def export_impact_measurements(self, filepath: str):
        """Export impact measurements to JSON file"""
        
        data = {
            "export_date": datetime.utcnow().isoformat(),
            "measurements": dict(self.impact_measurements)
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported impact measurements to {filepath}")
    
    def register_urgent_alert_callback(self, callback: callable):
        """Register callback for urgent alerts"""
        self.urgent_alert_callbacks.append(callback)
    
    def register_report_callback(self, callback: callable):
        """Register callback for new CAPA reports"""
        self.report_callbacks.append(callback)
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate summary report of manufacturing insights"""
        
        # Count CAPAs by status
        pending_capas = sum(1 for r in self.capa_reports if r.status == ActionStatus.PENDING.value)
        in_progress_capas = sum(1 for r in self.capa_reports if r.status == ActionStatus.IN_PROGRESS.value)
        completed_capas = sum(1 for r in self.capa_reports if r.status == ActionStatus.COMPLETED.value)
        
        # Top failing components
        component_failures = Counter(r.component for r in self.failure_records)
        top_components = component_failures.most_common(10)
        
        # Recent failures (last 30 days)
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        recent_failures = [
            r for r in self.failure_records
            if datetime.fromisoformat(r.timestamp) > cutoff_date
        ]
        
        # Severity distribution
        severity_dist = Counter(r.severity for r in self.failure_records)
        
        return {
            "total_failure_records": len(self.failure_records),
            "recent_failures_30d": len(recent_failures),
            "total_capa_reports": len(self.capa_reports),
            "pending_capas": pending_capas,
            "in_progress_capas": in_progress_capas,
            "completed_capas": completed_capas,
            "top_failing_components": top_components,
            "severity_distribution": dict(severity_dist),
            "total_components_analyzed": len(self.component_analyses),
            "total_impact_measurements": sum(len(m) for m in self.impact_measurements.values())
        }
