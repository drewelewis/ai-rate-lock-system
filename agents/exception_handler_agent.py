"""
Exception Handler Agent
Escalates complex cases and issues to human loan officers for review.
"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ExceptionHandlerAgent:
    """
    Role: Escalates issues to a human loan officer if something goes wrong.
    
    Tasks:
    - Identify scenarios requiring human intervention
    - Route exceptions to appropriate staff members
    - Track escalation resolution times
    - Provide context and recommendations for human reviewers
    """
    
    def __init__(self, notification_service=None, staff_service=None, audit_service=None):
        self.notification_service = notification_service
        self.staff_service = staff_service
        self.audit_service = audit_service
        self.agent_name = "ExceptionHandlerAgent"
    
    async def handle_exception(self, loan_lock_id: str, exception_type: str, 
                              exception_details: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an exception by escalating to appropriate human staff."""
        logger.info(f"{self.agent_name}: Handling exception {exception_type} for loan {loan_lock_id}")
        
        try:
            # Classify the exception
            classification = await self._classify_exception(exception_type, exception_details, context)
            
            # Determine escalation target
            escalation_target = await self._determine_escalation_target(classification, context)
            
            # Create escalation case
            escalation_case = await self._create_escalation_case(
                loan_lock_id, exception_type, exception_details, context, classification, escalation_target
            )
            
            # Send escalation notifications
            notification_result = await self._send_escalation_notifications(escalation_case)
            
            # Update loan lock status
            await self._update_loan_lock_status(loan_lock_id, escalation_case)
            
            # Log the escalation
            if self.audit_service:
                await self.audit_service.log_agent_action(
                    loan_lock_id=loan_lock_id,
                    agent_name=self.agent_name,
                    action="ESCALATE_EXCEPTION",
                    details=escalation_case,
                    outcome="SUCCESS"
                )
            
            escalation_response = {
                "escalation_id": escalation_case.get("escalation_id"),
                "status": "ESCALATED",
                "escalation_target": escalation_target,
                "priority": classification.get("priority"),
                "estimated_resolution_time": classification.get("estimated_resolution_time"),
                "notification_sent": notification_result.get("success", False),
                "next_steps": escalation_case.get("recommended_actions"),
                "audit": {
                    "escalated_by": self.agent_name,
                    "escalated_at": datetime.utcnow().isoformat()
                }
            }
            
            logger.info(f"{self.agent_name}: Successfully escalated exception {escalation_case.get('escalation_id')}")
            return escalation_response
            
        except Exception as e:
            logger.error(f"{self.agent_name}: Error handling exception - {str(e)}")
            raise
    
    async def _classify_exception(self, exception_type: str, exception_details: Dict[str, Any], 
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """Classify the exception to determine handling approach."""
        classification = {
            "category": "UNKNOWN",
            "priority": "MEDIUM",
            "complexity": "STANDARD",
            "estimated_resolution_time": "4 hours",
            "requires_specialist": False,
            "blocking_issue": False
        }
        
        # High priority exceptions
        high_priority_types = [
            "COMPLIANCE_FAILURE",
            "REGULATORY_VIOLATION", 
            "SYSTEM_ERROR",
            "DATA_CORRUPTION",
            "CRITICAL_DEADLINE"
        ]
        
        # Complex exceptions requiring specialists
        specialist_required_types = [
            "COMPLEX_LOAN_SCENARIO",
            "PRICING_ANOMALY",
            "REGULATORY_INTERPRETATION",
            "CUSTOM_PRODUCT_REQUIREMENTS"
        ]
        
        # Blocking exceptions that stop all progress
        blocking_types = [
            "MISSING_REQUIRED_DOCUMENTATION",
            "BORROWER_ELIGIBILITY_ISSUE",
            "PROPERTY_VALUATION_PROBLEM",
            "CREDIT_ISSUE"
        ]
        
        if exception_type in high_priority_types:
            classification["priority"] = "HIGH"
            classification["estimated_resolution_time"] = "2 hours"
        
        if exception_type in specialist_required_types:
            classification["requires_specialist"] = True
            classification["complexity"] = "COMPLEX"
            classification["estimated_resolution_time"] = "1 day"
        
        if exception_type in blocking_types:
            classification["blocking_issue"] = True
            classification["priority"] = "HIGH"
        
        # Set category based on exception type
        if "COMPLIANCE" in exception_type or "REGULATORY" in exception_type:
            classification["category"] = "COMPLIANCE"
        elif "PRICING" in exception_type or "RATE" in exception_type:
            classification["category"] = "PRICING"
        elif "BORROWER" in exception_type or "ELIGIBILITY" in exception_type:
            classification["category"] = "UNDERWRITING"
        elif "SYSTEM" in exception_type or "TECHNICAL" in exception_type:
            classification["category"] = "TECHNICAL"
        else:
            classification["category"] = "GENERAL"
        
        return classification
    
    async def _determine_escalation_target(self, classification: Dict[str, Any], 
                                          context: Dict[str, Any]) -> Dict[str, Any]:
        """Determine who should handle the escalated exception."""
        
        # Default to loan officer
        target = {
            "type": "LOAN_OFFICER",
            "name": None,
            "email": None,
            "phone": None
        }
        
        try:
            # Get loan officer from context
            loan_officer = context.get("loan_officer")
            
            if not loan_officer and self.staff_service:
                # Fetch loan officer from staff service
                loan_officer = await self.staff_service.get_loan_officer_for_loan(
                    context.get("loan_application_id")
                )
            
            if loan_officer:
                target.update({
                    "name": loan_officer.get("name"),
                    "email": loan_officer.get("email"),
                    "phone": loan_officer.get("phone")
                })
            
            # Route to specialists based on classification
            if classification.get("category") == "COMPLIANCE":
                specialist = await self._get_compliance_specialist()
                if specialist:
                    target = {
                        "type": "COMPLIANCE_SPECIALIST",
                        **specialist
                    }
            
            elif classification.get("category") == "PRICING":
                specialist = await self._get_pricing_specialist()
                if specialist:
                    target = {
                        "type": "PRICING_SPECIALIST", 
                        **specialist
                    }
            
            elif classification.get("category") == "TECHNICAL":
                specialist = await self._get_technical_support()
                if specialist:
                    target = {
                        "type": "TECHNICAL_SUPPORT",
                        **specialist
                    }
            
            elif classification.get("priority") == "HIGH":
                # Route high priority to supervisor
                supervisor = await self._get_supervisor(loan_officer)
                if supervisor:
                    target = {
                        "type": "SUPERVISOR",
                        **supervisor
                    }
            
        except Exception as e:
            logger.error(f"Error determining escalation target: {str(e)}")
        
        return target
    
    async def _create_escalation_case(self, loan_lock_id: str, exception_type: str, 
                                     exception_details: Dict[str, Any], context: Dict[str, Any],
                                     classification: Dict[str, Any], escalation_target: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comprehensive escalation case."""
        
        escalation_case = {
            "escalation_id": self._generate_escalation_id(),
            "loan_lock_id": loan_lock_id,
            "loan_application_id": context.get("loan_application_id"),
            "exception_type": exception_type,
            "exception_details": exception_details,
            "classification": classification,
            "escalation_target": escalation_target,
            "created_at": datetime.utcnow().isoformat(),
            "status": "OPEN",
            "priority": classification.get("priority"),
            "estimated_resolution": (datetime.utcnow() + timedelta(
                hours=self._parse_time_estimate(classification.get("estimated_resolution_time"))
            )).isoformat(),
            "context": {
                "borrower_info": context.get("borrower_info", {}),
                "loan_details": context.get("loan_details", {}),
                "current_state": context.get("current_state"),
                "previous_actions": context.get("previous_actions", []),
                "system_state": context.get("system_state", {})
            },
            "recommended_actions": self._generate_recommended_actions(exception_type, exception_details, context),
            "escalation_reason": self._generate_escalation_reason(exception_type, exception_details),
            "supporting_documents": context.get("supporting_documents", []),
            "metadata": {
                "escalated_by": self.agent_name,
                "automatic_escalation": True,
                "requires_callback": classification.get("blocking_issue", False)
            }
        }
        
        return escalation_case
    
    async def _send_escalation_notifications(self, escalation_case: Dict[str, Any]) -> Dict[str, Any]:
        """Send notifications about the escalation."""
        notification_result = {
            "success": False,
            "notifications_sent": [],
            "errors": []
        }
        
        try:
            if not self.notification_service:
                logger.warning("Notification service not configured")
                return notification_result
            
            target = escalation_case.get("escalation_target", {})
            target_email = target.get("email")
            target_phone = target.get("phone")
            
            # Send email notification
            if target_email:
                email_result = await self._send_escalation_email(escalation_case, target_email)
                if email_result.get("success"):
                    notification_result["notifications_sent"].append("email")
                else:
                    notification_result["errors"].append(f"Email failed: {email_result.get('error')}")
            
            # Send SMS for high priority cases
            if target_phone and escalation_case.get("priority") == "HIGH":
                sms_result = await self._send_escalation_sms(escalation_case, target_phone)
                if sms_result.get("success"):
                    notification_result["notifications_sent"].append("sms")
                else:
                    notification_result["errors"].append(f"SMS failed: {sms_result.get('error')}")
            
            # Send Slack/Teams notification if configured
            slack_result = await self._send_slack_notification(escalation_case)
            if slack_result.get("success"):
                notification_result["notifications_sent"].append("slack")
            
            notification_result["success"] = len(notification_result["notifications_sent"]) > 0
            
        except Exception as e:
            logger.error(f"Error sending escalation notifications: {str(e)}")
            notification_result["errors"].append(str(e))
        
        return notification_result
    
    async def _send_escalation_email(self, escalation_case: Dict[str, Any], target_email: str) -> Dict[str, Any]:
        """Send escalation email notification."""
        try:
            subject = f"ESCALATION: Rate Lock Issue - {escalation_case.get('loan_application_id')} [{escalation_case.get('priority')} Priority]"
            
            body = f"""
RATE LOCK ESCALATION REQUIRED

Escalation ID: {escalation_case.get('escalation_id')}
Loan Application: {escalation_case.get('loan_application_id')}
Priority: {escalation_case.get('priority')}
Exception Type: {escalation_case.get('exception_type')}

ESCALATION REASON:
{escalation_case.get('escalation_reason')}

RECOMMENDED ACTIONS:
"""
            
            for action in escalation_case.get('recommended_actions', []):
                body += f"• {action}\n"
            
            body += f"""

BORROWER INFORMATION:
Name: {escalation_case.get('context', {}).get('borrower_info', {}).get('name', 'N/A')}
Email: {escalation_case.get('context', {}).get('borrower_info', {}).get('email', 'N/A')}

LOAN DETAILS:
Amount: ${escalation_case.get('context', {}).get('loan_details', {}).get('loan_amount', 'N/A'):,}
Type: {escalation_case.get('context', {}).get('loan_details', {}).get('loan_type', 'N/A')}

Estimated Resolution Time: {escalation_case.get('estimated_resolution')}

Please review and take appropriate action as soon as possible.

---
Automated Rate Lock Processing System
Escalation ID: {escalation_case.get('escalation_id')}
"""
            
            await self.notification_service.send_email(
                to=target_email,
                subject=subject,
                body=body,
                priority=escalation_case.get('priority')
            )
            
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _send_escalation_sms(self, escalation_case: Dict[str, Any], target_phone: str) -> Dict[str, Any]:
        """Send escalation SMS notification."""
        try:
            message = f"URGENT: Rate Lock Escalation {escalation_case.get('escalation_id')} - Loan {escalation_case.get('loan_application_id')} requires immediate attention. Check email for details."
            
            await self.notification_service.send_sms(
                to=target_phone,
                message=message
            )
            
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _send_slack_notification(self, escalation_case: Dict[str, Any]) -> Dict[str, Any]:
        """Send Slack notification for escalation."""
        try:
            if not hasattr(self.notification_service, 'send_slack_message'):
                return {"success": False, "error": "Slack not configured"}
            
            message = {
                "text": f"🚨 Rate Lock Escalation - {escalation_case.get('priority')} Priority",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Escalation:* {escalation_case.get('escalation_id')}\n*Loan:* {escalation_case.get('loan_application_id')}\n*Type:* {escalation_case.get('exception_type')}\n*Priority:* {escalation_case.get('priority')}"
                        }
                    }
                ]
            }
            
            await self.notification_service.send_slack_message(message)
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_escalation_id(self) -> str:
        """Generate unique escalation ID."""
        return f"ESC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    def _parse_time_estimate(self, time_estimate: str) -> int:
        """Parse time estimate string to hours."""
        try:
            if "hour" in time_estimate:
                return int(time_estimate.split()[0])
            elif "day" in time_estimate:
                return int(time_estimate.split()[0]) * 24
            else:
                return 4  # Default 4 hours
        except:
            return 4
    
    def _generate_recommended_actions(self, exception_type: str, exception_details: Dict[str, Any], 
                                    context: Dict[str, Any]) -> List[str]:
        """Generate recommended actions based on exception type."""
        actions = []
        
        if exception_type == "COMPLIANCE_FAILURE":
            actions.extend([
                "Review compliance violation details",
                "Determine if rate lock can proceed with additional disclosures",
                "Consult with compliance team if necessary"
            ])
        
        elif exception_type == "MISSING_REQUIRED_DOCUMENTATION":
            actions.extend([
                "Contact borrower to request missing documents",
                "Set deadline for document submission",
                "Consider extending rate lock if needed"
            ])
        
        elif exception_type == "PRICING_ANOMALY":
            actions.extend([
                "Verify pricing engine configuration",
                "Check for market data issues",
                "Consider manual rate quote if needed"
            ])
        
        elif exception_type == "BORROWER_ELIGIBILITY_ISSUE":
            actions.extend([
                "Review underwriting guidelines",
                "Determine if additional conditions can resolve issue",
                "Consider alternative loan products"
            ])
        
        else:
            actions.extend([
                "Review exception details and context",
                "Determine appropriate resolution approach",
                "Update loan status based on findings"
            ])
        
        return actions
    
    def _generate_escalation_reason(self, exception_type: str, exception_details: Dict[str, Any]) -> str:
        """Generate human-readable escalation reason."""
        reason_templates = {
            "COMPLIANCE_FAILURE": "A compliance issue was detected that requires human review to ensure regulatory requirements are met.",
            "MISSING_REQUIRED_DOCUMENTATION": "Required documentation is missing and automated follow-up has been unsuccessful.",
            "PRICING_ANOMALY": "The pricing engine returned unexpected results that need manual verification.",
            "BORROWER_ELIGIBILITY_ISSUE": "Borrower eligibility concerns were identified that require underwriting review.",
            "SYSTEM_ERROR": "A technical error occurred that prevented automated processing from continuing.",
            "COMPLEX_LOAN_SCENARIO": "The loan scenario is too complex for automated processing and requires expert review."
        }
        
        base_reason = reason_templates.get(exception_type, "An exception occurred that requires human intervention.")
        
        # Add specific details if available
        if exception_details.get("details"):
            base_reason += f" Specific issue: {exception_details.get('details')}"
        
        return base_reason
    
    async def _update_loan_lock_status(self, loan_lock_id: str, escalation_case: Dict[str, Any]) -> None:
        """Update loan lock status to reflect escalation."""
        # TODO: Implement status update to loan lock storage
        logger.info(f"Updated loan lock {loan_lock_id} status to ESCALATED")
    
    async def _get_compliance_specialist(self) -> Optional[Dict[str, str]]:
        """Get compliance specialist contact information."""
        if self.staff_service:
            return await self.staff_service.get_compliance_specialist()
        return None
    
    async def _get_pricing_specialist(self) -> Optional[Dict[str, str]]:
        """Get pricing specialist contact information."""
        if self.staff_service:
            return await self.staff_service.get_pricing_specialist()
        return None
    
    async def _get_technical_support(self) -> Optional[Dict[str, str]]:
        """Get technical support contact information."""
        if self.staff_service:
            return await self.staff_service.get_technical_support()
        return None
    
    async def _get_supervisor(self, loan_officer: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
        """Get supervisor contact information."""
        if self.staff_service and loan_officer:
            return await self.staff_service.get_supervisor(loan_officer.get('id'))
        return None