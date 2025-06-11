import logging
import os
from typing import TYPE_CHECKING, Any, Literal
from collections.abc import AsyncIterable

from dotenv import load_dotenv
from pydantic import BaseModel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.contents import (
    StreamingChatMessageContent,
    StreamingTextContent,
)
from semantic_kernel.functions import KernelArguments

if TYPE_CHECKING:
    from semantic_kernel.contents import ChatMessageContent

logger = logging.getLogger(__name__)

# Load environment variables from parent directory
load_dotenv("../.env")

# Azure OpenAI configuration
deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
api_key = os.getenv('AZURE_OPENAI_API_KEY')
service_id = "writer_service"


class ResponseFormat(BaseModel):
    """Response format for the writer agent."""
    status: Literal['input_required', 'completed', 'error'] = 'input_required'
    message: str


class SemanticKernelWriterAgent:
    """Semantic Kernel-based agent for writing blog articles."""
    
    def __init__(self):
        # Configure Azure OpenAI service
        chat_service = AzureChatCompletion(
            service_id=service_id,
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key=api_key,
        )
        
        # Create the writer agent
        self.agent = ChatCompletionAgent(
            service=chat_service,
            name='BlogWriterAgent',
            instructions=(
                'You are a professional blog writer. You create engaging, well-structured blog articles '
                'on various topics. You are open to feedback and willing to revise your work to improve '
                'quality. When given a topic, write a comprehensive article with a clear introduction, '
                'body, and conclusion.\n\n'
                'Structure your articles as follows:\n'
                '1. Engaging title\n'
                '2. Introduction that hooks the reader\n'
                '3. Well-organized body with clear sections\n'
                '4. Compelling conclusion with key takeaways\n'
                '5. Proper formatting with headers and paragraphs\n\n'
                'Always write in a clear, engaging, and informative style.'
            ),
            arguments=KernelArguments(
                settings=OpenAIChatPromptExecutionSettings(
                    response_format=ResponseFormat,
                )
            ),
        )
        
        # Store session data
        self.sessions: dict[str, Any] = {}
    
    async def invoke(self, user_input: str, session_id: str) -> dict[str, Any]:
        """Handle synchronous writing requests."""
        # Get agent response
        response = await self.agent.get_response(messages=user_input)
        return self._get_agent_response(response.message)
    
    async def stream(
        self,
        user_input: str,
        session_id: str,
    ) -> AsyncIterable[dict[str, Any]]:
        """Handle streaming writing requests."""
        chunks: list[StreamingChatMessageContent] = []
        text_started = False
        
        async for chunk in self.agent.invoke_stream(messages=user_input):
            if any(isinstance(i, StreamingTextContent) for i in chunk.items):
                if not text_started:
                    yield {
                        'is_task_complete': False,
                        'require_user_input': False,
                        'content': 'Writing your blog article...',
                    }
                    text_started = True
                chunks.append(chunk.message)
        
        if chunks:
            yield self._get_agent_response(sum(chunks[1:], chunks[0]))
    
    def _get_agent_response(self, message: 'ChatMessageContent') -> dict[str, Any]:
        """Extract structured response from agent's message."""
        try:
            structured_response = ResponseFormat.model_validate_json(
                message.content
            )
            
            response_map = {
                'input_required': {
                    'is_task_complete': False,
                    'require_user_input': True,
                },
                'error': {
                    'is_task_complete': False,
                    'require_user_input': True,
                },
                'completed': {
                    'is_task_complete': True,
                    'require_user_input': False,
                },
            }
            
            response = response_map.get(structured_response.status)
            if response:
                return {**response, 'content': structured_response.message}
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
        
        return {
            'is_task_complete': False,
            'require_user_input': True,
            'content': 'Unable to process the writing request. Please try again.',
        }