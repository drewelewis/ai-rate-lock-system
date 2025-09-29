"""
Service Bus Operations
Handles all interactions with Azure Service Bus for messaging.
"""

import os
import json
from typing import Dict, Any, List, Optional
import asyncio
from azure.servicebus.aio import ServiceBusClient, ServiceBusMessage
from azure.identity.aio import DefaultAzureCredential
from utils.logger import console_info, console_debug, console_warning, console_error, console_telemetry_event

class ServiceBusOperations:
    def __init__(self):
        """
        Initialize the ServiceBusOperations class.
        """
        self.servicebus_namespace = os.getenv('AZURE_SERVICEBUS_NAMESPACE')
        self.credential = None
        self.client = None
        
        # Topics as defined in the Bicep template
        self.topics = {
            'inbound_email': 'inbound-email-requests',
            'rate_lock_requests': 'rate-lock-requests',
            'rate_quotes_generated': 'rate-quotes-generated',
            'compliance_passed': 'compliance-passed',
            'compliance_failed': 'compliance-failed',
            'audit_events': 'audit-events',
            'exception_alerts': 'exception-alerts',
            'outbound_email': 'outbound-email-notifications'
        }
        
        console_info(f"Service Bus Operations initialized for namespace: {self.servicebus_namespace}", "ServiceBusOps")

    async def _get_servicebus_client(self):
        """
        Get or create Service Bus client with proper authentication.
        """
        if self.client is None:
            try:
                if not self.servicebus_namespace:
                    raise ValueError("AZURE_SERVICEBUS_NAMESPACE environment variable is required")
                
                self.credential = DefaultAzureCredential()
                fully_qualified_namespace = f"{self.servicebus_namespace}.servicebus.windows.net"
                self.client = ServiceBusClient(fully_qualified_namespace, self.credential)
                
                console_info("Service Bus client initialized successfully", "ServiceBusOps")
                
            except Exception as e:
                console_error(f"Failed to initialize Service Bus client: {e}", "ServiceBusOps")
                raise
        
        return self.client

    async def send_message(self, topic_name: str, message_body: Dict[str, Any], correlation_id: Optional[str] = None) -> bool:
        """
        Send a message to a specific Service Bus topic.
        
        Args:
            topic_name (str): The logical name of the topic to send the message to.
            message_body (Dict[str, Any]): The message payload.
            correlation_id (str, optional): A correlation ID for tracking.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            client = await self._get_servicebus_client()
            actual_topic_name = self.topics.get(topic_name)
            if not actual_topic_name:
                raise ValueError(f"Topic '{topic_name}' not found in configuration.")

            async with client:
                sender = client.get_topic_sender(topic_name=actual_topic_name)
                async with sender:
                    message_to_send = ServiceBusMessage(
                        body=json.dumps(message_body),
                        content_type="application/json",
                        correlation_id=correlation_id
                    )
                    await sender.send_messages(message_to_send)
            
            console_info(f"Message sent to topic '{actual_topic_name}'", "ServiceBusOps")
            console_telemetry_event("message_sent", {
                "topic": actual_topic_name,
                "correlation_id": correlation_id,
                "message_type": message_body.get('message_type')
            }, "ServiceBusOps")
            
            return True

        except Exception as e:
            console_error(f"Failed to send message to topic '{topic_name}': {e}", "ServiceBusOps")
            return False

    async def close(self):
        """
        Clean up resources.
        """
        try:
            if self.client:
                await self.client.close()
                console_info("Service Bus client closed", "ServiceBusOps")
            
            if self.credential:
                await self.credential.close()
                console_info("Azure credential closed for Service Bus", "ServiceBusOps")
                
        except Exception as e:
            console_warning(f"Error closing Service Bus resources: {e}", "ServiceBusOps")
