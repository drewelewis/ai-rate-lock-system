"""
Azure Rate Lock System - AZD Infrastructure Setup Guide
Creates the complete Azure infrastructure using Azure Developer CLI (azd)
"""

print("🚀 Azure Rate Lock System - Infrastructure Setup Guide")
print("=" * 60)

print("\n📋 Prerequisites:")
print("   • Azure Developer CLI (azd) installed")
print("   • Azure CLI (az) installed and authenticated")
print("   • Docker installed (for container deployment)")
print("   • Python 3.9+ installed")

print("\n🔧 Setup Steps:")

print("\n1. Initialize AZD Environment:")
print("   azd init --template ./")
print("   # This creates .azure directory and configures the environment")

print("\n2. Login to Azure:")
print("   azd auth login")
print("   # Follow the authentication prompts")

print("\n3. Set Environment Variables (Optional):")
print("   azd env set AZURE_LOCATION eastus")
print("   azd env set AZURE_ENV_NAME ai-rate-lock-dev")
print("   # Customize location and environment name as needed")

print("\n4. Deploy Infrastructure:")
print("   azd up")
print("   # This provisions all Azure resources and deploys the application")

print("\n🏗️ Infrastructure Components Created:")

print("\n📡 Azure OpenAI Service:")
print("   • Account: <env>-<token>-openai")
print("   • Models Deployed:")
print("     - gpt-4o (10 TPM capacity)")
print("     - text-embedding-3-small (10 TPM capacity)")
print("   • Role: Cognitive Services OpenAI User assigned")

print("\n🗃️ Cosmos DB Account:")
print("   • Account: <env>-<token>-cosmos")
print("   • Database: RateLockSystem")
print("   • Containers:")
print("     - RateLockRecords (partition: /loanApplicationId)")
print("     - AuditLogs (partition: /auditDate, TTL: 30 days)")
print("     - Configuration (partition: /configType)")
print("     - Exceptions (partition: /priority, TTL: 90 days)")

print("\n📨 Service Bus Namespace:")
print("   • Namespace: <env>-<token>-servicebus")
print("   • Topics & Subscriptions:")
print("     - workflow-events:")
print("       → email-intake-agent")
print("       → loan-context-agent") 
print("       → rate-quote-agent")
print("       → compliance-risk-agent")
print("       → lock-confirmation-agent")
print("     - audit-events:")
print("       → audit-logging-agent")
print("     - exception-alerts:")
print("       → exception-handler-agent")
print("       → human-notifications (high priority filter)")

print("\n🔍 Monitoring & Logging:")
print("   • Log Analytics Workspace: <env>-<token>-logs")
print("   • Application Insights: <env>-<token>-appinsights")
print("   • 30-day log retention")

print("\n🐳 Container Platform:")
print("   • Container Apps Environment: <env>-<token>-containerenv")
print("   • Container Registry: <env><token>registry")
print("   • Integrated with Log Analytics and App Insights")

print("\n🔐 Security & Access:")
print("   • Managed Identity integration")
print("   • RBAC role assignments:")
print("     - Cognitive Services OpenAI User")
print("     - DocumentDB Account Contributor") 
print("     - Service Bus Data Owner")
print("     - ACR Pull")

print("\n📊 Partition Strategies:")

print("\n🗃️ Cosmos DB Partitioning:")
print("   • RateLockRecords: /loanApplicationId")
print("     - Distributes by loan application for balanced access")
print("     - Enables efficient single-loan queries")
print("   • AuditLogs: /auditDate (YYYY-MM-DD)")
print("     - Time-series partitioning for efficient date range queries")
print("     - Automatic cleanup with TTL")
print("   • Configuration: /configType")
print("     - Separates agent-settings, business-rules, rate-tables")
print("   • Exceptions: /priority")
print("     - Enables efficient priority-based queries")

print("\n📨 Service Bus Design:")
print("   • Topics for publish-subscribe patterns")
print("   • Message filtering with SQL expressions")
print("   • Dead letter queues for failed processing")
print("   • Duplicate detection (10-minute window)")
print("   • Ordered delivery for workflow events")

print("\n🔄 Post-Deployment:")

print("\n5. Get Connection Information:")
print("   azd env get-values")
print("   # Outputs all connection strings and endpoints")

print("\n6. Update Local Environment:")
print("   # Connection strings are automatically written to .env file")
print("   # Verify .env contains:")
print("   #   AZURE_OPENAI_ENDPOINT=...")
print("   #   AZURE_COSMOS_ENDPOINT=...")
print("   #   AZURE_SERVICE_BUS_ENDPOINT=...")

print("\n7. Test the Infrastructure:")
print("   python -c \"from config import azure_config; print('✅ Config loaded successfully')\"")

print("\n🎯 Architecture Benefits:")
print("   ✅ Serverless Cosmos DB - pay per operation")
print("   ✅ Standard Service Bus - optimized for workflow patterns") 
print("   ✅ Container Apps - serverless container hosting")
print("   ✅ Integrated monitoring and logging")
print("   ✅ Proper partitioning for scalability")
print("   ✅ Security best practices with managed identities")

print("\n💡 Cleanup (when needed):")
print("   azd down --purge")
print("   # Removes all resources and resource group")

print("\n🚀 Ready to build your AI Rate Lock Agents!")
print("   Next: Implement your Python agents using the generated connection strings")

print("\n" + "=" * 60)