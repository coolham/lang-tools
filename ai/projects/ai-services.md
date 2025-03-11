AI Services Architecture
Overview
The lang-tools application uses a modular AI service architecture that enables communication with various LLM providers through a unified interface. This design allows for easy extension to new providers while maintaining consistent behavior across the application.

Core Architecture
Base Components
AIService: Abstract base class defining the common interface for all AI providers
Message: Data class encapsulating conversation messages with role and content attributes
ConfigManager: Central configuration system for provider settings and credentials
Design Principles
Provider-agnostic interfaces for application components
Configuration-driven instantiation and behavior
Consistent error handling and logging patterns
Support for both streaming and non-streaming responses
Available Services
OpenAIService
Connects to OpenAI's API for GPT models (3.5-Turbo, 4, etc.)
Supports temperature and other generation parameters
Handles token counting and context management
Compatible with OpenAI API v1.0+ typing system
GrokService
Integrates with X.AI's Grok API
Currently supports the Grok-2 model
Uses similar parameter structure to OpenAI for consistency
Handles X.AI-specific authentication and API patterns
DeepseekService
Provides access to Deepseek's language models
Maintains compatible interface with other services
Supports Deepseek-specific features while preserving common patterns
Key Features
Provider Management
Support for multiple providers per service type
Provider selection through configuration or explicit parameters
Default provider fallback mechanism
Provider-specific settings (API keys, base URLs)
Network Configuration
Global and provider-specific proxy support
Intelligent handling of HTTP/HTTPS proxy requirements
Connection timeout and retry policies
SSL verification options for debugging
Response Handling
Unified format for responses across providers
Streaming support with consistent chunking behavior
Error normalization across different API error formats
Response data mapping to common structures
Common Usage Patterns
Basic Communication
Initialize the appropriate service with ConfigManager
Create Message objects for the conversation
Call send_message() to get a response
Process the structured response data
Streaming Interaction
Configure the service for streaming mode
Call send_message() with stream=True
Iterate through response chunks
Incrementally process content as it arrives
Provider Selection
Services can be instantiated with specific provider names
Default providers are configured in the configuration file
Multiple instances with different providers can be used simultaneously
Error Handling
Connection issues are logged and propagated with context
Authentication and authorization errors include troubleshooting info
Rate limiting triggers appropriate logging and retry behavior
Timeouts include information about request duration
Configuration Structure
Hierarchical JSON configuration for all services
Provider-specific sections for credentials and settings
Global proxy and network settings
Feature flags for experimental capabilities
Extension Points
The architecture is designed for easy extension:

New providers can be added by implementing the AIService interface
Additional parameters can be passed through the kwargs system
Response processors can be added to normalize new provider formats