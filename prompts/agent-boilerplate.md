  # Strands Agent Boilerplate Generator
     
  Create a Python-based Strands AI agent project with the following specifications:
  
  ## CORE REQUIREMENTS
  - **Language**: Python 3.10+
  - **Framework**: Strands Agents SDK
  - **Model**: AWS Bedrock (Claude Sonnet recommended)
  - **Structure**: Production-ready directory layout
  - **Complexity**: Intermediate (assumes familiarity with agents)
  
  ## PROJECT INFORMATION
  Please provide:
  1. **Agent Name** (e.g., "Research Assistant", "Data Analyzer")
  2. **Agent Description** (1-2 sentence purpose)
  3. **Deployment Type** (select one or more):
    - `cli` - Interactive CLI with streaming output
    - `agentcore` - Amazon Bedrock AgentCore (FastAPI with /invocations & /ping)
    - `lambda` - AWS Lambda function handler
    - `all` - Include all three deployment options
  4. **Features** (select all that apply, or leave blank for none):
    - `memory` - Add memory/knowledge base support
    - `logging` - Add comprehensive logging and observability
    - `guardrails` - Add Bedrock Guardrails integration
    - `mcp` - Add MCP (Model Context Protocol) server template
  5. **Tool Requirements** (select as needed):
    - `web_search` - Web search capability
    - `file_operations` - File read/write operations
    - `api_calls` - HTTP API calls
    - `aws_services` - AWS service integrations
    - `custom` - Just provide placeholder for custom tools
  6. **Optional Preferences**:
    - Include .env template? (yes/no)
    - Include unit tests? (yes/no)
    - Include deployment script? (yes/no)
    - Include documentation (README)? (yes/no)
  
  ## PROJECT STRUCTURE TO GENERATE

  ```
  {agent_name}/
  ├── src/
  │   ├── __init__.py
  │   ├── agent.py                    # Main agent initialization
  │   ├── prompts.py                  # System prompts and configurations
  │   ├── tools/
  │   │   ├── __init__.py
  │   │   └── {tool_name}.py          # Individual tool implementations
  │   ├── config.py                   # Configuration management
  │   └── utils.py                    # Utility functions
  ├── deployments/
  │   ├── cli.py                      # CLI deployment (if selected)
  │   ├── agentcore.py                # AgentCore FastAPI deployment (if selected)
  │   ├── Dockerfile                  # ARM64 container for AgentCore (if selected)
  │   └── lambda_handler.py           # Lambda handler (if selected)
  ├── tests/
  │   ├── __init__.py
  │   ├── test_agent.py
  │   └── test_tools.py
  ├── .env.example                    # Environment variables template
  ├── requirements.txt                # Python dependencies
  ├── pyproject.toml                  # Project metadata
  ├── README.md                       # Documentation
  ├── .gitignore
  └── Makefile                        # Common development commands
  ```

  
  ## CODE STANDARDS
  - Use type hints throughout
  - Follows PEP 8 style guide
  - Docstrings on all functions and classes
  - Error handling with try/except blocks
  - Logging for debugging and monitoring
  - Environment variables for configuration
  
  ## DEPENDENCIES TO INCLUDE
  - strands-agents (latest)
  - strands-agents-tools (for common tools)
  - python-dotenv (environment configuration)
  - fastapi + uvicorn (for agentcore deployment)
  - boto3 (AWS service interactions)
  - pydantic (validation)
  - pytest (if tests selected)
  - aws-opentelemetry-distro (for AgentCore observability)
  
  ## AGENT INITIALIZATION TEMPLATE
  The generated agent should include:
  - BedrockModel configuration with model_id
  - Agent initialization with system_prompt
  - Tools list with placeholder implementations
  - Model/tool configuration from environment variables
  - Proper error handling and logging setup
  
  ## DEPLOYMENT SPECIFICS
  
  ### CLI Deployment
  - Interactive loop with user input/agent response
  - Streaming output support
  - Graceful exit handling (Ctrl+C, "exit" command)
  - Optional rich formatting for tools display

  ### AgentCore Deployment (Custom Option B)
  - FastAPI server with /invocations POST endpoint (required by AgentCore Runtime)
  - POST /invocations accepts { "input": { "prompt": "..." } }
  - GET /ping health check endpoint (required by AgentCore Runtime)
  - Response format: { "output": { "message": "...", "timestamp": "...", "model": "..." } }
  - Error handling with proper HTTP status codes
  - ARM64 Docker container (linux/arm64) for ECR deployment
  - Environment variables for AWS credentials and configuration

  ### Lambda Deployment
  - handler(event, context) signature
  - Parse input from event['body']
  - Return properly formatted Lambda response
  - Minimal dependencies for package size
  
  ## PLACEHOLDER TOOLS STRUCTURE
  Each tool should include:
  ```python
  @tool
  def tool_name(param: str) -> str:
      """
      Tool description for LLM understanding.
      
      Args:
          param: Parameter description
      
      Returns:
          Result description
      """
      # Implementation or placeholder
      pass
  ```

  ## AGENTCORE SPECIFIC REQUIREMENTS
  When AgentCore deployment is selected, include:
  - **Dockerfile**: ARM64-based (linux/arm64) using Python base image suitable for AgentCore
  - **Port**: Application must run on port 8080
  - **Endpoints**: Both /invocations POST and /ping GET are MANDATORY
  - **Request Format**: { "input": { "prompt": "..." } } for /invocations
  - **Response Format**: { "output": { "message": "...", "timestamp": "...", "model": "..." } }
  - **Error Handling**: Return HTTP 400/500 with detail messages for validation/processing failures
  - **Observability**: Include opentelemetry-instrument in startup command for CloudWatch integration
  - **Session Isolation**: Each invocation is independent (no session state in handler)
  - **Deployment Script**: Python script using boto3 to:
    - Create ECR repository if needed
    - Build and push Docker image to ECR
    - Deploy AgentRuntime using CreateAgentRuntime API
    - Return Agent Runtime ARN for invocation

  ## AGENTCORE DEPLOYMENT WORKFLOW
  1. Generate project with agentcore option
  2. Test locally: `python deployments/agentcore.py` or `docker run locally`
  3. Build container: `docker buildx build --platform linux/arm64 -t my-agent:arm64`
  4. Push to ECR: `aws ecr create-repository` then `docker push`
  5. Deploy: Run deployment script with AgentRuntime name and ECR image URI
  6. Invoke: Use boto3 client invoke_agent_runtime with ARN and sessionId (33+ chars)
  7. Monitor: View traces and metrics in CloudWatch GenAI Observability page

  ## WHAT NOT TO INCLUDE
  - Actual API keys or credentials in code
  - Complex business logic (keep it template-like)
  - Multiple agent patterns by default (keep it single agent)
  - Database migrations or data schema
  - Extensive examples or sample data
  - Session-based state management in AgentCore deployments (stateless by design)

  ## QUALITY CHECKLIST
  - All files include proper imports and type hints
  - All functions have docstrings
  - Error handling for common failures
  - Logging configured and used appropriately
  - README explains how to run each deployment type, including AgentCore-specific instructions
  - README includes AgentCore deployment commands (ECR, Docker buildx, boto3 deployment)
  - Dockerfile properly configured for ARM64 with correct base image
  - .gitignore prevents credential/cache leakage
  - Code is runnable with minimal setup
  - AgentCore /invocations and /ping endpoints work without authentication
  - Response payloads match AgentCore expected format