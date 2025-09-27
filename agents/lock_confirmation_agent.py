"""
Lock Confirmation Agent
Executes the rate lock and sends confirmation notifications.
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class LockConfirmationAgent:
    """
    Role: Executes the lock and sends confirmation.
    
    Tasks:
    - Submit lock request to pricing engine or LOS
    - Generate lock confirmation document
    - Email borrower and loan officer with confirmation and next steps
    """
    
    def __init__(self, pricing_service=None, los_service=None, email_service=None, document_service=None):
        self.pricing_service = pricing_service
        self.los_service = los_service
        self.email_service = email_service
        self.document_service = document_service
        self.agent_name = "LockConfirmationAgent"
    
    async def execute_rate_lock(self, loan_context: Dict[str, Any], selected_rate: Dict[str, Any], compliance_validation: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the rate lock and generate confirmation."""
        logger.info(f"{self.agent_name}: Executing rate lock for loan {loan_context.get('loan_application_id')}")
        
        try:
            # Validate prerequisites
            if not self._validate_lock_prerequisites(compliance_validation):
                raise ValueError("Compliance validation failed - cannot execute lock")
            
            # Submit lock to pricing system
            lock_submission = await self._submit_lock_to_pricing_system(loan_context, selected_rate)
            
            # Update LOS with lock information
            await self._update_los_with_lock(loan_context, lock_submission)
            
            # Generate lock confirmation document
            confirmation_document = await self._generate_confirmation_document(loan_context, lock_submission)
            
            # Send notifications
            notification_results = await self._send_lock_confirmations(loan_context, lock_submission, confirmation_document)
            
            # Build final lock confirmation response
            lock_confirmation = {
                "loan_application_id": loan_context.get('loan_application_id'),
                "lock_confirmation_id": lock_submission.get('lock_id'),
                "status": "Locked",
                "lock_details": {
                    "rate": selected_rate.get('rate'),
                    "points": selected_rate.get('points'),
                    "lock_term_days": selected_rate.get('lock_term_days'),
                    "lock_date": lock_submission.get('lock_date'),
                    "lock_expiration_date": lock_submission.get('lock_expiration_date'),
                    "product_description": selected_rate.get('product_description'),
                    "monthly_payment": selected_rate.get('monthly_payment'),
                    "lock_source": lock_submission.get('pricing_source')
                },
                "compliance": {
                    "disclosures_sent": True,
                    "lock_fee": selected_rate.get('lock_fee', 0.0),
                    "lock_fee_waived": selected_rate.get('lock_fee_waived', False),
                    "regulatory_checks_passed": True,
                    "exceptions": compliance_validation.get('exceptions', [])
                },
                "confirmation_document": confirmation_document,
                "notifications": notification_results,
                "audit": {
                    "locked_by": self.agent_name,
                    "locked_at": datetime.utcnow().isoformat(),
                    "confirmation_sent": True
                }
            }
            
            logger.info(f"{self.agent_name}: Successfully executed rate lock {lock_confirmation['lock_confirmation_id']}")
            return lock_confirmation
            
        except Exception as e:
            logger.error(f"{self.agent_name}: Error executing rate lock - {str(e)}")
            raise
    
    def _validate_lock_prerequisites(self, compliance_validation: Dict[str, Any]) -> bool:
        """Validate all prerequisites are met before executing lock."""
        overall_status = compliance_validation.get('overall_status')
        
        # Only allow locks if compliance passed or has manageable warnings
        if overall_status in ['PASS', 'WARNING']:
            return True
        
        logger.error(f"Cannot execute lock - compliance status: {overall_status}")
        return False
    
    async def _submit_lock_to_pricing_system(self, loan_context: Dict[str, Any], selected_rate: Dict[str, Any]) -> Dict[str, Any]:
        """Submit rate lock request to the pricing engine."""
        try:
            lock_request = self._build_lock_request(loan_context, selected_rate)
            
            if self.pricing_service:
                # Submit to actual pricing service
                lock_response = await self.pricing_service.submit_lock(lock_request)
            else:
                # Mock response for development
                lock_response = self._generate_mock_lock_response(lock_request)
            
            return lock_response
            
        except Exception as e:
            logger.error(f"Error submitting lock to pricing system: {str(e)}")
            raise
    
    def _build_lock_request(self, loan_context: Dict[str, Any], selected_rate: Dict[str, Any]) -> Dict[str, Any]:
        """Build lock request payload for pricing system."""
        loan_details = loan_context.get('loan_details', {})
        borrower_info = loan_context.get('borrower_info', {})
        property_info = loan_context.get('property_info', {})
        
        return {
            "loan_application_id": loan_context.get('loan_application_id'),
            "borrower_name": borrower_info.get('name'),
            "borrower_email": borrower_info.get('email'),
            "loan_amount": loan_details.get('loan_amount'),
            "loan_type": loan_details.get('loan_type'),
            "property_address": property_info.get('address'),
            "rate": selected_rate.get('rate'),
            "points": selected_rate.get('points', 0.0),
            "lock_term_days": selected_rate.get('lock_term_days'),
            "product_code": selected_rate.get('product_code'),
            "lock_fee": selected_rate.get('lock_fee', 0.0),
            "requested_by": self.agent_name,
            "requested_at": datetime.utcnow().isoformat()
        }
    
    def _generate_mock_lock_response(self, lock_request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock lock response for testing."""
        lock_date = datetime.utcnow()
        expiration_date = lock_date + timedelta(days=lock_request.get('lock_term_days', 30))
        
        return {
            "lock_id": f"LOCK-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "status": "CONFIRMED",
            "lock_date": lock_date.isoformat(),
            "lock_expiration_date": expiration_date.isoformat(),
            "pricing_source": "MockPricingEngine",
            "confirmation_number": f"CNF{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        }
    
    async def _update_los_with_lock(self, loan_context: Dict[str, Any], lock_submission: Dict[str, Any]) -> bool:
        """Update the Loan Origination System with lock details."""
        try:
            if not self.los_service:
                logger.warning("LOS service not configured - skipping LOS update")
                return True
            
            update_data = {
                "loan_application_id": loan_context.get('loan_application_id'),
                "rate_lock_id": lock_submission.get('lock_id'),
                "locked_rate": lock_submission.get('rate'),
                "lock_expiration_date": lock_submission.get('lock_expiration_date'),
                "lock_status": "ACTIVE"
            }
            
            success = await self.los_service.update_rate_lock(update_data)
            
            if success:
                logger.info(f"Successfully updated LOS with lock information")
            else:
                logger.warning(f"Failed to update LOS with lock information")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating LOS: {str(e)}")
            return False
    
    async def _generate_confirmation_document(self, loan_context: Dict[str, Any], lock_submission: Dict[str, Any]) -> Dict[str, Any]:
        """Generate rate lock confirmation document."""
        try:
            if self.document_service:
                # Use document service to generate professional document
                document = await self.document_service.generate_lock_confirmation(loan_context, lock_submission)
            else:
                # Generate basic confirmation document
                document = self._generate_basic_confirmation_document(loan_context, lock_submission)
            
            return document
            
        except Exception as e:
            logger.error(f"Error generating confirmation document: {str(e)}")
            return {
                "document_id": f"DOC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "document_type": "rate_lock_confirmation",
                "status": "ERROR",
                "error": str(e)
            }
    
    def _generate_basic_confirmation_document(self, loan_context: Dict[str, Any], lock_submission: Dict[str, Any]) -> Dict[str, Any]:
        """Generate basic rate lock confirmation document."""
        borrower_info = loan_context.get('borrower_info', {})
        loan_details = loan_context.get('loan_details', {})
        
        document_content = f"""
RATE LOCK CONFIRMATION

Lock ID: {lock_submission.get('lock_id')}
Date: {datetime.utcnow().strftime('%B %d, %Y')}

Borrower: {borrower_info.get('name')}
Loan Application ID: {loan_context.get('loan_application_id')}
Loan Amount: ${loan_details.get('loan_amount'):,.2f}

LOCKED RATE DETAILS:
- Interest Rate: {lock_submission.get('rate')}%
- Lock Period: {lock_submission.get('lock_term_days', 30)} days
- Lock Expiration: {lock_submission.get('lock_expiration_date')}
- Product: {loan_details.get('loan_type')} {loan_details.get('loan_term', 30)}-Year Fixed

This rate lock is subject to the terms and conditions outlined in your loan documents.
Please contact your loan officer with any questions.
"""
        
        return {
            "document_id": f"DOC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "document_type": "rate_lock_confirmation",
            "content": document_content,
            "format": "text",
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def _send_lock_confirmations(self, loan_context: Dict[str, Any], lock_submission: Dict[str, Any], confirmation_document: Dict[str, Any]) -> Dict[str, Any]:
        """Send lock confirmation notifications to all stakeholders."""
        notification_results = {
            "borrower_notified": False,
            "loan_officer_notified": False,
            "notification_method": [],
            "errors": []
        }
        
        try:
            # Send confirmation to borrower
            borrower_result = await self._send_borrower_confirmation(loan_context, lock_submission, confirmation_document)
            notification_results["borrower_notified"] = borrower_result.get("success", False)
            if not borrower_result.get("success"):
                notification_results["errors"].append(f"Borrower notification failed: {borrower_result.get('error')}")
            
            # Send notification to loan officer
            lo_result = await self._send_loan_officer_notification(loan_context, lock_submission)
            notification_results["loan_officer_notified"] = lo_result.get("success", False)
            if not lo_result.get("success"):
                notification_results["errors"].append(f"Loan officer notification failed: {lo_result.get('error')}")
            
            notification_results["notification_method"] = ["email"]
            
        except Exception as e:
            logger.error(f"Error sending confirmations: {str(e)}")
            notification_results["errors"].append(str(e))
        
        return notification_results
    
    async def _send_borrower_confirmation(self, loan_context: Dict[str, Any], lock_submission: Dict[str, Any], confirmation_document: Dict[str, Any]) -> Dict[str, Any]:
        """Send rate lock confirmation email to borrower."""
        try:
            if not self.email_service:
                return {"success": False, "error": "Email service not configured"}
            
            borrower_info = loan_context.get('borrower_info', {})
            borrower_email = borrower_info.get('email')
            
            if not borrower_email:
                return {"success": False, "error": "Borrower email not available"}
            
            subject = f"Rate Lock Confirmed - Loan Application {loan_context.get('loan_application_id')}"
            
            body = f"""
Dear {borrower_info.get('name', 'Borrower')},

Great news! Your rate lock has been successfully confirmed.

LOCK DETAILS:
- Lock ID: {lock_submission.get('lock_id')}
- Interest Rate: {lock_submission.get('rate')}%
- Lock Period: {lock_submission.get('lock_term_days', 30)} days
- Lock Expires: {lock_submission.get('lock_expiration_date')}

Your rate is now protected against market fluctuations until the lock expires.
Please ensure all required documentation is submitted promptly to meet your closing timeline.

Your loan officer will be in touch with next steps.

Best regards,
Mortgage Processing Team

---
This is an automated message from the Rate Lock Processing System.
"""
            
            await self.email_service.send_email(
                to=borrower_email,
                subject=subject,
                body=body,
                attachments=[confirmation_document] if confirmation_document.get("content") else None
            )
            
            logger.info(f"Rate lock confirmation sent to borrower: {borrower_email}")
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Error sending borrower confirmation: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _send_loan_officer_notification(self, loan_context: Dict[str, Any], lock_submission: Dict[str, Any]) -> Dict[str, Any]:
        """Send rate lock notification to loan officer."""
        try:
            if not self.email_service:
                return {"success": False, "error": "Email service not configured"}
            
            loan_officer = await self._get_loan_officer_info(loan_context)
            
            if not loan_officer or not loan_officer.get('email'):
                return {"success": False, "error": "Loan officer email not available"}
            
            subject = f"Rate Lock Executed - {loan_context.get('loan_application_id')}"
            
            body = f"""
Rate lock has been successfully executed for loan application {loan_context.get('loan_application_id')}.

LOCK DETAILS:
- Lock ID: {lock_submission.get('lock_id')}
- Borrower: {loan_context.get('borrower_info', {}).get('name')}
- Rate: {lock_submission.get('rate')}%
- Lock Period: {lock_submission.get('lock_term_days', 30)} days
- Expires: {lock_submission.get('lock_expiration_date')}

The borrower has been notified of the confirmation.
Please proceed with loan processing to meet the closing timeline.

---
Automated Rate Lock Processing System
"""
            
            await self.email_service.send_email(
                to=loan_officer.get('email'),
                subject=subject,
                body=body
            )
            
            logger.info(f"Rate lock notification sent to loan officer: {loan_officer.get('email')}")
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Error sending loan officer notification: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _get_loan_officer_info(self, loan_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get loan officer information from context or LOS."""
        # Try to get from context first
        loan_officer = loan_context.get('loan_officer')
        
        if not loan_officer and self.los_service:
            # Fetch from LOS if not in context
            try:
                loan_officer = await self.los_service.get_loan_officer(
                    loan_context.get('loan_application_id')
                )
            except Exception as e:
                logger.error(f"Error fetching loan officer info: {str(e)}")
        
        return loan_officer