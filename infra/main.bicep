targetScope = 'resourceGroup'

@minLength(1)
@maxLength(64)
@description('Name of the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Principal ID of the user that will be granted access to the resources')
param principalId string = ''

// Optional parameters
@description('The pricing tier for the OpenAI service')
@allowed(['S0'])
param openAISkuName string = 'S0'

@description('The pricing tier for the Service Bus namespace')
@allowed(['Basic', 'Standard', 'Premium'])
param serviceBusSkuName string = 'Standard'

// Generate a unique suffix for resource names
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = { 'azd-env-name': environmentName }

// Resource names
var prefix = '${environmentName}-${resourceToken}'
var openAIAccountName = '${prefix}-openai'
var cosmosDbAccountName = '${prefix}-cosmos'
var serviceBusNamespaceName = '${prefix}-servicebus'
var logAnalyticsWorkspaceName = '${prefix}-logs'
var applicationInsightsName = '${prefix}-appinsights'
// Container-related names - commented out for now
// var containerAppsEnvironmentName = '${prefix}-containerenv'
// var containerRegistryName = replace('${prefix}registry', '-', '')

module openAI 'core/ai/openai.bicep' = {
  name: 'openai'
  params: {
    name: openAIAccountName
    location: location
    tags: tags
    skuName: openAISkuName
    principalId: principalId
  }
}

module cosmosDb 'core/database/cosmos.bicep' = {
  name: 'cosmos'
  params: {
    name: cosmosDbAccountName
    location: location
    tags: tags
    principalId: principalId
  }
}

module serviceBus 'core/messaging/servicebus.bicep' = {
  name: 'servicebus'
  params: {
    name: serviceBusNamespaceName
    location: location
    tags: tags
    skuName: serviceBusSkuName
    principalId: principalId
  }
}

module monitoring 'core/monitor/monitoring.bicep' = {
  name: 'monitoring'
  params: {
    location: location
    tags: tags
    logAnalyticsName: logAnalyticsWorkspaceName
    applicationInsightsName: applicationInsightsName
  }
}

// Container services - commented out for now, will add back when containerizing
// module containerApps 'core/host/container-apps.bicep' = {
//   name: 'container-apps'
//   params: {
//     name: containerAppsEnvironmentName
//     location: location
//     tags: tags
//     applicationInsightsName: applicationInsightsName
//     logAnalyticsWorkspaceName: logAnalyticsWorkspaceName
//   }
// }

// module containerRegistry 'core/host/container-registry.bicep' = {
//   name: 'container-registry'
//   params: {
//     name: containerRegistryName
//     location: location
//     tags: tags
//     principalId: principalId
//   }
// }

// Outputs for application configuration
output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_SUBSCRIPTION_ID string = subscription().subscriptionId

// OpenAI Configuration
output AZURE_OPENAI_ENDPOINT string = openAI.outputs.endpoint
output AZURE_OPENAI_SERVICE string = openAI.outputs.name

// Cosmos DB Configuration  
output AZURE_COSMOS_ENDPOINT string = cosmosDb.outputs.endpoint
output AZURE_COSMOS_DATABASE_NAME string = cosmosDb.outputs.databaseName

// Service Bus Configuration
output AZURE_SERVICE_BUS_ENDPOINT string = serviceBus.outputs.endpoint
output AZURE_SERVICE_BUS_NAMESPACE string = serviceBus.outputs.namespaceName

// Container Apps Configuration - commented out for now
// output AZURE_CONTAINER_APPS_ENVIRONMENT_ID string = containerApps.outputs.environmentId
// output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.outputs.loginServer
// output AZURE_CONTAINER_REGISTRY_NAME string = containerRegistry.outputs.name

// Monitoring Configuration
output APPLICATIONINSIGHTS_CONNECTION_STRING string = monitoring.outputs.applicationInsightsConnectionString
