import logging

import click
import httpx
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, InMemoryPushNotifier
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from agent_executor import SemanticKernelWriterAgentExecutor
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv("../.env")


@click.command()
@click.option('--host', default='0.0.0.0')
@click.option('--port', default=8002)
def main(host, port):
    """Starts the Semantic Kernel Writer Agent server using A2A."""
    httpx_client = httpx.AsyncClient()
    request_handler = DefaultRequestHandler(
        agent_executor=SemanticKernelWriterAgentExecutor(),
        task_store=InMemoryTaskStore(),
        push_notifier=InMemoryPushNotifier(httpx_client),
    )

    server = A2AStarletteApplication(
        agent_card=get_agent_card(host, port), http_handler=request_handler
    )
    
    import uvicorn
    uvicorn.run(server.build(), host=host, port=port)


def get_agent_card(host: str, port: int):
    """Returns the Agent Card for the Semantic Kernel Writer Agent."""
    
    capabilities = AgentCapabilities(streaming=True)
    
    skill_write_blog = AgentSkill(
        id='write_blog',
        name='Write Blog',
        description=(
            'Creates comprehensive blog articles with introduction, body, and conclusion '
            'based on given topics. Writes engaging, well-structured content.'
        ),
        tags=['write', 'create', 'blog', 'article', 'content', 'semantic-kernel'],
        examples=[
            'Write a blog about artificial intelligence',
            'Create an article about sustainable living',
            'Write a comprehensive guide on remote work best practices',
        ],
    )

    agent_card = AgentCard(
        name='SK Writer Agent',
        description=(
            'Semantic Kernel-based blog writer agent that creates engaging, well-structured '
            'blog articles on various topics with proper formatting and clear organization.'
        ),
        url=f'http://localhost:{port}/',
        version='1.0.0',
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        capabilities=capabilities,
        skills=[skill_write_blog],
    )

    return agent_card


if __name__ == '__main__':
    main()
