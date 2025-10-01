---
applyTo: '**'
---

# AI Rate Lock System - GitHub Copilot Instructions

## Project Context
This is an AI-powered mortgage rate lock processing system built with Python, Azure services, and Semantic Kernel. The system uses multi-agent architecture to autonomously process rate lock requests through various stages from email intake to lock confirmation.

## Terminal and Shell Preferences - CRITICAL
- **ALWAYS use Windows Command Prompt (cmd.exe) for ALL terminal operations**
- **NEVER use PowerShell** - if PowerShell spawns, this is an error
- Generate terminal commands using cmd syntax only, not PowerShell syntax
- Use cmd.exe commands: `dir`, `cd`, `type`, `copy`, etc.
- Avoid PowerShell-specific commands like `Get-*`, `Set-*`, etc.
- VS Code is configured to use cmd as the default terminal via `.vscode/settings.json`
- When running Python commands, always use the full path: `C:\gitrepos\ai-rate-lock-system\.venv\Scripts\python.exe`

## Azure Infrastructure Guidelines
- Use Infrastructure as Code (Bicep) for all Azure resource deployments
- For Service Bus managed identity connections, use ARM templates when Bicep limitations exist
- Follow the declarative approach - avoid post-deployment scripts when possible
- All Azure resources should use managed identities for authentication
- Follow Option 2 implementation pattern (full declarative) as documented

## Python Development Standards
- Use virtual environment (.venv) for Python package management
- Follow async/await patterns for I/O operations
- Use proper logging throughout the application
- Implement proper error handling and exception management
- Follow PEP 8 style guidelines

## Multi-Agent System Architecture
- Each agent should be autonomous and stateless where possible
- Use Semantic Kernel for AI-powered decision making
- Implement proper memory management for agent context
- Follow the established agent communication patterns via Service Bus
- Ensure proper audit logging for all agent actions

## Data Storage Patterns
- Use Cosmos DB for primary rate lock record storage
- Use Service Bus for inter-agent communication
- Implement proper data models for loan lock entities
- Follow the established JSON schema for rate lock records

## Security and Compliance
- All API connections must use managed identity authentication
- Implement proper audit trails for compliance requirements
- Ensure sensitive data is properly handled and encrypted
- Follow financial services security best practices

## Testing and Validation
- Write unit tests for all agent functionality
- Test Service Bus message processing end-to-end
- Validate managed identity authentication works correctly
- Test the complete workflow from email intake to lock confirmation

## Documentation Standards
- Keep README.md updated with current setup instructions
- Document any architectural decisions and trade-offs
- Maintain clear API documentation for external integrations
- Update deployment documentation when infrastructure changes