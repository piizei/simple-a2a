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
service_id = "critic_service"


class ResponseFormat(BaseModel):
    """Response format for the critic agent."""
    status: Literal['input_required', 'completed', 'error'] = 'input_required'
    message: str


class SemanticKernelCriticAgent:
    """Semantic Kernel-based agent for reviewing blog articles."""
    
    def __init__(self):
        # Configure Azure OpenAI service
        chat_service = AzureChatCompletion(
            service_id=service_id,
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key=api_key,
        )
        
        # Create the critic agent
        self.agent = ChatCompletionAgent(
            service=chat_service,
            name='BlogCriticAgent',
            instructions=(
                'You are a professional blog editor and critic. Your role is to review blog articles '
                'and provide constructive feedback. Focus on: structure, clarity, engagement, accuracy, '
                'grammar, and overall quality. If an article is well-written, acknowledge its strengths. '
                'Always provide specific, actionable suggestions for improvement.\n\n'
                'When reviewing, structure your feedback as follows:\n'
                '1. Overall impression\n'
                '2. Strengths of the article\n'
                '3. Areas for improvement\n'
                '4. Specific suggestions\n'
                '5. Summary recommendation\n\n'
                'Always respond in a constructive and encouraging tone.'
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
        """Handle synchronous review requests."""
        # Get agent response
        response = await self.agent.get_response(messages=user_input)
        return self._get_agent_response(response.message)
    
    async def stream(
        self,
        user_input: str,
        session_id: str,
    ) -> AsyncIterable[dict[str, Any]]:
        """Handle streaming review requests."""
        chunks: list[StreamingChatMessageContent] = []
        text_started = False
        
        async for chunk in self.agent.invoke_stream(messages=user_input):
            if any(isinstance(i, StreamingTextContent) for i in chunk.items):
                if not text_started:
                    yield {
                        'is_task_complete': False,
                        'require_user_input': False,
                        'content': 'Analyzing the blog article...',
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
            'content': 'Unable to process the review request. Please try again.',
        }
