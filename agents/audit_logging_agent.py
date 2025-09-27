"""
Audit & Logging Agent
Maintains comprehensive audit trail for compliance and traceability.
"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

class AuditLoggingAgent:
    """
    Role: Maintains a record of all actions for compliance and traceability.
    
    Tasks:
    - Log timestamps, agent actions, and decisions
    - Store audit trail in a secure, queryable format
    - Generate compliance reports
    - Track SLA performance and metrics
    """
    
    def __init__(self, storage_service=None, metrics_service=None):
        self.storage_service = storage_service
        self.metrics_service = metrics_service
        self.agent_name = "AuditLoggingAgent"
    
    async def log_agent_action(self, loan_lock_id: str, agent_name: str, action: str, 
                              details: Dict[str, Any], outcome: str, duration_ms: Optional[int] = None) -> str:
        """Log an individual agent action with full context."""
        try:
            audit_entry = {
                "audit_id": self._generate_audit_id(),
                "loan_lock_id": loan_lock_id,
                "timestamp": datetime.utcnow().isoformat(),
                "agent_name": agent_name,
                "action": action,
                "details": details,
                "outcome": outcome,  # SUCCESS, FAILURE, WARNING, PARTIAL
                "duration_ms": duration_ms,
                "metadata": {
                    "logged_by": self.agent_name,
                    "log_level": self._determine_log_level(outcome),
                    "session_id": details.get('session_id'),
                    "correlation_id": details.get('correlation_id')
                }
            }
            
            # Store audit entry
            await self._store_audit_entry(audit_entry)
            
            # Update metrics if service available
            if self.metrics_service:
                await self._update_metrics(audit_entry)
            
            logger.info(f"{self.agent_name}: Logged action {action} by {agent_name} with outcome {outcome}")
            return audit_entry["audit_id"]
            
        except Exception as e:
            logger.error(f"{self.agent_name}: Error logging agent action - {str(e)}")
            # Fallback to basic logging
            logger.info(f"AUDIT: {agent_name} - {action} - {outcome}")
            return ""
    
    async def log_state_transition(self, loan_lock_id: str, from_state: str, to_state: str, 
                                  triggered_by: str, context: Dict[str, Any]) -> str:
        """Log loan lock state transitions."""
        try:
            transition_entry = {
                "audit_id": self._generate_audit_id(),
                "entry_type": "STATE_TRANSITION",
                "loan_lock_id": loan_lock_id,
                "timestamp": datetime.utcnow().isoformat(),
                "from_state": from_state,
                "to_state": to_state,
                "triggered_by": triggered_by,
                "context": context,
                "metadata": {
                    "logged_by": self.agent_name,
                    "transition_duration": context.get('state_duration_ms'),
                    "auto_triggered": context.get('auto_triggered', True)
                }
            }
            
            await self._store_audit_entry(transition_entry)
            
            # Track state timing metrics
            if self.metrics_service:
                await self._track_state_metrics(transition_entry)
            
            logger.info(f"{self.agent_name}: Logged state transition {from_state} -> {to_state}")
            return transition_entry["audit_id"]
            
        except Exception as e:
            logger.error(f"{self.agent_name}: Error logging state transition - {str(e)}")
            return ""
    
    async def log_error_event(self, loan_lock_id: str, error_source: str, error_type: str, 
                             error_message: str, error_context: Dict[str, Any]) -> str:
        """Log error events for troubleshooting and monitoring."""
        try:
            error_entry = {
                "audit_id": self._generate_audit_id(),
                "entry_type": "ERROR_EVENT",
                "loan_lock_id": loan_lock_id,
                "timestamp": datetime.utcnow().isoformat(),
                "error_source": error_source,
                "error_type": error_type,
                "error_message": error_message,
                "error_context": error_context,
                "severity": self._determine_error_severity(error_type),
                "metadata": {
                    "logged_by": self.agent_name,
                    "requires_human_attention": self._requires_human_attention(error_type),
                    "auto_retry_attempted": error_context.get('retry_attempted', False)
                }
            }
            
            await self._store_audit_entry(error_entry)
            
            # Alert on critical errors
            if error_entry["severity"] == "CRITICAL":
                await self._send_error_alert(error_entry)
            
            logger.error(f"{self.agent_name}: Logged error event - {error_type}: {error_message}")
            return error_entry["audit_id"]
            
        except Exception as e:
            logger.error(f"{self.agent_name}: Error logging error event - {str(e)}")
            return ""
    
    async def log_compliance_check(self, loan_lock_id: str, check_type: str, check_result: str, 
                                  check_details: Dict[str, Any]) -> str:
        """Log compliance check results."""
        try:
            compliance_entry = {
                "audit_id": self._generate_audit_id(),
                "entry_type": "COMPLIANCE_CHECK",
                "loan_lock_id": loan_lock_id,
                "timestamp": datetime.utcnow().isoformat(),
                "check_type": check_type,
                "check_result": check_result,  # PASS, FAIL, WARNING
                "check_details": check_details,
                "regulatory_impact": self._assess_regulatory_impact(check_type, check_result),
                "metadata": {
                    "logged_by": self.agent_name,
                    "requires_disclosure": check_details.get('requires_disclosure', False),
                    "blocking_issue": check_result == "FAIL"
                }
            }
            
            await self._store_audit_entry(compliance_entry)
            
            logger.info(f"{self.agent_name}: Logged compliance check {check_type} with result {check_result}")
            return compliance_entry["audit_id"]
            
        except Exception as e:
            logger.error(f"{self.agent_name}: Error logging compliance check - {str(e)}")
            return ""
    
    async def generate_audit_trail(self, loan_lock_id: str, start_date: Optional[str] = None, 
                                  end_date: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive audit trail for a loan lock."""
        try:
            # Fetch all audit entries for the loan lock
            audit_entries = await self._fetch_audit_entries(loan_lock_id, start_date, end_date)
            
            # Organize entries by type
            organized_entries = self._organize_audit_entries(audit_entries)
            
            # Generate summary statistics
            audit_summary = self._generate_audit_summary(audit_entries)
            
            # Build audit trail report
            audit_trail = {
                "loan_lock_id": loan_lock_id,
                "generated_at": datetime.utcnow().isoformat(),
                "generated_by": self.agent_name,
                "period": {
                    "start_date": start_date or audit_entries[0]["timestamp"] if audit_entries else None,
                    "end_date": end_date or audit_entries[-1]["timestamp"] if audit_entries else None
                },
                "summary": audit_summary,
                "entries": organized_entries,
                "total_entries": len(audit_entries),
                "compliance_status": self._assess_overall_compliance(audit_entries)
            }
            
            logger.info(f"{self.agent_name}: Generated audit trail with {len(audit_entries)} entries")
            return audit_trail
            
        except Exception as e:
            logger.error(f"{self.agent_name}: Error generating audit trail - {str(e)}")
            raise
    
    async def track_sla_performance(self, loan_lock_id: str, sla_metric: str, 
                                   actual_duration: int, target_duration: int) -> None:
        """Track SLA performance metrics."""
        try:
            sla_entry = {
                "audit_id": self._generate_audit_id(),
                "entry_type": "SLA_METRIC",
                "loan_lock_id": loan_lock_id,
                "timestamp": datetime.utcnow().isoformat(),
                "sla_metric": sla_metric,
                "actual_duration": actual_duration,
                "target_duration": target_duration,
                "sla_met": actual_duration <= target_duration,
                "variance_percent": ((actual_duration - target_duration) / target_duration) * 100,
                "metadata": {
                    "logged_by": self.agent_name,
                    "measurement_unit": "minutes"
                }
            }
            
            await self._store_audit_entry(sla_entry)
            
            # Update SLA metrics dashboard
            if self.metrics_service:
                await self._update_sla_metrics(sla_entry)
            
            logger.info(f"{self.agent_name}: Tracked SLA metric {sla_metric} - Met: {sla_entry['sla_met']}")
            
        except Exception as e:
            logger.error(f"{self.agent_name}: Error tracking SLA performance - {str(e)}")
    
    def _generate_audit_id(self) -> str:
        """Generate unique audit entry ID."""
        return f"AUDIT-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
    
    def _determine_log_level(self, outcome: str) -> str:
        """Determine appropriate log level based on outcome."""
        level_mapping = {
            "SUCCESS": "INFO",
            "FAILURE": "ERROR",
            "WARNING": "WARNING",
            "PARTIAL": "WARNING"
        }
        return level_mapping.get(outcome, "INFO")
    
    def _determine_error_severity(self, error_type: str) -> str:
        """Determine error severity level."""
        critical_errors = ["COMPLIANCE_FAILURE", "PRICING_ENGINE_DOWN", "DATA_CORRUPTION"]
        warning_errors = ["TIMEOUT", "RETRY_EXHAUSTED", "VALIDATION_WARNING"]
        
        if error_type in critical_errors:
            return "CRITICAL"
        elif error_type in warning_errors:
            return "WARNING"
        else:
            return "MINOR"
    
    def _requires_human_attention(self, error_type: str) -> bool:
        """Determine if error requires human attention."""
        human_attention_required = [
            "COMPLIANCE_FAILURE", 
            "MANUAL_REVIEW_NEEDED", 
            "BORROWER_DISPUTE",
            "COMPLEX_SCENARIO"
        ]
        return error_type in human_attention_required
    
    def _assess_regulatory_impact(self, check_type: str, check_result: str) -> str:
        """Assess regulatory impact of compliance check."""
        if check_result == "FAIL":
            high_impact_checks = ["TRID_COMPLIANCE", "DISCLOSURE_TIMING", "RATE_LOCK_DISCLOSURE"]
            if check_type in high_impact_checks:
                return "HIGH"
            else:
                return "MEDIUM"
        elif check_result == "WARNING":
            return "LOW"
        else:
            return "NONE"
    
    async def _store_audit_entry(self, audit_entry: Dict[str, Any]) -> bool:
        """Store audit entry in persistent storage."""
        try:
            if self.storage_service:
                success = await self.storage_service.store_audit_entry(audit_entry)
                return success
            else:
                # Fallback to file logging
                logger.info(f"AUDIT_ENTRY: {json.dumps(audit_entry)}")
                return True
                
        except Exception as e:
            logger.error(f"Error storing audit entry: {str(e)}")
            return False
    
    async def _fetch_audit_entries(self, loan_lock_id: str, start_date: Optional[str], 
                                  end_date: Optional[str]) -> List[Dict[str, Any]]:
        """Fetch audit entries from storage."""
        try:
            if self.storage_service:
                entries = await self.storage_service.fetch_audit_entries(
                    loan_lock_id, start_date, end_date
                )
                return entries
            else:
                logger.warning("Storage service not configured - returning empty audit trail")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching audit entries: {str(e)}")
            return []
    
    def _organize_audit_entries(self, entries: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Organize audit entries by type."""
        organized = {
            "agent_actions": [],
            "state_transitions": [],
            "error_events": [],
            "compliance_checks": [],
            "sla_metrics": []
        }
        
        for entry in entries:
            entry_type = entry.get("entry_type", "agent_actions")
            
            if entry_type == "STATE_TRANSITION":
                organized["state_transitions"].append(entry)
            elif entry_type == "ERROR_EVENT":
                organized["error_events"].append(entry)
            elif entry_type == "COMPLIANCE_CHECK":
                organized["compliance_checks"].append(entry)
            elif entry_type == "SLA_METRIC":
                organized["sla_metrics"].append(entry)
            else:
                organized["agent_actions"].append(entry)
        
        return organized
    
    def _generate_audit_summary(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics from audit entries."""
        total_entries = len(entries)
        
        if total_entries == 0:
            return {"total_entries": 0}
        
        # Count entries by type
        entry_types = {}
        outcomes = {}
        agents = {}
        
        for entry in entries:
            # Count entry types
            entry_type = entry.get("entry_type", "agent_action")
            entry_types[entry_type] = entry_types.get(entry_type, 0) + 1
            
            # Count outcomes
            outcome = entry.get("outcome", "unknown")
            outcomes[outcome] = outcomes.get(outcome, 0) + 1
            
            # Count agents
            agent_name = entry.get("agent_name", "unknown")
            agents[agent_name] = agents.get(agent_name, 0) + 1
        
        return {
            "total_entries": total_entries,
            "entry_types": entry_types,
            "outcomes": outcomes,
            "agents": agents,
            "time_span": self._calculate_time_span(entries)
        }
    
    def _calculate_time_span(self, entries: List[Dict[str, Any]]) -> Dict[str, str]:
        """Calculate time span of audit entries."""
        if not entries:
            return {}
        
        timestamps = [entry["timestamp"] for entry in entries if "timestamp" in entry]
        
        if timestamps:
            return {
                "start": min(timestamps),
                "end": max(timestamps)
            }
        
        return {}
    
    def _assess_overall_compliance(self, entries: List[Dict[str, Any]]) -> str:
        """Assess overall compliance status from audit entries."""
        compliance_entries = [e for e in entries if e.get("entry_type") == "COMPLIANCE_CHECK"]
        
        if not compliance_entries:
            return "NO_CHECKS_PERFORMED"
        
        # Check for any failed compliance checks
        failed_checks = [e for e in compliance_entries if e.get("check_result") == "FAIL"]
        if failed_checks:
            return "NON_COMPLIANT"
        
        # Check for warnings
        warning_checks = [e for e in compliance_entries if e.get("check_result") == "WARNING"]
        if warning_checks:
            return "COMPLIANT_WITH_WARNINGS"
        
        return "FULLY_COMPLIANT"
    
    async def _update_metrics(self, audit_entry: Dict[str, Any]) -> None:
        """Update performance metrics."""
        if not self.metrics_service:
            return
        
        try:
            await self.metrics_service.record_agent_action(
                agent_name=audit_entry.get("agent_name"),
                action=audit_entry.get("action"),
                outcome=audit_entry.get("outcome"),
                duration_ms=audit_entry.get("duration_ms")
            )
        except Exception as e:
            logger.error(f"Error updating metrics: {str(e)}")
    
    async def _track_state_metrics(self, transition_entry: Dict[str, Any]) -> None:
        """Track state transition metrics."""
        if not self.metrics_service:
            return
        
        try:
            await self.metrics_service.record_state_transition(
                from_state=transition_entry.get("from_state"),
                to_state=transition_entry.get("to_state"),
                duration_ms=transition_entry.get("context", {}).get("state_duration_ms")
            )
        except Exception as e:
            logger.error(f"Error tracking state metrics: {str(e)}")
    
    async def _update_sla_metrics(self, sla_entry: Dict[str, Any]) -> None:
        """Update SLA performance metrics."""
        if not self.metrics_service:
            return
        
        try:
            await self.metrics_service.record_sla_performance(
                metric=sla_entry.get("sla_metric"),
                actual=sla_entry.get("actual_duration"),
                target=sla_entry.get("target_duration"),
                met=sla_entry.get("sla_met")
            )
        except Exception as e:
            logger.error(f"Error updating SLA metrics: {str(e)}")
    
    async def _send_error_alert(self, error_entry: Dict[str, Any]) -> None:
        """Send alert for critical errors."""
        # TODO: Implement alerting mechanism (email, Slack, Teams, etc.)
        logger.critical(f"CRITICAL ERROR ALERT: {error_entry.get('error_message')}")
        pass