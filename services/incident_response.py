#!/usr/bin/env python3
"""
🚨 Production Feature: Incident Response Management

Implements comprehensive incident response procedures, escalation workflows,
and automated incident management for production environments.

Key Features:
- Incident classification and severity levels
- Automated escalation procedures
- Incident tracking and documentation
- Post-incident analysis and learning
- Integration with monitoring and alerting systems
"""

import logging
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class IncidentSeverity(Enum):
    """Incident severity levels."""
    CRITICAL = "critical"    # Service down, data loss, security breach
    HIGH = "high"           # Major feature broken, performance degraded
    MEDIUM = "medium"       # Minor feature issues, non-critical bugs
    LOW = "low"            # Cosmetic issues, documentation updates

class IncidentStatus(Enum):
    """Incident status states."""
    OPEN = "open"
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    MONITORING = "monitoring"
    RESOLVED = "resolved"
    CLOSED = "closed"

class EscalationLevel(Enum):
    """Escalation levels."""
    L1 = "l1"  # First responder
    L2 = "l2"  # Senior engineer / Team lead
    L3 = "l3"  # Management / CTO

@dataclass
class IncidentContact:
    """Contact information for incident response."""
    name: str
    role: str
    phone: str
    email: str
    escalation_level: EscalationLevel
    availability_hours: str = "24/7"

@dataclass
class Incident:
    """Incident record."""
    id: str
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus
    created_at: datetime
    updated_at: datetime
    affected_services: List[str]
    assigned_to: Optional[str] = None
    escalation_level: EscalationLevel = EscalationLevel.L1
    root_cause: Optional[str] = None
    resolution: Optional[str] = None
    closed_at: Optional[datetime] = None
    
    # SLA tracking
    response_time_minutes: Optional[int] = None
    resolution_time_minutes: Optional[int] = None
    
    # Communication
    customer_impact: Optional[str] = None
    status_page_updated: bool = False
    
    # Learning
    lessons_learned: List[str] = None
    follow_up_actions: List[str] = None
    
    def __post_init__(self):
        if self.lessons_learned is None:
            self.lessons_learned = []
        if self.follow_up_actions is None:
            self.follow_up_actions = []

@dataclass
class IncidentUpdate:
    """Incident status update."""
    incident_id: str
    timestamp: datetime
    author: str
    message: str
    status_change: Optional[IncidentStatus] = None
    severity_change: Optional[IncidentSeverity] = None

