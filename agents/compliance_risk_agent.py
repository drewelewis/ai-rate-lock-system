"""
Compliance & Risk Agent
Ensures rate lock requests comply with internal and regulatory guidelines.
"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ComplianceRiskAgent:
    """
    Role: Ensures the lock request complies with internal and regulatory guidelines.
    
    Tasks:
    - Check lock window vs. estimated closing date
    - Validate lock fees, disclosures, and timing
    - Flag any exceptions (e.g., expired pre-approval, missing disclosures)
    - Ensure regulatory compliance (TRID, state requirements)
    """
    
    def __init__(self, compliance_service=None, disclosure_service=None):
        self.compliance_service = compliance_service
        self.disclosure_service = disclosure_service
        self.agent_name = "ComplianceRiskAgent"
    
    async def validate_lock_request(self, loan_context: Dict[str, Any], rate_quote: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive compliance validation on rate lock request."""
        logger.info(f"{self.agent_name}: Validating compliance for loan {loan_context.get('loan_application_id')}")
        
        try:
            validation_results = {
                "loan_application_id": loan_context.get('loan_application_id'),
                "validation_date": datetime.utcnow().isoformat(),
                "overall_status": "PENDING",
                "compliance_checks": {},
                "required_disclosures": [],
                "exceptions": [],
                "next_actions": [],
                "audit": {
                    "validated_by": self.agent_name,
                    "validated_at": datetime.utcnow().isoformat()
                }
            }
            
            # Perform all compliance checks
            await self._check_lock_timing(loan_context, rate_quote, validation_results)
            await self._validate_disclosures(loan_context, validation_results)
            await self._check_regulatory_requirements(loan_context, validation_results)
            await self._validate_lock_fees(rate_quote, validation_results)
            await self._check_loan_status_eligibility(loan_context, validation_results)
            await self._validate_borrower_capacity(loan_context, validation_results)
            
            # Determine overall status
            validation_results["overall_status"] = self._determine_overall_status(validation_results)
            
            logger.info(f"{self.agent_name}: Compliance validation completed with status {validation_results['overall_status']}")
            return validation_results
            
        except Exception as e:
            logger.error(f"{self.agent_name}: Error during compliance validation - {str(e)}")
            raise
    
    async def _check_lock_timing(self, loan_context: Dict[str, Any], rate_quote: Dict[str, Any], results: Dict[str, Any]) -> None:
        """Validate lock timing against closing schedule."""
        try:
            closing_date = loan_context.get('estimated_closing_date')
            rate_options = rate_quote.get('rate_options', [])
            
            timing_check = {
                "status": "PASS",
                "issues": [],
                "recommendations": []
            }
            
            if not closing_date:
                timing_check["status"] = "WARNING"
                timing_check["issues"].append("No estimated closing date provided")
                timing_check["recommendations"].append("Obtain estimated closing date for optimal lock term selection")
            else:
                # Calculate days to closing
                closing_dt = datetime.fromisoformat(closing_date.replace('Z', '+00:00'))
                days_to_closing = (closing_dt - datetime.utcnow()).days
                
                if days_to_closing < 15:
                    timing_check["status"] = "WARNING"
                    timing_check["issues"].append(f"Short timeline to closing ({days_to_closing} days)")
                    timing_check["recommendations"].append("Consider 30-day lock maximum")
                
                if days_to_closing > 90:
                    timing_check["status"] = "WARNING"
                    timing_check["issues"].append(f"Extended timeline to closing ({days_to_closing} days)")
                    timing_check["recommendations"].append("Consider longer lock terms or delayed lock timing")
                
                # Check if any rate options exceed closing timeline
                for option in rate_options:
                    lock_days = option.get('lock_term_days', 30)
                    if lock_days < days_to_closing - 5:  # 5-day buffer
                        timing_check["recommendations"].append(f"Consider {lock_days}-day lock may be insufficient")
            
            results["compliance_checks"]["lock_timing"] = timing_check
            
        except Exception as e:
            logger.error(f"Error checking lock timing: {str(e)}")
            results["compliance_checks"]["lock_timing"] = {
                "status": "ERROR",
                "issues": [f"Failed to validate timing: {str(e)}"]
            }
    
    async def _validate_disclosures(self, loan_context: Dict[str, Any], results: Dict[str, Any]) -> None:
        """Validate required disclosures are present and current."""
        disclosure_check = {
            "status": "PASS",
            "issues": [],
            "missing_disclosures": []
        }
        
        required_disclosures = [
            "initial_loan_estimate",
            "rate_lock_disclosure",
            "good_faith_estimate",
            "truth_in_lending"
        ]
        
        try:
            loan_id = loan_context.get('loan_application_id')
            
            for disclosure_type in required_disclosures:
                is_present = await self._check_disclosure_present(loan_id, disclosure_type)
                is_current = await self._check_disclosure_current(loan_id, disclosure_type)
                
                if not is_present:
                    disclosure_check["missing_disclosures"].append(disclosure_type)
                    disclosure_check["status"] = "FAIL"
                elif not is_current:
                    disclosure_check["issues"].append(f"{disclosure_type} is outdated")
                    disclosure_check["status"] = "WARNING"
            
            # Add required disclosures to results
            if disclosure_check["missing_disclosures"]:
                results["required_disclosures"].extend(disclosure_check["missing_disclosures"])
                results["next_actions"].append("Generate and send missing disclosures")
            
            results["compliance_checks"]["disclosures"] = disclosure_check
            
        except Exception as e:
            logger.error(f"Error validating disclosures: {str(e)}")
            results["compliance_checks"]["disclosures"] = {
                "status": "ERROR",
                "issues": [f"Failed to validate disclosures: {str(e)}"]
            }
    
    async def _check_regulatory_requirements(self, loan_context: Dict[str, Any], results: Dict[str, Any]) -> None:
        """Check regulatory compliance requirements (TRID, state laws, etc.)."""
        regulatory_check = {
            "status": "PASS",
            "issues": [],
            "requirements": []
        }
        
        try:
            property_state = loan_context.get('property_info', {}).get('state')
            loan_amount = loan_context.get('loan_details', {}).get('loan_amount', 0)
            
            # TRID compliance check
            if loan_amount >= 100000:  # TRID applies to most residential mortgages
                trid_compliant = await self._check_trid_compliance(loan_context)
                if not trid_compliant:
                    regulatory_check["status"] = "FAIL"
                    regulatory_check["issues"].append("TRID compliance requirements not met")
            
            # State-specific requirements
            state_requirements = await self._check_state_requirements(property_state, loan_context)
            if state_requirements["issues"]:
                regulatory_check["issues"].extend(state_requirements["issues"])
                regulatory_check["status"] = "WARNING" if regulatory_check["status"] == "PASS" else regulatory_check["status"]
            
            regulatory_check["requirements"] = state_requirements.get("requirements", [])
            
            results["compliance_checks"]["regulatory"] = regulatory_check
            
        except Exception as e:
            logger.error(f"Error checking regulatory requirements: {str(e)}")
            results["compliance_checks"]["regulatory"] = {
                "status": "ERROR",
                "issues": [f"Failed to validate regulatory requirements: {str(e)}"]
            }
    
    async def _validate_lock_fees(self, rate_quote: Dict[str, Any], results: Dict[str, Any]) -> None:
        """Validate lock fees are reasonable and properly disclosed."""
        fee_check = {
            "status": "PASS",
            "issues": [],
            "fee_summary": {}
        }
        
        try:
            lock_fees = rate_quote.get('lock_fees', {})
            
            # Check fee reasonableness
            for term, fee in lock_fees.items():
                if fee > 1000:  # High fee threshold
                    fee_check["status"] = "WARNING"
                    fee_check["issues"].append(f"High lock fee for {term}: ${fee}")
                
                fee_check["fee_summary"][term] = fee
            
            results["compliance_checks"]["lock_fees"] = fee_check
            
        except Exception as e:
            logger.error(f"Error validating lock fees: {str(e)}")
            results["compliance_checks"]["lock_fees"] = {
                "status": "ERROR",
                "issues": [f"Failed to validate lock fees: {str(e)}"]
            }
    
    async def _check_loan_status_eligibility(self, loan_context: Dict[str, Any], results: Dict[str, Any]) -> None:
        """Check if loan status allows for rate lock."""
        status_check = {
            "status": "PASS",
            "issues": [],
            "current_status": ""
        }
        
        try:
            loan_status = loan_context.get('status_info', {}).get('current_status', '').lower()
            eligible_statuses = ['pre-approved', 'underwritten', 'conditionally_approved', 'clear_to_close']
            
            status_check["current_status"] = loan_status
            
            if loan_status not in eligible_statuses:
                status_check["status"] = "FAIL"
                status_check["issues"].append(f"Loan status '{loan_status}' not eligible for rate lock")
                results["exceptions"].append(f"Ineligible loan status: {loan_status}")
            
            results["compliance_checks"]["loan_status"] = status_check
            
        except Exception as e:
            logger.error(f"Error checking loan status eligibility: {str(e)}")
            results["compliance_checks"]["loan_status"] = {
                "status": "ERROR",
                "issues": [f"Failed to validate loan status: {str(e)}"]
            }
    
    async def _validate_borrower_capacity(self, loan_context: Dict[str, Any], results: Dict[str, Any]) -> None:
        """Validate borrower has capacity to proceed with rate lock."""
        capacity_check = {
            "status": "PASS",
            "issues": [],
            "checks_performed": []
        }
        
        try:
            borrower_info = loan_context.get('borrower_info', {})
            
            # Check income verification
            if not borrower_info.get('income_verified'):
                capacity_check["status"] = "WARNING"
                capacity_check["issues"].append("Income verification pending")
            capacity_check["checks_performed"].append("income_verification")
            
            # Check asset verification
            if not borrower_info.get('assets_verified'):
                capacity_check["status"] = "WARNING"
                capacity_check["issues"].append("Asset verification pending")
            capacity_check["checks_performed"].append("asset_verification")
            
            # Check debt-to-income ratio
            dti = borrower_info.get('debt_to_income')
            if dti and dti > 43:  # Standard DTI threshold
                capacity_check["status"] = "WARNING"
                capacity_check["issues"].append(f"High debt-to-income ratio: {dti}%")
            capacity_check["checks_performed"].append("debt_to_income")
            
            results["compliance_checks"]["borrower_capacity"] = capacity_check
            
        except Exception as e:
            logger.error(f"Error validating borrower capacity: {str(e)}")
            results["compliance_checks"]["borrower_capacity"] = {
                "status": "ERROR",
                "issues": [f"Failed to validate borrower capacity: {str(e)}"]
            }
    
    def _determine_overall_status(self, results: Dict[str, Any]) -> str:
        """Determine overall compliance status based on all checks."""
        checks = results.get("compliance_checks", {})
        
        # If any check failed, overall status is FAIL
        for check_name, check_result in checks.items():
            if check_result.get("status") == "FAIL":
                return "FAIL"
            elif check_result.get("status") == "ERROR":
                return "ERROR"
        
        # If any check has warnings, overall status is WARNING
        for check_name, check_result in checks.items():
            if check_result.get("status") == "WARNING":
                return "WARNING"
        
        return "PASS"
    
    async def _check_disclosure_present(self, loan_id: str, disclosure_type: str) -> bool:
        """Check if required disclosure is present."""
        if not self.disclosure_service:
            return True  # Assume present if service not configured
        
        try:
            return await self.disclosure_service.check_disclosure_exists(loan_id, disclosure_type)
        except Exception:
            return False
    
    async def _check_disclosure_current(self, loan_id: str, disclosure_type: str) -> bool:
        """Check if disclosure is current (not expired)."""
        if not self.disclosure_service:
            return True  # Assume current if service not configured
        
        try:
            return await self.disclosure_service.check_disclosure_current(loan_id, disclosure_type)
        except Exception:
            return False
    
    async def _check_trid_compliance(self, loan_context: Dict[str, Any]) -> bool:
        """Check TRID (Truth in Lending/Real Estate Settlement) compliance."""
        # TODO: Implement TRID compliance checks
        # This would check timing requirements, disclosure accuracy, etc.
        return True  # Placeholder
    
    async def _check_state_requirements(self, state: str, loan_context: Dict[str, Any]) -> Dict[str, Any]:
        """Check state-specific regulatory requirements."""
        state_check = {
            "issues": [],
            "requirements": []
        }
        
        if not state:
            return state_check
        
        # TODO: Implement state-specific compliance checks
        # Different states have different requirements for rate locks
        
        return state_check
    
    async def generate_compliance_report(self, validation_results: Dict[str, Any]) -> str:
        """Generate a human-readable compliance report."""
        report = f"""
COMPLIANCE VALIDATION REPORT
============================
Loan ID: {validation_results.get('loan_application_id')}
Validation Date: {validation_results.get('validation_date')}
Overall Status: {validation_results.get('overall_status')}

COMPLIANCE CHECKS:
"""
        
        for check_name, check_result in validation_results.get('compliance_checks', {}).items():
            report += f"\n{check_name.upper()}: {check_result.get('status')}\n"
            
            if check_result.get('issues'):
                report += "  Issues:\n"
                for issue in check_result.get('issues'):
                    report += f"    - {issue}\n"
        
        if validation_results.get('exceptions'):
            report += "\nEXCEPTIONS:\n"
            for exception in validation_results.get('exceptions'):
                report += f"  - {exception}\n"
        
        if validation_results.get('next_actions'):
            report += "\nNEXT ACTIONS:\n"
            for action in validation_results.get('next_actions'):
                report += f"  - {action}\n"
        
        return report