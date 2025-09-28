#!/usr/bin/env python3
"""
Test script to verify Azure infrastructure deployment
"""
import sys
from dotenv import load_dotenv
from config.azure_config import azure_config

def main():
    """Test the deployed Azure infrastructure"""
    print("🔧 Loading environment variables...")
    load_dotenv()
    
    print("\n📋 Azure Configuration Summary")
    print("=" * 50)
    print(azure_config.get_configuration_summary())
    
    print("\n🔍 Service Endpoints:")
    print("-" * 30)
    print(f"OpenAI Endpoint: {azure_config.get_openai_endpoint()}")
    print(f"OpenAI Service:  {azure_config.get_openai_service_name()}")
    print(f"Cosmos Endpoint: {azure_config.get_cosmosdb_endpoint()}")
    print(f"Cosmos Database: {azure_config.get_cosmosdb_database()}")
    print(f"Service Bus:     {azure_config.get_servicebus_endpoint()}")
    print(f"Service Bus NS:  {azure_config.get_servicebus_namespace()}")
    print(f"App Insights:    {azure_config.get_application_insights_connection()[:50]}...")
    
    print(f"\n🌍 Region: {azure_config.get_azure_location()}")
    print(f"💰 Subscription: {azure_config.get_azure_subscription_id()}")
    
    validation = azure_config.validate_configuration()
    if all(validation.values()):
        print("\n✅ All services configured correctly!")
        print("🚀 Ready to start developing with Azure services!")
        return 0
    else:
        print("\n❌ Some services are not configured properly")
        return 1

if __name__ == "__main__":
    sys.exit(main())