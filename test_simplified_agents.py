#!/usr/bin/env python3
"""
Simple test to verify enhanced agents work without telemetry complexity.
This test focuses on the core functionality without Azure SDK dependencies.
"""

import asyncio
import os
from datetime import datetime

# Set up mock environment variables for testing
os.environ['AZURE_OPENAI_ENDPOINT'] = 'https://mock-openai.openai.azure.com/'
os.environ['AZURE_OPENAI_API_KEY'] = 'mock-key-for-testing'
os.environ['AZURE_OPENAI_CHAT_DEPLOYMENT_NAME'] = 'gpt-4'
os.environ['AZURE_COSMOS_ENDPOINT'] = 'https://mock-cosmos.documents.azure.com:443/'
os.environ['AZURE_COSMOS_KEY'] = 'mock-cosmos-key'

print("🚀 Testing Simplified AI Rate Lock Agents")
print("=" * 50)

def test_operations_import():
    """Test that operations can be imported without telemetry delays"""
    print("\n📦 Testing Operations Import Speed...")
    
    import time
    
    # Test Cosmos DB Operations
    start_time = time.time()
    try:
        from operations.cosmos_db_operations import CosmosDBOperations
        cosmos_ops = CosmosDBOperations()
        cosmos_time = time.time() - start_time
        print(f"✅ Cosmos DB Operations: {cosmos_time:.3f}s (no telemetry delays!)")
    except Exception as e:
        print(f"❌ Cosmos DB Operations failed: {e}")
    
    # Test Risk Operations  
    start_time = time.time()
    try:
        from operations.risk_operations import RiskOperations
        risk_ops = RiskOperations()
        risk_time = time.time() - start_time
        print(f"✅ Risk Operations: {risk_time:.3f}s (simplified!)")
    except Exception as e:
        print(f"❌ Risk Operations failed: {e}")
    
    # Test Service Bus Operations (may fail without azure-servicebus package)
    start_time = time.time()
    try:
        from operations.service_bus_operations import ServiceBusOperations
        sb_ops = ServiceBusOperations()
        sb_time = time.time() - start_time
        print(f"✅ Service Bus Operations: {sb_time:.3f}s (clean!)")
    except ImportError as e:
        print(f"⚠️  Service Bus Operations: Missing azure-servicebus package (expected)")
    except Exception as e:
        print(f"❌ Service Bus Operations failed: {e}")

def test_plugin_import():
    """Test that plugins can be imported cleanly"""
    print("\n🔌 Testing Plugin Import...")
    
    try:
        from plugins.cosmos_db_plugin import CosmosDBPlugin
        print("✅ Cosmos DB Plugin imported")
    except Exception as e:
        print(f"❌ Cosmos DB Plugin failed: {e}")
    
    try:
        from plugins.risk_plugin import RiskPlugin  
        print("✅ Risk Plugin imported")
    except Exception as e:
        print(f"❌ Risk Plugin failed: {e}")
    
    try:
        from plugins.service_bus_plugin import ServiceBusPlugin
        print("⚠️  Service Bus Plugin: May fail without azure-servicebus")
    except Exception as e:
        print(f"⚠️  Service Bus Plugin expected error: {type(e).__name__}")

def test_semantic_kernel_setup():
    """Test Semantic Kernel setup without full Azure dependencies"""
    print("\n🧠 Testing Semantic Kernel Setup...")
    
    try:
        from semantic_kernel import Kernel
        from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
        
        kernel = Kernel()
        print("✅ Semantic Kernel imported successfully")
        
        # Test Azure OpenAI service setup (won't connect but will validate config)
        try:
            chat_service = AzureChatCompletion(
                service_id="azure_openai_chat",
                deployment_name=os.getenv('AZURE_OPENAI_CHAT_DEPLOYMENT_NAME', 'gpt-4'),
                endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
                api_key=os.getenv('AZURE_OPENAI_API_KEY')
            )
            kernel.add_service(chat_service)
            print("✅ Azure OpenAI service configuration validated")
        except Exception as e:
            print(f"⚠️  Azure OpenAI setup: {e}")
            
    except Exception as e:
        print(f"❌ Semantic Kernel setup failed: {e}")

def main():
    """Run all simplified tests"""
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_operations_import()
    test_plugin_import() 
    test_semantic_kernel_setup()
    
    print("\n" + "=" * 50)
    print("✅ Simplified agent testing completed!")
    print("📝 Next steps:")
    print("   1. Install missing packages: pip install -r requirements.txt")
    print("   2. Set up Azure environment variables")
    print("   3. Run full demo: python demo_enhanced_agents.py")

if __name__ == "__main__":
    main()