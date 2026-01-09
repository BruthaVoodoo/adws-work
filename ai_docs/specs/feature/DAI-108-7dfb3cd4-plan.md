# Feature: Create OpenCodeHTTPClient class with session management

## Feature Description
This feature implements a robust HTTP client class specifically designed to manage OpenCode sessions within the Strands Agents framework. The OpenCodeHTTPClient provides session lifecycle management, authentication handling, and reliable communication with OpenCode HTTP servers. This client will enable agents to interact with OpenCode services through managed sessions, ensuring proper connection handling, authentication, and graceful error management.

## Agent Capability
This feature adds HTTP session management capability to the agent, allowing it to:
- Establish authenticated sessions with OpenCode servers
- Maintain session state across multiple requests
- Handle session lifecycle (creation, management, cleanup)
- Provide reliable error handling for authentication and connection issues
- Enable secure communication with external OpenCode services

## Problem Statement
Currently, there is no standardized way for agents to interact with OpenCode HTTP servers. Without proper session management, agents cannot maintain persistent connections, handle authentication properly, or ensure reliable communication with OpenCode services. This creates barriers for agents that need to integrate with OpenCode functionality and limits their ability to provide comprehensive services.

## Solution Statement
The OpenCodeHTTPClient class will be implemented as a core component within the Strands Agents framework, providing a standardized interface for OpenCode server communication. It will integrate with Amazon AgentCore deployment patterns and follow the framework's conventions for tool implementation. The solution includes proper session management, authentication handling, connection pooling, and comprehensive error handling to ensure reliable operation in production environments.

## Strands Agents Integration
This feature integrates with the Strands framework through:
- Handler implementation in the handlers/ directory for HTTP client operations
- Tool definition for agent access to OpenCode services
- Integration with the agent's configuration system for server URLs and credentials
- Compatibility with Amazon AgentCore deployment patterns
- Following the framework's logging and error handling conventions
- Support for async operations within the agent execution context

## Relevant Files
Use these files to implement the feature:

- `agent/__init__.py` - Agent initialization and core framework setup
- `agent/core.py` - Main agent implementation with tool registration
- `handlers/__init__.py` - Handler module initialization
- `handlers/opencode_client.py` - OpenCodeHTTPClient implementation and session management
- `config/agent_config.py` - Agent configuration including OpenCode server settings
- `config/__init__.py` - Configuration module initialization
- `tests/__init__.py` - Test module initialization
- `tests/test_opencode_client.py` - Unit tests for OpenCodeHTTPClient functionality
- `tests/test_integration.py` - Integration tests for agent framework integration

### New Files

- `pyproject.toml` - Project configuration and dependencies
- `README.md` - Project documentation and setup instructions
- `requirements.txt` - Python dependencies
- `.env.example` - Example environment configuration
- `agent/__init__.py` - Agent module initialization
- `agent/core.py` - Main agent implementation
- `handlers/__init__.py` - Handler module initialization
- `handlers/opencode_client.py` - OpenCodeHTTPClient implementation
- `config/__init__.py` - Configuration module
- `config/agent_config.py` - Agent configuration settings
- `tests/__init__.py` - Test module initialization
- `tests/test_opencode_client.py` - OpenCodeHTTPClient unit tests
- `tests/test_integration.py` - Integration tests
- `tests/conftest.py` - Pytest configuration and fixtures

## Implementation Plan
### Phase 1: Foundation
Set up the basic Strands Agents project structure with proper Python packaging, configuration management, and testing infrastructure. This includes creating the directory structure, dependency management, and core framework components.

### Phase 2: Core Implementation
Implement the OpenCodeHTTPClient class with session management, authentication handling, and HTTP communication capabilities. This includes creating the main client class, session lifecycle methods, and error handling.

### Phase 3: Integration
Integrate the OpenCodeHTTPClient with the Strands Agents framework by creating handlers, tools, and configuration systems. This ensures the client can be used by agents and follows framework conventions.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Project Setup and Configuration

- Create project configuration file (pyproject.toml) with dependencies including httpx, pydantic, and pytest
- Create requirements.txt for pip-based installations
- Create .env.example with OpenCode server configuration templates
- Create README.md with project overview and setup instructions

### Directory Structure Creation

- Create agent/ directory and __init__.py for the main agent module
- Create handlers/ directory and __init__.py for handler implementations
- Create config/ directory and __init__.py for configuration management
- Create tests/ directory and __init__.py for testing infrastructure

