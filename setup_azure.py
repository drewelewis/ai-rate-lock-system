"""
Azure Resource Setup Script
Creates the necessary Azure resources for the Rate Lock System
"""

print("Azure Rate Lock System - Resource Setup Guide")
print("=" * 50)

print("\n1. Azure Service Bus Setup:")
print("   Development Namespace: rate-lock-dev")
print("   Production Namespace: rate-lock-prod")
print("\n   Run these Azure CLI commands:")
print("   # Create Service Bus namespaces")
print("   az servicebus namespace create --name rate-lock-dev --resource-group YOUR_RG --location eastus --sku Standard")
print("   az servicebus namespace create --name rate-lock-prod --resource-group YOUR_RG --location eastus --sku Standard")
print("\n   # Get connection strings")
print("   az servicebus namespace authorization-rule keys list --resource-group YOUR_RG --namespace-name rate-lock-dev --name RootManageSharedAccessKey")
print("   az servicebus namespace authorization-rule keys list --resource-group YOUR_RG --namespace-name rate-lock-prod --name RootManageSharedAccessKey")

print("\n2. Azure Cosmos DB Setup:")
print("   Development Account: rate-lock-dev")
print("   Production Account: rate-lock-prod")
print("\n   Run these Azure CLI commands:")
print("   # Create Cosmos DB accounts")
print("   az cosmosdb create --name rate-lock-dev --resource-group YOUR_RG --locations regionName=EastUS")
print("   az cosmosdb create --name rate-lock-prod --resource-group YOUR_RG --locations regionName=EastUS")
print("\n   # Get connection strings")
print("   az cosmosdb keys list --name rate-lock-dev --resource-group YOUR_RG --type connection-strings")
print("   az cosmosdb keys list --name rate-lock-prod --resource-group YOUR_RG --type connection-strings")

print("\n3. Update your .env file with the actual connection strings from the commands above")

print("\n4. Queue Configuration:")
print("   The following queues will be created automatically by the agents:")
print("   - new-requests")
print("   - context-retrieved")
print("   - rates-presented")
print("   - compliance-passed")
print("   - exceptions")

print("\n5. Start local services:")
print("   docker-compose up -d")

print("\nSetup Complete! Your system will use:")
print("✅ Azure Service Bus for messaging (both dev and prod)")
print("✅ Azure Cosmos DB for data storage (both dev and prod)")
print("✅ Local Redis for caching and agent memory")