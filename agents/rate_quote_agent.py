"""
Rate Quote Agent
Fetches current rate lock options from pricing engines and matches to borrower profiles.
"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RateQuoteAgent:
    """
    Role: Fetches current rate lock options.
    
    Tasks:
    - Query pricing engine (e.g., Optimal Blue, MCT, Polly)
    - Match borrower's loan profile to available rate lock terms
    - Return options (e.g., 30-day lock @ 6.25%, 45-day @ 6.375%)
    - Include float-down or lock-and-shop options if available
    """
    
    def __init__(self, pricing_service=None):
        self.pricing_service = pricing_service
        self.agent_name = "RateQuoteAgent"
    
    async def get_rate_options(self, loan_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get available rate lock options for the loan."""
        logger.info(f"{self.agent_name}: Getting rate options for loan {loan_context.get('loan_application_id')}")
        
        try:
            # Validate loan context
            if not self._validate_loan_context(loan_context):
                raise ValueError("Invalid loan context provided")
            
            # Build pricing request
            pricing_request = self._build_pricing_request(loan_context)
            
            # Fetch rate options from pricing engine
            rate_options = await self._fetch_rate_options(pricing_request)
            
            # Calculate lock terms based on closing date
            lock_terms = self._calculate_lock_terms(loan_context)
            
            # Build comprehensive rate quote response
            quote_response = {
                "loan_application_id": loan_context.get('loan_application_id'),
                "quote_id": self._generate_quote_id(),
                "rate_options": rate_options,
                "lock_terms": lock_terms,
                "pricing_date": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(hours=4)).isoformat(),  # Rate quotes typically expire in 4 hours
                "lock_fees": self._calculate_lock_fees(rate_options),
                "special_programs": self._check_special_programs(loan_context),
                "audit": {
                    "quoted_by": self.agent_name,
                    "quoted_at": datetime.utcnow().isoformat()
                }
            }
            
            logger.info(f"{self.agent_name}: Successfully retrieved {len(rate_options)} rate options")
            return quote_response
            
        except Exception as e:
            logger.error(f"{self.agent_name}: Error getting rate options - {str(e)}")
            raise
    
    def _validate_loan_context(self, loan_context: Dict[str, Any]) -> bool:
        """Validate that loan context contains required fields for pricing."""
        required_fields = [
            'loan_application_id',
            'loan_details.loan_amount',
            'loan_details.loan_type',
            'property_info.property_type',
            'property_info.occupancy'
        ]
        
        for field in required_fields:
            if '.' in field:
                # Handle nested fields
                parts = field.split('.')
                value = loan_context
                for part in parts:
                    value = value.get(part, {})
                if not value:
                    logger.error(f"Missing required field: {field}")
                    return False
            else:
                if not loan_context.get(field):
                    logger.error(f"Missing required field: {field}")
                    return False
        
        return True
    
    def _build_pricing_request(self, loan_context: Dict[str, Any]) -> Dict[str, Any]:
        """Build pricing request for the pricing engine."""
        loan_details = loan_context.get('loan_details', {})
        property_info = loan_context.get('property_info', {})
        borrower_info = loan_context.get('borrower_info', {})
        
        return {
            "loan_amount": loan_details.get('loan_amount'),
            "loan_type": loan_details.get('loan_type'),
            "loan_purpose": loan_details.get('loan_purpose'),
            "property_type": property_info.get('property_type'),
            "occupancy": property_info.get('occupancy'),
            "property_state": property_info.get('state'),
            "credit_score": borrower_info.get('credit_score'),
            "ltv_ratio": self._calculate_ltv_ratio(loan_context),
            "debt_to_income": borrower_info.get('debt_to_income'),
            "loan_term": loan_details.get('loan_term', 30),
            "rate_type": loan_details.get('rate_type', 'Fixed')
        }
    
    async def _fetch_rate_options(self, pricing_request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch rate options from pricing engine."""
        if not self.pricing_service:
            # Return mock data for development
            return self._get_mock_rate_options(pricing_request)
        
        try:
            # TODO: Implement actual pricing engine integration
            rate_options = await self.pricing_service.get_rates(pricing_request)
            return rate_options
            
        except Exception as e:
            logger.error(f"Error fetching rate options from pricing engine: {str(e)}")
            # Fallback to mock data
            return self._get_mock_rate_options(pricing_request)
    
    def _get_mock_rate_options(self, pricing_request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate mock rate options for testing."""
        base_rate = 6.25  # Mock base rate
        
        return [
            {
                "rate": base_rate,
                "points": 0.0,
                "lock_term_days": 30,
                "product_description": "30-Year Fixed",
                "apr": base_rate + 0.125,
                "monthly_payment": self._calculate_monthly_payment(
                    pricing_request.get('loan_amount', 400000),
                    base_rate,
                    30 * 12
                )
            },
            {
                "rate": base_rate + 0.125,
                "points": 0.0,
                "lock_term_days": 45,
                "product_description": "30-Year Fixed (45-day lock)",
                "apr": base_rate + 0.25,
                "monthly_payment": self._calculate_monthly_payment(
                    pricing_request.get('loan_amount', 400000),
                    base_rate + 0.125,
                    30 * 12
                )
            },
            {
                "rate": base_rate + 0.25,
                "points": 0.0,
                "lock_term_days": 60,
                "product_description": "30-Year Fixed (60-day lock)",
                "apr": base_rate + 0.375,
                "monthly_payment": self._calculate_monthly_payment(
                    pricing_request.get('loan_amount', 400000),
                    base_rate + 0.25,
                    30 * 12
                )
            }
        ]
    
    def _calculate_lock_terms(self, loan_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Calculate appropriate lock terms based on closing timeline."""
        closing_date = loan_context.get('estimated_closing_date')
        
        if not closing_date:
            # Default terms if no closing date
            return [
                {"term_days": 30, "recommended": False},
                {"term_days": 45, "recommended": True},
                {"term_days": 60, "recommended": False}
            ]
        
        # Calculate days to closing
        try:
            closing_dt = datetime.fromisoformat(closing_date.replace('Z', '+00:00'))
            days_to_closing = (closing_dt - datetime.utcnow()).days
            
            terms = []
            
            if days_to_closing <= 25:
                terms.append({"term_days": 30, "recommended": True})
            else:
                terms.append({"term_days": 30, "recommended": False})
            
            if days_to_closing <= 40:
                terms.append({"term_days": 45, "recommended": days_to_closing > 25})
            else:
                terms.append({"term_days": 45, "recommended": False})
            
            terms.append({"term_days": 60, "recommended": days_to_closing > 40})
            
            return terms
            
        except Exception as e:
            logger.error(f"Error calculating lock terms: {str(e)}")
            return [
                {"term_days": 30, "recommended": False},
                {"term_days": 45, "recommended": True},
                {"term_days": 60, "recommended": False}
            ]
    
    def _calculate_lock_fees(self, rate_options: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate lock fees for different terms."""
        return {
            "30_day": 0.0,      # No fee for 30-day lock
            "45_day": 125.0,    # Small fee for extended lock
            "60_day": 250.0     # Higher fee for longer lock
        }
    
    def _check_special_programs(self, loan_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for special rate lock programs (float-down, lock-and-shop, etc.)."""
        programs = []
        
        loan_details = loan_context.get('loan_details', {})
        
        # Float-down option
        if loan_details.get('loan_type') in ['Conventional', 'VA', 'FHA']:
            programs.append({
                "program_type": "float_down",
                "description": "One-time rate reduction if rates improve",
                "fee": 250.0,
                "terms": "Available once during lock period if rates drop by 0.25% or more"
            })
        
        # Lock-and-shop for purchase loans
        if loan_details.get('loan_purpose') == 'Purchase':
            programs.append({
                "program_type": "lock_and_shop",
                "description": "Lock rate before finding property",
                "fee": 500.0,
                "terms": "45-day rate lock while shopping for property"
            })
        
        return programs
    
    def _calculate_ltv_ratio(self, loan_context: Dict[str, Any]) -> Optional[float]:
        """Calculate loan-to-value ratio."""
        loan_amount = loan_context.get('loan_details', {}).get('loan_amount', 0)
        property_value = loan_context.get('property_info', {}).get('appraised_value', 0)
        
        if property_value > 0:
            return round((loan_amount / property_value) * 100, 2)
        
        return None
    
    def _calculate_monthly_payment(self, loan_amount: float, rate: float, num_payments: int) -> float:
        """Calculate monthly principal and interest payment."""
        if rate == 0:
            return loan_amount / num_payments
        
        monthly_rate = rate / 100 / 12
        payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / \
                 ((1 + monthly_rate) ** num_payments - 1)
        
        return round(payment, 2)
    
    def _generate_quote_id(self) -> str:
        """Generate unique quote identifier."""
        return f"RQ-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    async def refresh_expired_quote(self, quote_id: str, loan_context: Dict[str, Any]) -> Dict[str, Any]:
        """Refresh an expired rate quote with current market rates."""
        logger.info(f"{self.agent_name}: Refreshing expired quote {quote_id}")
        
        # Generate new quote with updated rates
        return await self.get_rate_options(loan_context)