class IncidentResponseManager:
    """
    🚨 Production-grade incident response manager.
    
    Manages incident lifecycle, escalation procedures, and post-incident analysis
    to ensure rapid response and continuous improvement.
    """
    
    def __init__(self):
        self.incidents = {}
        self.incident_updates = {}
        
        # Define SLA targets (in minutes)
        self.sla_targets = {
            IncidentSeverity.CRITICAL: {"response": 15, "resolution": 240},    # 15min/4hr
            IncidentSeverity.HIGH: {"response": 30, "resolution": 480},        # 30min/8hr
            IncidentSeverity.MEDIUM: {"response": 120, "resolution": 1440},    # 2hr/24hr
            IncidentSeverity.LOW: {"response": 480, "resolution": 4320}        # 8hr/72hr
        }
        
        # Define escalation matrix
        self.escalation_contacts = [
            IncidentContact(
                name="On-Call Engineer",
                role="First Responder",
                phone="+1-555-ONCALL",
                email="oncall@company.com",
                escalation_level=EscalationLevel.L1
            ),
            IncidentContact(
                name="Technical Lead",
                role="Senior Engineer",
                phone="+1-555-LEAD",
                email="tech-lead@company.com",
                escalation_level=EscalationLevel.L2
            ),
            IncidentContact(
                name="CTO",
                role="Chief Technology Officer",
                phone="+1-555-CTO",
                email="cto@company.com",
                escalation_level=EscalationLevel.L3
            )
        ]
        
        logger.info("🚨 Incident Response Manager initialized")
    
    def create_incident(self, title: str, description: str, severity: IncidentSeverity,
                       affected_services: List[str], reporter: str = "system") -> Incident:
        """Create new incident and trigger response procedures."""
        incident_id = str(uuid.uuid4())[:8]
        
        incident = Incident(
            id=incident_id,
            title=title,
            description=description,
            severity=severity,
            status=IncidentStatus.OPEN,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            affected_services=affected_services
        )
        
        self.incidents[incident_id] = incident
        self.incident_updates[incident_id] = []
        
        # Add initial update
        self._add_incident_update(
            incident_id, 
            f"Incident created by {reporter}",
            "system"
        )
        
        # Trigger automated response
        self._trigger_incident_response(incident)
        
        logger.error(f"🚨 INCIDENT CREATED: {incident_id} - {title} (Severity: {severity.value})")
        return incident
    
    def update_incident(self, incident_id: str, status: Optional[IncidentStatus] = None,
                       severity: Optional[IncidentSeverity] = None, message: str = "",
                       author: str = "system") -> bool:
        """Update incident status and add timeline entry."""
        if incident_id not in self.incidents:
            logger.error(f"Incident {incident_id} not found")
            return False
        
        incident = self.incidents[incident_id]
        old_status = incident.status
        old_severity = incident.severity
        
        # Update fields
        if status:
            incident.status = status
        if severity:
            incident.severity = severity
        
        incident.updated_at = datetime.utcnow()
        
        # Handle status transitions
        if status and status != old_status:
            self._handle_status_transition(incident, old_status, status)
        
        # Add update to timeline
        update = IncidentUpdate(
            incident_id=incident_id,
            timestamp=datetime.utcnow(),
            author=author,
            message=message,
            status_change=status if status != old_status else None,
            severity_change=severity if severity != old_severity else None
        )
        
        self.incident_updates[incident_id].append(update)
        
        logger.info(f"Incident {incident_id} updated: {message}")
        return True
    
    def resolve_incident(self, incident_id: str, resolution: str, 
                        root_cause: str = "", author: str = "system") -> bool:
        """Resolve incident and calculate metrics."""
        if incident_id not in self.incidents:
            return False
        
        incident = self.incidents[incident_id]
        
        # Update incident
        incident.status = IncidentStatus.RESOLVED
        incident.resolution = resolution
        incident.root_cause = root_cause
        incident.updated_at = datetime.utcnow()
        
        # Calculate resolution time
        resolution_delta = incident.updated_at - incident.created_at
        incident.resolution_time_minutes = int(resolution_delta.total_seconds() / 60)
        
        # Add resolution update
        self._add_incident_update(
            incident_id,
            f"Incident resolved: {resolution}",
            author
        )
        
        # Check SLA compliance
        self._check_sla_compliance(incident)
        
        # Trigger post-incident procedures
        self._trigger_post_incident_procedures(incident)
        
        logger.info(f"🎉 Incident {incident_id} resolved: {resolution}")
        return True
    
    def escalate_incident(self, incident_id: str, level: EscalationLevel, 
                         reason: str = "") -> bool:
        """Escalate incident to higher level."""
        if incident_id not in self.incidents:
            return False
        
        incident = self.incidents[incident_id]
        old_level = incident.escalation_level
        incident.escalation_level = level
        
        # Find contact for escalation level
        contact = next(
            (c for c in self.escalation_contacts if c.escalation_level == level),
            None
        )
        
        if contact:
            incident.assigned_to = contact.name
            
            # Send escalation notification
            self._send_escalation_notification(incident, contact, reason)
        
        # Add escalation update
        self._add_incident_update(
            incident_id,
            f"Escalated from {old_level.value} to {level.value}: {reason}",
            "system"
        )
        
        logger.warning(f"📈 Incident {incident_id} escalated to {level.value}: {reason}")
        return True
    
    def _trigger_incident_response(self, incident: Incident):
        """Trigger automated incident response procedures."""
        # 1. Notify on-call engineer
        self._notify_on_call(incident)
        
        # 2. Create incident channel (would integrate with Slack/Teams)
        self._create_incident_channel(incident)
        
        # 3. Update status page if customer-facing
        if self._is_customer_facing(incident):
            self._update_status_page(incident)
        
        # 4. Set up monitoring dashboards
        self._setup_incident_monitoring(incident)
        
        # 5. Schedule escalation if critical
        if incident.severity == IncidentSeverity.CRITICAL:
            self._schedule_escalation(incident)
    
    def _handle_status_transition(self, incident: Incident, 
                                old_status: IncidentStatus, new_status: IncidentStatus):
        """Handle incident status transitions."""
        if old_status == IncidentStatus.OPEN and new_status == IncidentStatus.INVESTIGATING:
            # Record response time
            response_delta = incident.updated_at - incident.created_at
            incident.response_time_minutes = int(response_delta.total_seconds() / 60)
        
        elif new_status == IncidentStatus.RESOLVED:
            # Trigger resolution procedures
            incident.closed_at = incident.updated_at
        
        elif new_status == IncidentStatus.CLOSED:
            # Final closure procedures
            self._finalize_incident(incident)
    
    def _check_sla_compliance(self, incident: Incident):
        """Check if incident met SLA targets."""
        targets = self.sla_targets.get(incident.severity)
        if not targets:
            return
        
        # Check response time
        if incident.response_time_minutes:
            if incident.response_time_minutes > targets["response"]:
                logger.warning(f"🚨 SLA BREACH: Incident {incident.id} response time: "
                             f"{incident.response_time_minutes}min (target: {targets['response']}min)")
        
        # Check resolution time
        if incident.resolution_time_minutes:
            if incident.resolution_time_minutes > targets["resolution"]:
                logger.warning(f"🚨 SLA BREACH: Incident {incident.id} resolution time: "
                             f"{incident.resolution_time_minutes}min (target: {targets['resolution']}min)")
    
    def _trigger_post_incident_procedures(self, incident: Incident):
        """Trigger post-incident analysis procedures."""
        # Schedule post-incident review for critical/high incidents
        if incident.severity in [IncidentSeverity.CRITICAL, IncidentSeverity.HIGH]:
            self._schedule_post_incident_review(incident)
        
        # Generate incident report
        self._generate_incident_report(incident)
        
        # Update knowledge base
        self._update_knowledge_base(incident)
    
    def _add_incident_update(self, incident_id: str, message: str, author: str):
        """Add update to incident timeline."""
        update = IncidentUpdate(
            incident_id=incident_id,
            timestamp=datetime.utcnow(),
            author=author,
            message=message
        )
        
        if incident_id not in self.incident_updates:
            self.incident_updates[incident_id] = []
        
        self.incident_updates[incident_id].append(update)
    
    def _notify_on_call(self, incident: Incident):
        """Notify on-call engineer (placeholder for integration)."""
        logger.info(f"📞 Notifying on-call engineer for incident {incident.id}")
        # In production: integrate with PagerDuty, OpsGenie, etc.
    
    def _create_incident_channel(self, incident: Incident):
        """Create dedicated incident communication channel."""
        logger.info(f"💬 Creating incident channel for {incident.id}")
        # In production: integrate with Slack, Microsoft Teams, etc.
    
    def _update_status_page(self, incident: Incident):
        """Update public status page."""
        logger.info(f"📢 Updating status page for incident {incident.id}")
        # In production: integrate with status page service
        incident.status_page_updated = True
    
    def _setup_incident_monitoring(self, incident: Incident):
        """Set up focused monitoring for incident."""
        logger.info(f"📊 Setting up monitoring for incident {incident.id}")
        # In production: create incident-specific dashboards
    
    def _schedule_escalation(self, incident: Incident):
        """Schedule automatic escalation for critical incidents."""
        logger.info(f"⏰ Scheduling escalation for critical incident {incident.id}")
        # In production: schedule escalation after SLA time
    
    def _is_customer_facing(self, incident: Incident) -> bool:
        """Determine if incident affects customers."""
        customer_facing_services = ["api", "web", "mobile", "transcription"]
        return any(service in customer_facing_services for service in incident.affected_services)
    
    def _schedule_post_incident_review(self, incident: Incident):
        """Schedule post-incident review meeting."""
        logger.info(f"📅 Scheduling post-incident review for {incident.id}")
        # In production: create calendar invite, prepare review agenda
    
    def _generate_incident_report(self, incident: Incident) -> str:
        """Generate detailed incident report."""
        report = f"""
# Incident Report: {incident.id}

## Incident Summary
- **Title**: {incident.title}
- **Severity**: {incident.severity.value.upper()}
- **Status**: {incident.status.value.upper()}
- **Created**: {incident.created_at.isoformat()}
- **Resolved**: {incident.closed_at.isoformat() if incident.closed_at else 'Not resolved'}

## Impact
- **Affected Services**: {', '.join(incident.affected_services)}
- **Customer Impact**: {incident.customer_impact or 'Not specified'}

## Timeline
"""
        
        # Add timeline from updates
        if incident.id in self.incident_updates:
            for update in self.incident_updates[incident.id]:
                report += f"- **{update.timestamp.strftime('%H:%M')}**: {update.message}\n"
        
        report += f"""

## Resolution
- **Root Cause**: {incident.root_cause or 'Not specified'}
- **Resolution**: {incident.resolution or 'Not specified'}

## Metrics
- **Response Time**: {incident.response_time_minutes or 'N/A'} minutes
- **Resolution Time**: {incident.resolution_time_minutes or 'N/A'} minutes

## Lessons Learned
"""
        
        for lesson in incident.lessons_learned:
            report += f"- {lesson}\n"
        
        report += "\n## Follow-up Actions\n"
        for action in incident.follow_up_actions:
            report += f"- {action}\n"
        
        # Save report
        report_file = f"incident_report_{incident.id}.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        logger.info(f"📄 Incident report generated: {report_file}")
        return report_file
    
    def _update_knowledge_base(self, incident: Incident):
        """Update knowledge base with incident learnings."""
        logger.info(f"📚 Updating knowledge base with learnings from {incident.id}")
        # In production: update runbooks, troubleshooting guides
    
    def _finalize_incident(self, incident: Incident):
        """Finalize closed incident."""
        logger.info(f"✅ Finalizing incident {incident.id}")
        # Final cleanup, archival, etc.
    
    def _send_escalation_notification(self, incident: Incident, 
                                    contact: IncidentContact, reason: str):
        """Send escalation notification to contact."""
        logger.info(f"📞 Notifying {contact.name} about escalated incident {incident.id}")
        # In production: send SMS, email, phone call
    
    def get_incident_status(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Get current incident status and timeline."""
        if incident_id not in self.incidents:
            return None
        
        incident = self.incidents[incident_id]
        updates = self.incident_updates.get(incident_id, [])
        
        return {
            "incident": asdict(incident),
            "updates": [asdict(update) for update in updates],
            "sla_compliance": self._get_sla_status(incident)
        }
    
    def _get_sla_status(self, incident: Incident) -> Dict[str, Any]:
        """Get SLA compliance status for incident."""
        targets = self.sla_targets.get(incident.severity, {})
        
        status = {
            "response_target_minutes": targets.get("response"),
            "resolution_target_minutes": targets.get("resolution"),
            "response_actual_minutes": incident.response_time_minutes,
            "resolution_actual_minutes": incident.resolution_time_minutes,
            "response_sla_met": None,
            "resolution_sla_met": None
        }
        
        if incident.response_time_minutes and targets.get("response"):
            status["response_sla_met"] = incident.response_time_minutes <= targets["response"]
        
        if incident.resolution_time_minutes and targets.get("resolution"):
            status["resolution_sla_met"] = incident.resolution_time_minutes <= targets["resolution"]
        
        return status
    
    def get_incident_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get incident metrics for specified period."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_incidents = [
            incident for incident in self.incidents.values()
            if incident.created_at > cutoff_date
        ]
        
        if not recent_incidents:
            return {"error": "No incidents in specified period"}
        
        # Calculate metrics
        total_incidents = len(recent_incidents)
        by_severity = {}
        for severity in IncidentSeverity:
            count = len([i for i in recent_incidents if i.severity == severity])
            by_severity[severity.value] = count
        
        # SLA compliance
        response_sla_breaches = 0
        resolution_sla_breaches = 0
        
        for incident in recent_incidents:
            targets = self.sla_targets.get(incident.severity, {})
            
            if (incident.response_time_minutes and 
                targets.get("response") and 
                incident.response_time_minutes > targets["response"]):
                response_sla_breaches += 1
            
            if (incident.resolution_time_minutes and 
                targets.get("resolution") and 
                incident.resolution_time_minutes > targets["resolution"]):
                resolution_sla_breaches += 1
        
        # Average times
        response_times = [i.response_time_minutes for i in recent_incidents if i.response_time_minutes]
        resolution_times = [i.resolution_time_minutes for i in recent_incidents if i.resolution_time_minutes]
        
        return {
            "period_days": days,
            "total_incidents": total_incidents,
            "incidents_by_severity": by_severity,
            "sla_compliance": {
                "response_sla_breaches": response_sla_breaches,
                "resolution_sla_breaches": resolution_sla_breaches,
                "response_sla_compliance_rate": 1 - (response_sla_breaches / total_incidents) if total_incidents > 0 else 1,
                "resolution_sla_compliance_rate": 1 - (resolution_sla_breaches / total_incidents) if total_incidents > 0 else 1
            },
            "average_times": {
                "response_time_minutes": sum(response_times) / len(response_times) if response_times else 0,
                "resolution_time_minutes": sum(resolution_times) / len(resolution_times) if resolution_times else 0
            }
        }

# Integration with monitoring systems
def create_incident_from_alert(alert_data: Dict[str, Any]) -> Incident:
    """Create incident from monitoring alert."""
    manager = IncidentResponseManager()
    
    # Map alert severity to incident severity
    severity_mapping = {
        "critical": IncidentSeverity.CRITICAL,
        "warning": IncidentSeverity.HIGH,
        "info": IncidentSeverity.MEDIUM
    }
    
    severity = severity_mapping.get(
        alert_data.get("severity", "").lower(),
        IncidentSeverity.MEDIUM
    )
    
    incident = manager.create_incident(
        title=alert_data.get("title", "Monitoring Alert"),
        description=alert_data.get("description", ""),
        severity=severity,
        affected_services=alert_data.get("services", ["unknown"]),
        reporter="monitoring_system"
    )
    
    return incident

if __name__ == "__main__":
    # CLI interface for incident management
    import argparse
    
    parser = argparse.ArgumentParser(description="Incident Response Management")
    parser.add_argument("--create", nargs=4, metavar=("TITLE", "DESC", "SEVERITY", "SERVICES"),
                       help="Create incident")
    parser.add_argument("--update", nargs=3, metavar=("ID", "STATUS", "MESSAGE"),
                       help="Update incident")
    parser.add_argument("--resolve", nargs=3, metavar=("ID", "RESOLUTION", "ROOT_CAUSE"),
                       help="Resolve incident")
    parser.add_argument("--status", type=str, help="Get incident status")
    parser.add_argument("--metrics", type=int, default=30, help="Get metrics for N days")
    
    args = parser.parse_args()
    
    manager = IncidentResponseManager()
    
    if args.create:
        title, desc, severity_str, services_str = args.create
        severity = IncidentSeverity(severity_str.lower())
        services = services_str.split(",")
        
        incident = manager.create_incident(title, desc, severity, services)
        print(f"Created incident: {incident.id}")
    
    elif args.update:
        incident_id, status_str, message = args.update
        status = IncidentStatus(status_str.lower())
        
        success = manager.update_incident(incident_id, status=status, message=message)
        print(f"Update {'successful' if success else 'failed'}")
    
    elif args.resolve:
        incident_id, resolution, root_cause = args.resolve
        
        success = manager.resolve_incident(incident_id, resolution, root_cause)
        print(f"Resolution {'successful' if success else 'failed'}")
    
    elif args.status:
        status = manager.get_incident_status(args.status)
        if status:
            print(json.dumps(status, indent=2, default=str))
        else:
            print("Incident not found")
    
    elif args.metrics:
        metrics = manager.get_incident_metrics(args.metrics)
        print(json.dumps(metrics, indent=2))
    
    else:
        parser.print_help()