# Blog Writing Agentic System

This repository demonstrates a multi-agent blog writing system using **Semantic Kernel** communicating over the **Agent-to-Agent (A2A) protocol**. The system consists of three specialized agents that collaborate to create high-quality blog articles.

## 🏗️ Architecture

The system implements a distributed agent architecture where remote agents expose their capabilities through the A2A protocol, and a local coordinator orchestrates their collaboration.

### Remote Agents (Semantic Kernel with A2A Protocol)

1. **Critic Agent** (`critic/agent.py`)
   - URL: `http://localhost:8001`
   - Role: Reviews blog articles and provides constructive feedback
   - Focuses on structure, clarity, engagement, accuracy, and grammar
   - Uses Azure OpenAI with Semantic Kernel

2. **Writer Agent** (`writer/agent.py`)
   - URL: `http://localhost:8002`
   - Role: Creates blog articles based on given topics
   - Writes comprehensive articles with introduction, body, and conclusion
   - Uses Azure OpenAI with Semantic Kernel

### Local Coordinator Agent (Semantic Kernel)

3. **Blog Coordinator Agent** (`blogging_agent.py`)
   - URL: `http://localhost:8000`
   - Role: Orchestrates the blog writing process
   - Has a web UI for user interaction
   - Uses Semantic Kernel with two tools:
     - `write_blog`: Communicates with the writer agent
     - `review_blog`: Communicates with the critic agent
   - Workflow:
     1. Receives blog topic from user
     2. Asks writer to create initial draft
     3. Sends draft to critic for review
     4. Iterates with writer to improve based on feedback
     5. Delivers final polished article

## Project Structure

```
a2a/
├── critic/              # Critic agent (UV project)
│   ├── __main__.py     # A2A server startup script
│   ├── agent.py        # Semantic Kernel critic agent implementation
│   ├── agent_executor.py # A2A agent executor for critic
│   ├── pyproject.toml  # UV project config
│   ├── README.md       # Critic agent documentation
│   └── uv.lock         # UV lock file
├── writer/              # Writer agent (UV project)
│   ├── __main__.py     # A2A server startup script
│   ├── agent.py        # Semantic Kernel writer agent implementation
│   ├── agent_executor.py # A2A agent executor for writer
│   ├── pyproject.toml  # UV project config
│   ├── README.md       # Writer agent documentation
│   └── uv.lock         # UV lock file
├── blogging_agent.py    # Blog coordinator agent (FastAPI)
├── start_all.sh         # Script to start all agents
├── index.html           # Web UI for blog coordination
├── pyproject.toml       # Main project UV config
├── uv.lock              # Main project UV lock file
├── .env                 # Environment variables (Azure OpenAI config)
├── .env.example         # Example environment variables
└── README.md            # Project documentation
```

## Environment Variables

All agents use the same Azure OpenAI configuration from `.env`:

```env
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_API_VERSION="2024-12-01-preview"
```

Use `.env.example` as a template to create your `.env` file.

## Running the System

1. **Prerequisites**: Ensure you have UV package manager installed and Azure OpenAI credentials configured in `.env`
2. **Start all agents**: `bash start_all.sh` (or `./start_all.sh` on Unix systems)
3. **Access the web UI**: Navigate to `http://localhost:8000`
4. **Start writing**: Ask the system to write a blog about any topic

### Individual Agent Startup
- **Critic Agent**: `cd critic && uv run python __main__.py` (runs on port 8001)
- **Writer Agent**: `cd writer && uv run python __main__.py` (runs on port 8002)  
- **Blog Coordinator**: `uv run python blogging_agent.py` (runs on port 8000 with web UI)

## Development Guidelines

### When modifying agents:
- Each agent is its own UV project - respect project boundaries
- Each remote agent has an `agent.py` (Semantic Kernel implementation) and `agent_executor.py` (A2A protocol adapter)
- Remote agents are started via `__main__.py` which creates an A2A server with the agent executor
- The coordinator uses Semantic Kernel with custom tools (`BlogWritingTools` class) for A2A client communication
- All agents share the same Azure OpenAI configuration via environment variables loaded from `.env`

### Adding new features:
- To add new remote agents: Create a new UV project with `agent.py` (Semantic Kernel AI agent), `agent_executor.py` (A2A adapter), and `__main__.py` (server startup)
- To add new tools: Add kernel functions to `BlogWritingTools` class in `blogging_agent.py`
- To modify the workflow: Update the coordinator agent's instructions in `blogging_agent.py`

### Testing:
- Test remote agents individually by sending HTTP requests to their A2A endpoints
- Test the full system through the web UI
- Monitor logs for debugging (all agents log at INFO level)

### Common patterns:
- Remote agents are stateless - use context IDs for conversation tracking
- The coordinator maintains chat history per context
- A2A communication uses `SendMessageRequest` with proper message structure
- Error handling should be graceful - agents should continue operating if one fails
- Remote agents use structured response formats with Pydantic models (`ResponseFormat`)
- Each agent has specific instructions and roles defined in their Semantic Kernel configuration

### Dependencies and Technologies:
- **Semantic Kernel**: Core AI agent framework for all agents
- **A2A SDK**: Agent-to-Agent protocol implementation
- **FastAPI**: Web framework for the coordinator's HTTP API
- **httpx**: HTTP client for A2A communication
- **Azure OpenAI**: LLM service for all agents
- **UV**: Package manager for Python projects
- **Pydantic**: Data validation and structured responses
