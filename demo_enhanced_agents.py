"""
AI Rate Lock System - Enhanced Agent Demo
Demonstrates the new Semantic Kernel integration with the agents.
"""

import asyncio
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Import enhanced agents
from agents.email_intake_agent import EmailIntakeAgent
from agents.rate_quote_agent import RateQuoteAgent

async def demo_enhanced_agents():
    """Demo the enhanced AI-powered agent workflow."""
    print("\n🚀 AI Rate Lock System - Enhanced Agent Demo")
    print("=" * 60)
    
    # Initialize agents
    print("\n📋 Initializing AI-Enhanced Agents...")
    email_agent = EmailIntakeAgent()
    rate_agent = RateQuoteAgent()
    
    try:
        # Demo 1: Email Intake Agent Processing
        print("\n📧 Demo 1: AI-Powered Email Processing")
        print("-" * 40)
        
        processed_requests = await email_agent.process_inbox()
        
        if processed_requests:
            for request in processed_requests:
                print(f"✅ Processed Rate Lock Request: {request.get('rate_lock_id')}")
                print(f"   📋 Loan Application: {request.get('loan_application_id')}")
                print(f"   📧 Borrower: {request.get('borrower_email')}")
                print(f"   ⏱️  Status: {request.get('status')}")
                
                # Demo 2: Rate Quote Agent Processing
                print(f"\n💰 Demo 2: AI-Powered Rate Quote Generation")
                print("-" * 40)
                
                rate_result = await rate_agent.process_rate_quote_request(request.get('rate_lock_id'))
                
                if rate_result.get('success'):
                    print(f"✅ Generated Rate Quotes: {rate_result.get('quote_count')} options")
                    print(f"   📋 Rate Lock ID: {rate_result.get('rate_lock_id')}")
                    print(f"   ⏰ Expires: {rate_result.get('expires_at')}")
                    print(f"   📊 Status: {rate_result.get('status')}")
                else:
                    print(f"❌ Rate quote generation failed: {rate_result.get('error')}")
        else:
            print("📭 No email requests found to process")
        
        # Demo 3: Agent Status Check
        print(f"\n🔧 Demo 3: Agent Configuration Status")
        print("-" * 40)
        
        email_status = email_agent.get_agent_status()
        rate_status = rate_agent.get_agent_status()
        
        print("📧 Email Intake Agent:")
        print(f"   🤖 Initialized: {email_status.get('initialized')}")
        print(f"   🧠 AI Service: {email_status.get('has_chat_service')}")
        print(f"   🔌 Plugins: {json.dumps(email_status.get('plugins', {}), indent=6)}")
        
        print("\n💰 Rate Quote Agent:")
        print(f"   🤖 Initialized: {rate_status.get('initialized')}")
        print(f"   🧠 AI Service: {rate_status.get('has_chat_service')}")
        print(f"   🔌 Plugins: {json.dumps(rate_status.get('plugins', {}), indent=6)}")
        
        # Demo 4: Workflow Message Registration
        print(f"\n🔄 Demo 4: Service Bus Message Registration")
        print("-" * 40)
        
        email_registered = await email_agent.register_for_workflow_messages()
        rate_registered = await rate_agent.register_for_workflow_messages()
        
        print(f"📧 Email Agent Messages: {'✅ Registered' if email_registered else '❌ Failed'}")
        print(f"💰 Rate Agent Messages: {'✅ Registered' if rate_registered else '❌ Failed'}")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {str(e)}")
    
    finally:
        # Clean up resources
        print(f"\n🧹 Cleaning up agent resources...")
        await email_agent.close()
        await rate_agent.close()
        print("✅ Cleanup complete")

async def demo_agent_capabilities():
    """Demo individual agent capabilities."""
    print("\n🎯 Agent Capabilities Overview")
    print("=" * 60)
    
    capabilities = {
        "📧 Email Intake Agent": [
            "🤖 AI-powered email parsing and data extraction",
            "🔍 Intelligent borrower identity validation", 
            "💾 Automated Cosmos DB rate lock record creation",
            "📨 Service Bus workflow coordination",
            "✉️  AI-generated personalized acknowledgment emails"
        ],
        "💰 Rate Quote Agent": [
            "🧠 AI-driven pricing strategy optimization",
            "📊 Real-time market analysis and rate adjustments",
            "🎯 Smart lock term recommendations",
            "👤 Personalized rate options based on borrower profile",
            "⚖️  Comprehensive risk analysis integration"
        ]
    }
    
    for agent, features in capabilities.items():
        print(f"\n{agent}:")
        for feature in features:
            print(f"   {feature}")
    
    print(f"\n🔧 Shared Infrastructure:")
    print("   🌟 Semantic Kernel integration with Azure OpenAI")
    print("   🏗️  Cosmos DB operations for data persistence") 
    print("   📡 Service Bus messaging for agent coordination")
    print("   📈 Risk analysis engine for intelligent decision making")
    print("   📊 Comprehensive audit logging and monitoring")

if __name__ == "__main__":
    print("🏢 AI Rate Lock System - Enhanced with Semantic Kernel")
    print("Built for intelligent mortgage rate lock processing")
    print(f"Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Run capability overview
        asyncio.run(demo_agent_capabilities())
        
        # Run agent demo
        asyncio.run(demo_enhanced_agents())
        
        print(f"\n🎉 Demo completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
    
    print(f"Demo ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")