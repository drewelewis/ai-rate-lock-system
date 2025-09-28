@description('The name of the Service Bus namespace')
param name string

@description('The location into which the Service Bus resources should be deployed')
param location string = resourceGroup().location

@description('The tags to apply to the Service Bus namespace')
param tags object = {}

@description('The pricing tier for the Service Bus namespace')
@allowed(['Basic', 'Standard', 'Premium'])
param skuName string = 'Standard'

@description('The principal ID to assign roles to')
param principalId string = ''

resource serviceBusNamespace 'Microsoft.ServiceBus/namespaces@2021-11-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: skuName
  }
  properties: {
    disableLocalAuth: false
  }
}

// Main workflow topic for agent coordination events
resource workflowTopic 'Microsoft.ServiceBus/namespaces/topics@2021-11-01' = {
  parent: serviceBusNamespace
  name: 'workflow-events'
  properties: {
    maxMessageSizeInKilobytes: 256
    defaultMessageTimeToLive: 'P1D' // 1 day
    maxSizeInMegabytes: 1024
    duplicateDetectionHistoryTimeWindow: 'PT10M' // 10 minutes
    requiresDuplicateDetection: true
    enablePartitioning: false
    supportOrdering: true
  }
}

// Audit topic for comprehensive logging
resource auditTopic 'Microsoft.ServiceBus/namespaces/topics@2021-11-01' = {
  parent: serviceBusNamespace
  name: 'audit-events'
  properties: {
    maxMessageSizeInKilobytes: 256
    defaultMessageTimeToLive: 'P7D' // 7 days
    maxSizeInMegabytes: 2048
    duplicateDetectionHistoryTimeWindow: 'PT10M'
    requiresDuplicateDetection: true
    enablePartitioning: true // Enable partitioning for high throughput
  }
}

// Exception topic for human escalation alerts
resource exceptionTopic 'Microsoft.ServiceBus/namespaces/topics@2021-11-01' = {
  parent: serviceBusNamespace
  name: 'exception-alerts'
  properties: {
    maxMessageSizeInKilobytes: 256
    defaultMessageTimeToLive: 'P1D' // 1 day
    maxSizeInMegabytes: 1024
    duplicateDetectionHistoryTimeWindow: 'PT10M'
    requiresDuplicateDetection: true
    enablePartitioning: false
    supportOrdering: true
  }
}

// Agent subscriptions with proper filters
resource emailIntakeSubscription 'Microsoft.ServiceBus/namespaces/topics/subscriptions@2021-11-01' = {
  parent: workflowTopic
  name: 'email-intake-agent'
  properties: {
    maxDeliveryCount: 3
    defaultMessageTimeToLive: 'P1D'
    lockDuration: 'PT5M'
    deadLetteringOnMessageExpiration: true
    deadLetteringOnFilterEvaluationExceptions: true
  }
}

resource loanContextSubscription 'Microsoft.ServiceBus/namespaces/topics/subscriptions@2021-11-01' = {
  parent: workflowTopic
  name: 'loan-context-agent'
  properties: {
    maxDeliveryCount: 3
    defaultMessageTimeToLive: 'P1D'
    lockDuration: 'PT5M'
    deadLetteringOnMessageExpiration: true
    deadLetteringOnFilterEvaluationExceptions: true
  }
}

resource rateQuoteSubscription 'Microsoft.ServiceBus/namespaces/topics/subscriptions@2021-11-01' = {
  parent: workflowTopic
  name: 'rate-quote-agent'
  properties: {
    maxDeliveryCount: 3
    defaultMessageTimeToLive: 'P1D'
    lockDuration: 'PT5M'
    deadLetteringOnMessageExpiration: true
    deadLetteringOnFilterEvaluationExceptions: true
  }
}

resource complianceSubscription 'Microsoft.ServiceBus/namespaces/topics/subscriptions@2021-11-01' = {
  parent: workflowTopic
  name: 'compliance-risk-agent'
  properties: {
    maxDeliveryCount: 3
    defaultMessageTimeToLive: 'P1D'
    lockDuration: 'PT5M' // Max allowed for Standard tier
    deadLetteringOnMessageExpiration: true
    deadLetteringOnFilterEvaluationExceptions: true
  }
}

resource lockConfirmationSubscription 'Microsoft.ServiceBus/namespaces/topics/subscriptions@2021-11-01' = {
  parent: workflowTopic
  name: 'lock-confirmation-agent'
  properties: {
    maxDeliveryCount: 3
    defaultMessageTimeToLive: 'P1D'
    lockDuration: 'PT5M'
    deadLetteringOnMessageExpiration: true
    deadLetteringOnFilterEvaluationExceptions: true
  }
}

// Audit and exception subscriptions
resource auditLoggingSubscription 'Microsoft.ServiceBus/namespaces/topics/subscriptions@2021-11-01' = {
  parent: auditTopic
  name: 'audit-logging-agent'
  properties: {
    maxDeliveryCount: 5
    defaultMessageTimeToLive: 'P7D'
    lockDuration: 'PT1M'
    deadLetteringOnMessageExpiration: true
    deadLetteringOnFilterEvaluationExceptions: true
  }
}

resource exceptionHandlerSubscription 'Microsoft.ServiceBus/namespaces/topics/subscriptions@2021-11-01' = {
  parent: exceptionTopic
  name: 'exception-handler-agent'
  properties: {
    maxDeliveryCount: 5
    defaultMessageTimeToLive: 'P1D'
    lockDuration: 'PT5M'
    deadLetteringOnMessageExpiration: true
    deadLetteringOnFilterEvaluationExceptions: true
  }
}

resource humanNotificationSubscription 'Microsoft.ServiceBus/namespaces/topics/subscriptions@2021-11-01' = {
  parent: exceptionTopic
  name: 'human-notifications'
  properties: {
    maxDeliveryCount: 10
    defaultMessageTimeToLive: 'P1D'
    lockDuration: 'PT30S'
    deadLetteringOnMessageExpiration: true
    deadLetteringOnFilterEvaluationExceptions: true
  }
}

// Assign Service Bus Data Owner role to the principal
resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  scope: serviceBusNamespace
  name: guid(serviceBusNamespace.id, principalId, '090c5cfd-751d-490a-894a-3ce6f1109419')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '090c5cfd-751d-490a-894a-3ce6f1109419') // Azure Service Bus Data Owner
    principalId: principalId
    principalType: 'User'
  }
}

output endpoint string = 'https://${serviceBusNamespace.name}.servicebus.windows.net'
output namespaceName string = serviceBusNamespace.name
output id string = serviceBusNamespace.id
