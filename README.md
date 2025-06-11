# Blog Writing Agentic System

This repository demonstrates a multi-agent blog writing system using  **Semantic Kernel** communicating over the **Agent-to-Agent (A2A) protocol**. The system consists of three specialized agents that collaborate to create high-quality blog articles.


##
TL;DR
```bash
./start_all.sh
```
Then http://localhost:8000

## 🏗️ Architecture

The system implements a distributed agent architecture where remote agents expose their capabilities through the A2A protocol, and a local coordinator orchestrates their collaboration.

### Remote Agents (Semantic Kernel with A2A Protocol)

1. **Critic Agent** (`critic/agent.py`)
   - **URL**: `http://localhost:8001`
   - **Role**: Reviews blog articles and provides constructive feedback
   - **Focus**: Structure, clarity, engagement, accuracy, and grammar
   - **Technology**: Semantic Kernel + Azure OpenAI

2. **Writer Agent** (`writer/agent.py`)
   - **URL**: `http://localhost:8002`
   - **Role**: Creates blog articles based on given topics
   - **Output**: Comprehensive articles with introduction, body, and conclusion
   - **Technology**: Semantic Kernel + Azure OpenAI

### Local Coordinator Agent (Semantic Kernel)

3. **Blog Coordinator Agent** (`blogging_agent.py`)
   - **URL**: `http://localhost:8000`
   - **Role**: Orchestrates the entire blog writing process
   - **Interface**: Web UI for user interaction
   - **Technology**: Semantic Kernel with A2A client tools
   - **Workflow**:
     1. Receives blog topic from user
     2. Requests initial draft from writer agent
     3. Sends draft to critic agent for review
     4. Iterates with writer to improve based on feedback
     5. Delivers final polished article


## 🚀 Setup and Installation

### Prerequisites

- Python 3.10 or higher
- [UV package manager](https://docs.astral.sh/uv/) 
- Azure OpenAI account with API access

### 1. Clone the Repository

```bash
git clone https://github.com/piizei/simple-a2a
cd simple-a2a
```

### 2. Create Environment Variables

Copy `.env.example` to  `.env` file in the root directory with your Azure OpenAI configuration:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key
```

**Note**: All agents share the same Azure OpenAI configuration from this `.env` file.

### 3. Install Dependencies

Using UV (recommended):
```bash
uv sync
```


### 4. Install Dependencies for Each Agent

The critic and writer agents are separate UV projects:

```bash
# Install critic agent dependencies
cd critic
uv sync
cd ..

# Install writer agent dependencies
cd writer
uv sync
cd ..
```

## 🎯 Running the System

### Option 1: Start All Agents at Once

```bash
# Linux/macOS
./start_all.sh

# Windows (using Git Bash or WSL)
bash start_all.sh
```

### Option 2: Start Agents Individually

```bash
# Terminal 1: Start Critic Agent
cd critic
uv run python __main__.py

# Terminal 2: Start Writer Agent
cd writer
uv run python __main__.py

# Terminal 3: Start Blog Coordinator
uv run python blogging_agent.py
```

### Access the Web UI

Once all agents are running, open your browser and navigate to:
```
http://localhost:8000
```

## 💡 Usage

1. **Access the Web UI** at `http://localhost:8000`
2. **Enter a blog topic** in the chat interface
3. **Watch the agents collaborate**:
   - The coordinator asks the writer to create an initial draft
   - The critic reviews the draft and provides feedback
   - The writer iterates based on the feedback
   - The process continues until a polished article is ready
4. **Receive your final blog article**

### Example Prompts

- "Write a blog about the future of artificial intelligence"
- "Create an article about sustainable living practices"
- "Write a comprehensive guide on remote work productivity"
- "Create a blog post about the benefits of meditation"

## 📋 Troubleshooting

### Common Issues

1. **Agents not starting**: Check that all dependencies are installed and ports are available
2. **Azure OpenAI errors**: Verify your `.env` configuration and API key validity
3. **A2A communication failures**: Ensure all agents are running and accessible on their respective ports
4. **Web UI not loading**: Check if `index.html` exists and the coordinator agent is running

### Logs

All agents log at INFO level. Check the console output for detailed information about:
- Agent startup and initialization
- A2A protocol communications
- Azure OpenAI API calls
- Error messages and stack traces

## 📄 License

MIT
