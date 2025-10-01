"""
Email Intake Agent - Enhanced for Service Bus Integration
Parses loan lock requests from Service Bus messages (originating from a Logic App) and initiates the workflow.
"""

import asyncio
import json
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import os

# Semantic Kernel imports
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import kernel_function

# Import our plugins
from plugins.cosmos_db_plugin import CosmosDBPlugin
from plugins.service_bus_plugin import ServiceBusPlugin

logger = logging.getLogger(__name__)

class EmailIntakeAgent:
    """
    Role: AI-powered intake for loan lock requests from Service Bus.
    
    Tasks:
    - Listens for 'new_email_request' messages from Service Bus.
    - Uses an LLM to parse the email content within the message.
    - Validates the request and sender.
    - Creates a rate lock record in Cosmos DB.
    - Sends a message to the next agent in the workflow.
    - Sends a message to the outbound email topic to send an acknowledgment.
    """
    
    def __init__(self):
        self.agent_name = "email_intake_agent"
        self.session_id = f"intake_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.kernel = None
        self.cosmos_plugin = None
        self.servicebus_plugin = None
        
        self._initialized = False

    async def _initialize_kernel(self):
        """Initialize Semantic Kernel with Azure OpenAI and plugins."""
        if self._initialized:
            return
            
        try:
            self.kernel = Kernel()
            
            endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
            api_key = os.environ.get("AZURE_OPENAI_API_KEY") 
            deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
            
            if not all([endpoint, api_key, deployment_name]):
                raise ValueError("Missing Azure OpenAI configuration for Email Intake Agent.")

            self.kernel.add_service(AzureChatCompletion(
                deployment_name=deployment_name,
                endpoint=endpoint,
                api_key=api_key
            ))
            
            self.cosmos_plugin = CosmosDBPlugin(debug=True, session_id=self.session_id)
            self.servicebus_plugin = ServiceBusPlugin(debug=True, session_id=self.session_id)
            
            self.kernel.add_plugin(self.cosmos_plugin, plugin_name="cosmos_db")
            self.kernel.add_plugin(self.servicebus_plugin, plugin_name="service_bus")
            self.kernel.add_plugin(self, plugin_name="email_parser")
            
            self._initialized = True
            logger.info(f"{self.agent_name}: Semantic Kernel initialized successfully")
            
        except Exception as e:
            logger.error(f"{self.agent_name}: Failed to initialize Semantic Kernel - {str(e)}")
            raise

    async def handle_message(self, message: Dict[str, Any]):
        """Handles a single message from the service bus."""
        await self._initialize_kernel()
        
        message_type = message.get('message_type')
        if message_type != 'new_email_request':
            logger.warning(f"Received unexpected message type: {message_type}. Skipping.")
            return

        try:
            loan_application_id_from_subject = message.get('loan_application_id') # Extracted by Logic App
            email_body = message.get('email_body')
            from_address = message.get('from_address')
            
            logger.info(f"{self.agent_name}: Processing email from {from_address} for loan '{loan_application_id_from_subject}'")
            
            # Use the LLM to extract full details from the email body
            extraction_result_str = await self.kernel.invoke(
                self.kernel.plugins["email_parser"]["extract_loan_data_from_email"],
                email_body=email_body,
                subject_loan_id=loan_application_id_from_subject
            )
            extracted_data = json.loads(str(extraction_result_str))

            loan_application_id = extracted_data.get('loan_application_id')
            if not loan_application_id:
                raise ValueError("LLM failed to extract a valid Loan Application ID from the email.")

            # Create the initial record in Cosmos DB
            rate_lock_record = {
                "status": "PENDING_CONTEXT",
                "source_email": from_address,
                "received_at": datetime.utcnow().isoformat(),
                "extracted_data": extracted_data
            }
            await self.cosmos_plugin.create_rate_lock(loan_application_id, json.dumps(rate_lock_record))
            
            # Send audit message
            await self._send_audit_message("EMAIL_PROCESSED", loan_application_id, {
                "email_from": from_address,
                "extracted_data": extracted_data
            })
            
            # Send message to the next agent in the workflow
            await self.servicebus_plugin.send_message_to_topic(
                topic_name="rate_lock_requests",
                message_type="context_retrieval_needed",
                loan_application_id=loan_application_id,
                message_data={"status": "PENDING_CONTEXT"}
            )
            
            # Send a message to the outbound topic to generate an acknowledgment email
            await self._send_acknowledgment_notification(from_address, loan_application_id, extracted_data)
            
            logger.info(f"Successfully initiated rate lock process for loan '{loan_application_id}'")

        except Exception as e:
            error_msg = f"Failed to process email request: {str(e)}"
            logger.error(error_msg)
            await self._send_exception_alert("TECHNICAL_ERROR", "high", error_msg, message.get('loan_application_id', 'unknown'))

    async def process_inbox(self):
        """
        Demo method to simulate processing inbound email queue messages.
        Returns a list of processed rate lock requests for demo purposes.
        """
        # Try to initialize kernel, but continue in demo mode if it fails
        try:
            await self._initialize_kernel()
            ai_available = True
        except Exception as e:
            logger.warning(f"AI services unavailable for demo: {str(e)}")
            print(f"   ⚠️  Running in demo mode without AI services")
            ai_available = False
        
        # Simulate inbound email messages that would come from Service Bus
        sample_messages = [
            {
                "message_type": "new_email_request",
                "loan_application_id": "LA123456",
                "email_body": "Hello, I would like to lock the rate for loan LA123456 for 45 days. The property is at 123 Main St, Anytown, USA. Please confirm. Best regards, John Doe",
                "from_address": "john.doe@email.com"
            },
            {
                "message_type": "new_email_request", 
                "loan_application_id": "LA789012",
                "email_body": "Rate lock request for loan LA789012. Need 30 day lock for property at 456 Oak Ave. Thanks, Jane Smith",
                "from_address": "jane.smith@email.com"
            }
        ]
        
        processed_requests = []
        
        try:
            print(f"📨 Processing {len(sample_messages)} simulated email messages...")
            
            for i, message in enumerate(sample_messages, 1):
                print(f"   📧 Processing message {i}/{len(sample_messages)} from {message['from_address']}")
                
                # Process the message
                loan_application_id = message.get('loan_application_id')
                email_body = message.get('email_body')
                from_address = message.get('from_address')
                
                if ai_available:
                    # Extract data using AI
                    try:
                        extraction_result_str = await self.kernel.invoke(
                            self.kernel.plugins["email_parser"]["extract_loan_data_from_email"],
                            email_body=email_body,
                            subject_loan_id=loan_application_id
                        )
                        extracted_data = json.loads(str(extraction_result_str))
                    except Exception as e:
                        logger.warning(f"AI extraction failed, using fallback: {str(e)}")
                        extracted_data = self._fallback_extract_data(email_body, loan_application_id)
                else:
                    # Use fallback extraction for demo
                    extracted_data = self._fallback_extract_data(email_body, loan_application_id)
                
                print(f"   🤖 Extracted: Loan {extracted_data.get('loan_application_id')}, {extracted_data.get('requested_lock_period_days')} days")
                
                # Create rate lock record
                rate_lock_record = {
                    "rate_lock_id": f"RL{datetime.now().strftime('%Y%m%d%H%M%S')}{i:02d}",
                    "loan_application_id": extracted_data.get("loan_application_id", loan_application_id),
                    "borrower_email": from_address,
                    "status": "PENDING_QUOTE",
                    "requested_lock_period_days": extracted_data.get("requested_lock_period_days", 30),
                    "borrower_name": extracted_data.get("borrower_name", "Unknown"),
                    "property_address": extracted_data.get("property_address", "Unknown"),
                    "created_timestamp": datetime.now().isoformat(),
                    "updated_timestamp": datetime.now().isoformat()
                }
                
                # Store in Cosmos DB (simulated for demo)
                print(f"   💾 Creating rate lock record: {rate_lock_record['rate_lock_id']}")
                
                # Add to processed list
                processed_requests.append(rate_lock_record)
                
                print(f"   ✅ Message processed successfully")
                
                # Small delay to simulate processing time
                await asyncio.sleep(0.5)
                
        except Exception as e:
            logger.error(f"Error in process_inbox demo: {str(e)}")
            print(f"   ❌ Error processing messages: {str(e)}")
        
        return processed_requests
    
    def _fallback_extract_data(self, email_body: str, subject_loan_id: str):
        """
        Fallback data extraction without AI for demo purposes.
        """
        import re
        
        # Try to find a loan ID in the body first
        loan_id_match = re.search(r'LA\d{5,}', email_body, re.IGNORECASE)
        loan_id = loan_id_match.group() if loan_id_match else subject_loan_id
        
        # Extract lock period
        lock_period_match = re.search(r'(\d+)\s*day', email_body, re.IGNORECASE)
        lock_period = int(lock_period_match.group(1)) if lock_period_match else 30
        
        # Extract name (simple heuristic)
        name_match = re.search(r'(Best regards|Thanks|Sincerely),?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)', email_body)
        borrower_name = name_match.group(2) if name_match else "Unknown Borrower"
        
        # Extract address (simple heuristic)  
        address_match = re.search(r'(\d+\s+[A-Za-z\s]+(?:St|Ave|Rd|Blvd|Dr)[^.]*)', email_body)
        property_address = address_match.group(1).strip() if address_match else "Address not found"
        
        return {
            "loan_application_id": loan_id,
            "requested_lock_period_days": lock_period,
            "borrower_name": borrower_name,
            "property_address": property_address
        }

    @kernel_function(
        description="Extracts structured loan application data from the body of an email.",
        name="extract_loan_data_from_email"
    )
    def extract_loan_data_from_email(self, email_body: str, subject_loan_id: str) -> str:
        """
        Uses a simulated LLM to parse the email body and return structured JSON.
        The loan ID from the subject is used as a fallback.
        """
        import re
        
        # Try to find a loan ID in the body first
        loan_id_match = re.search(r'LA\d{5,}', email_body, re.IGNORECASE)
        loan_id = loan_id_match.group() if loan_id_match else subject_loan_id
        
        # Extract lock period
        lock_period_match = re.search(r'(\d+)\s*day', email_body, re.IGNORECASE)
        lock_period = int(lock_period_match.group(1)) if lock_period_match else 30
        
        return json.dumps({
            "loan_application_id": loan_id,
            "requested_lock_period_days": lock_period,
            "borrower_name": "John Doe (extracted)", # Placeholder
            "property_address": "123 Main St, Anytown, USA (extracted)" # Placeholder
        })

    async def _send_acknowledgment_notification(self, recipient_email: str, loan_id: str, extracted_data: Dict[str, Any]):
        """Sends a message to the outbound email topic via Service Bus."""
        
        subject = f"Rate Lock Request Received for Loan: {loan_id}"
        body = f"""
        Dear {extracted_data.get('borrower_name', 'Customer')},

        Thank you for submitting your rate lock request for loan application {loan_id}.

        We have received your request for a {extracted_data.get('requested_lock_period_days')}-day lock period. Our system is now gathering the required information from the Loan Origination System.

        You will receive a separate email with your personalized rate quotes shortly.

        Thank you,
        The Automated Rate Lock System
        """
        
        email_payload = {
            "recipient_email": recipient_email,
            "subject": subject,
            "body": body,
            "attachments": [] # No attachments for acknowledgment
        }
        
        await self.servicebus_plugin.send_message_to_topic(
            topic_name="outbound_email",
            message_type="send_email_notification",
            loan_application_id=loan_id,
            message_data=email_payload
        )
        logger.info(f"Sent acknowledgment notification request to Service Bus for loan '{loan_id}'")

    async def _send_audit_message(self, action: str, loan_application_id: str, audit_data: Dict[str, Any]):
        try:
            await self.servicebus_plugin.send_audit_message(
                agent_name=self.agent_name,
                action=action,
                loan_application_id=loan_application_id,
                audit_data=json.dumps(audit_data)
            )
        except Exception as e:
            logger.error(f"Failed to send audit message: {str(e)}")

    async def _send_exception_alert(self, exception_type: str, priority: str, message: str, loan_application_id: str):
        try:
            exception_data = {
                "agent": self.agent_name,
                "error_message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.servicebus_plugin.send_exception_alert(
                exception_type=exception_type,
                priority=priority,
                loan_application_id=loan_application_id,
                exception_data=json.dumps(exception_data)
            )
        except Exception as e:
            logger.error(f"Failed to send exception alert: {str(e)}")

    def get_agent_status(self):
        """
        Returns the current status of the email intake agent.
        """
        return {
            "agent_name": self.agent_name,
            "session_id": self.session_id,
            "initialized": self._initialized,
            "status": "READY" if self._initialized else "INITIALIZING"
        }

    async def register_for_workflow_messages(self):
        """
        Demo method to simulate registering for workflow messages.
        Returns True to indicate successful registration.
        """
        try:
            print(f"      📡 Registering {self.agent_name} for workflow messages...")
            await asyncio.sleep(0.5)  # Simulate registration time
            print(f"      ✅ Successfully registered for Service Bus messages")
            return True
        except Exception as e:
            logger.error(f"Failed to register for workflow messages: {str(e)}")
            return False

    async def close(self):
        if self._initialized:
            if self.cosmos_plugin: await self.cosmos_plugin.close()
            if self.servicebus_plugin: await self.servicebus_plugin.close()
        logger.info(f"{self.agent_name}: Resources cleaned up.")