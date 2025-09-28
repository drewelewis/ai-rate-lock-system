"""
Azure Configuration Management
Handles environment-specific Azure service connections
"""
import os
from typing import Tuple


class AzureConfig:
    """Manages Azure service configurations based on environment"""
    
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'development').lower()
        
    def get_servicebus_connection(self) -> str:
        """Get Service Bus connection string based on environment"""
        if self.environment == 'production':
            return os.getenv('AZURE_SERVICEBUS_CONNECTION_STRING_PROD')
        else:
            return os.getenv('AZURE_SERVICEBUS_CONNECTION_STRING_DEV')
    
    def get_servicebus_namespace(self) -> str:
        """Get Service Bus namespace based on environment"""
        if self.environment == 'production':
            return os.getenv('AZURE_SERVICEBUS_NAMESPACE_PROD')
        else:
            return os.getenv('AZURE_SERVICEBUS_NAMESPACE_DEV')
    
    def get_cosmosdb_connection(self) -> str:
        """Get Cosmos DB connection string based on environment"""
        if self.environment == 'production':
            return os.getenv('AZURE_COSMOSDB_CONNECTION_STRING_PROD')
        else:
            return os.getenv('AZURE_COSMOSDB_CONNECTION_STRING_DEV')
    
    def get_cosmosdb_database(self) -> str:
        """Get Cosmos DB database name based on environment"""
        if self.environment == 'production':
            return os.getenv('AZURE_COSMOSDB_DATABASE_NAME_PROD')
        else:
            return os.getenv('AZURE_COSMOSDB_DATABASE_NAME_DEV')
    
    def get_redis_config(self) -> Tuple[str, int, int]:
        """Get Redis configuration (host, port, db)"""
        host = os.getenv('REDIS_HOST', 'localhost')
        port = int(os.getenv('REDIS_PORT', 6379))
        db = int(os.getenv('REDIS_DB', 0))
        return host, port, db
    
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment == 'development'
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment == 'production'


# Global instance
azure_config = AzureConfig()