### Configuration System Implementation

- Implement config/agent_config.py with Pydantic models for OpenCode server settings
- Create configuration classes for authentication, server URLs, and client settings
- Add environment variable support for configuration management
- Create validation for required configuration parameters

### Core Agent Framework

- Implement agent/core.py with basic Strands Agents framework structure
- Create agent initialization and tool registration system
- Add logging configuration and error handling framework
- Implement agent lifecycle management

### OpenCodeHTTPClient Implementation

- Create handlers/opencode_client.py with the main OpenCodeHTTPClient class
- Implement session creation with authentication handling
- Add session management methods (create_session, close_session, get_session_info)
- Implement HTTP client with proper connection pooling and timeout handling
- Add comprehensive error handling for authentication and connection failures

### Testing Infrastructure

- Create tests/conftest.py with pytest fixtures for testing
- Implement mock OpenCode server for testing purposes
- Create test data and helper functions for test scenarios

### Unit Tests for OpenCodeHTTPClient

- Implement tests/test_opencode_client.py with comprehensive unit tests
- Test session creation with valid and invalid credentials
- Test session lifecycle management and cleanup
- Test error handling for various failure scenarios
- Test HTTP communication and response handling

### Integration Tests

- Create tests/test_integration.py for end-to-end testing
- Test agent framework integration with OpenCodeHTTPClient
- Test configuration loading and validation
- Test tool registration and usage within agent context

### Documentation and Examples

- Update README.md with usage examples and API documentation
- Add docstrings to all classes and methods
- Create example scripts demonstrating OpenCodeHTTPClient usage

## Testing Strategy
### Unit Tests
- Test OpenCodeHTTPClient class initialization and configuration
- Test session creation with various authentication scenarios
- Test session management operations (create, get info, close)
- Test HTTP communication methods and response handling
- Test error handling for network failures, authentication errors, and invalid responses
- Test connection pooling and timeout behavior
- Mock all external HTTP calls to ensure isolated testing

### Integration Tests
- Test integration with Strands Agents framework
- Test configuration loading from environment variables and files
- Test agent tool registration and usage
- Test end-to-end workflow from agent initialization to OpenCode communication
- Test with actual OpenCode server (if available) for real-world validation

### Edge Cases
- Invalid server URLs and unreachable endpoints
- Network timeouts and connection failures
- Authentication with expired or invalid credentials
- Session creation when server is at capacity
- Concurrent session management operations
- Large response handling and memory management
- SSL/TLS certificate validation failures

## Acceptance Criteria
- OpenCodeHTTPClient can be instantiated with server URL and creates a unique session ID
- Session creation works with valid credentials and raises authentication errors for invalid credentials
- close_session() properly closes and cleans up sessions
- Client handles network errors gracefully with meaningful error messages
- Client integrates seamlessly with Strands Agents framework
- All unit tests pass with 100% coverage on core functionality
- Integration tests validate end-to-end functionality
- Configuration system supports environment variables and file-based configuration
- Client supports concurrent operations and proper connection pooling
- Documentation includes clear usage examples and API reference

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `pytest tests/ -v` - Run all agent tests to validate the feature works with zero regressions
- `pytest tests/test_opencode_client.py -v` - Run OpenCodeHTTPClient unit tests
- `pytest tests/test_integration.py -v` - Run integration tests
- `python -m pytest tests/ --cov=handlers --cov=agent --cov=config` - Run tests with coverage reporting
- `python -c "from handlers.opencode_client import OpenCodeHTTPClient; print('Import successful')"` - Validate imports work correctly
- `python -c "from agent.core import Agent; agent = Agent(); print('Agent initialization successful')"` - Validate agent framework works
- `ruff check .` - Run code quality checks
- `mypy handlers/ agent/ config/` - Run type checking on all modules

## Notes
- Use httpx for async HTTP client capabilities and better performance
- Implement proper connection pooling to handle multiple concurrent sessions
- Use Pydantic for configuration validation and type safety
- Follow Python logging best practices for debugging and monitoring
- Consider implementing retry logic with exponential backoff for network failures
- Use uv add for dependency management: `uv add httpx pydantic pytest pytest-cov ruff mypy`
- The OpenCodeHTTPClient should be thread-safe for use in multi-agent scenarios
- Consider implementing session persistence for long-running agents
- Add metrics collection for session creation, duration, and failure rates
- Future consideration: Add support for WebSocket connections for real-time communication