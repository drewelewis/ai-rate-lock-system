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

resource office365Connection 'Microsoft.Web/connections@2016-06-01' = {
  name: 'office365'
  location: location
  properties: {
    displayName: 'Office365'
    customParameterValues: {}
    api: {
      id: subscriptionResourceId('Microsoft.Web/locations/managedApis', location, 'office365')
    }
  }
}

resource serviceBusConnection 'Microsoft.Web/connections@2016-06-01' = {
  name: 'servicebus'
  location: location
  properties: {
    displayName: 'ServiceBus'
    customParameterValues: {}
    api: {
      id: subscriptionResourceId('Microsoft.Web/locations/managedApis', location, 'servicebus')
    }
    parameterValues: {
      connectionString: serviceBus.outputs.connectionString
    }
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

module workflows 'workflows.bicep' = {
  name: 'workflows'
  params: {
    location: location
    office365ApiConnectionId: office365Connection.id
    serviceBusApiConnectionId: serviceBusConnection.id
  }
}

// Outputs for application configuration
output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_SUBSCRIPTION_ID string = subscription().subscriptionId

// OpenAI Configuration
output AZURE_OPENAI_NAME string = openAIAccountName
output AZURE_OPENAI_ENDPOINT string = openAI.outputs.endpoint
output AZURE_COSMOSDB_ACCOUNT_NAME string = cosmosDbAccountName
output AZURE_COSMOSDB_ENDPOINT string = cosmosDb.outputs.endpoint
output AZURE_SERVICEBUS_NAMESPACE_NAME string = serviceBusNamespaceName
output AZURE_SERVICEBUS_ENDPOINT string = serviceBus.outputs.endpoint
output AZURE_LOG_ANALYTICS_WORKSPACE_NAME string = logAnalyticsWorkspaceName
output AZURE_APPLICATION_INSIGHTS_NAME string = applicationInsightsName
output OFFICE365_CONNECTION_ID string = office365Connection.id
output SERVICEBUS_CONNECTION_ID string = serviceBusConnection.id
