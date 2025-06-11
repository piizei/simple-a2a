import os
import logging
import httpx
import asyncio
from typing import Dict, Any
from uuid import uuid4
from dotenv import load_dotenv

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from semantic_kernel.agents.chat_completion.chat_completion_agent import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Remote agent URLs
writer_url = 'http://localhost:8002'
critic_url = 'http://localhost:8001'

# Maintain chat history per context
chat_history_store: dict[str, ChatHistory] = {}

class BlogWritingTools:
    @kernel_function(
        description="Use the writer agent to create a blog article on a given topic",
        name="write_blog"
    )
    async def write_blog(self, topic: str, requirements: str = "") -> str:
        """Ask the writer agent to create a blog article"""
        async with httpx.AsyncClient(http2=True, timeout=httpx.Timeout(60.0)) as httpx_client:
            resolver = A2ACardResolver(httpx_client=httpx_client, base_url=writer_url)
            agent_card = await resolver.get_agent_card()

            client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)

            prompt = f"Write a blog article about: {topic}"
            if requirements:
                prompt += f"\n\nRequirements: {requirements}"

            request = SendMessageRequest(
                id=str(uuid4()),
                params=MessageSendParams(
                    message={
                        "messageId": uuid4().hex,
                        "role": "user",
                        "parts": [{"text": prompt}],
                        "contextId": str(uuid4()),
                    }
                )
            )
            response = await client.send_message(request)
            result = response.model_dump(mode='json', exclude_none=True)
            print(result)
            logger.info(f"Writer agent response received")

            return result["result"]["artifacts"][0]["parts"][0]["text"]

    @kernel_function(
        description="Use the critic agent to review and provide feedback on a blog article",
        name="review_blog"
    )
    async def review_blog(self, article: str) -> str:
        """Ask the critic agent to review a blog article"""
        async with httpx.AsyncClient(http2=True, timeout=httpx.Timeout(60.0)) as httpx_client:
            resolver = A2ACardResolver(httpx_client=httpx_client, base_url=critic_url)
            agent_card = await resolver.get_agent_card()

            client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)

            request = SendMessageRequest(
                id=str(uuid4()),
                params=MessageSendParams(
                    message={
                        "messageId": uuid4().hex,
                        "role": "user",
                        "parts": [{"text": f"Please review this blog article and provide feedback:\n\n{article}"}],
                        "contextId": str(uuid4()),
                    }
                )
            )
            response = await client.send_message(request)
            result = response.model_dump(mode='json', exclude_none=True)
            logger.info(f"Critic agent response received")

            return result["result"]["artifacts"][0]["parts"][0]["text"]

# Create the blog coordination agent
blog_coordinator_agent = ChatCompletionAgent(
    service=AzureChatCompletion(
        api_key=os.getenv('AZURE_OPENAI_API_KEY'),
        endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
        deployment_name=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME'),
        api_version="2024-12-01-preview",
    ),
    name="BlogCoordinator",
    instructions="""You are a blog writing coordinator. Your role is to help users create high-quality blog articles by:
    1. Using the writer agent to create initial drafts
    2. Using the critic agent to review and provide feedback
    3. Iterating with the writer to improve the article based on feedback
    4. Delivering a polished final article
    
    Always start by asking the writer to create a draft, then get feedback from the critic, and iterate as needed.""",
    plugins=[BlogWritingTools()]
)

@app.post("/chat")
async def chat(user_input: str = Form(...), context_id: str = Form("default")):
    logger.info(f"Received chat request: {user_input} with context ID: {context_id}")

    # Get or create ChatHistory for the context
    chat_history = chat_history_store.get(context_id)
    if chat_history is None:
        chat_history = ChatHistory(
            messages=[],
            system_message="You are a blog writing coordinator assistant. Help users create high-quality blog articles by coordinating between writer and critic agents."
        )
        chat_history_store[context_id] = chat_history
        logger.info(f"Created new ChatHistory for context ID: {context_id}")

    # Add user input to chat history
    chat_history.messages.append(ChatMessageContent(role="user", content=user_input))

    # Create a new thread from the chat history
    thread = ChatHistoryAgentThread(chat_history=chat_history, thread_id=str(uuid4()))

    # Get response from the agent
    response = await blog_coordinator_agent.get_response(message=user_input, thread=thread)

    # Add assistant response to chat history
    chat_history.messages.append(ChatMessageContent(role="assistant", content=response.content.content))

    logger.info(f"Blog coordinator response: {response.content.content}")

    return {"response": response.content.content}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        logger.error("index.html file not found. Please ensure it exists in the current directory.")
        return HTMLResponse(content="<h1>Error: index.html not found</h1>", status_code=404)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)