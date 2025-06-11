import logging

import click
import httpx
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, InMemoryPushNotifier
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from agent_executor import SemanticKernelCriticAgentExecutor
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv("../.env")


@click.command()
@click.option('--host', default='0.0.0.0')
@click.option('--port', default=8001)
def main(host, port):
    """Starts the Semantic Kernel Critic Agent server using A2A."""
    httpx_client = httpx.AsyncClient()
    request_handler = DefaultRequestHandler(
        agent_executor=SemanticKernelCriticAgentExecutor(),
        task_store=InMemoryTaskStore(),
        push_notifier=InMemoryPushNotifier(httpx_client),
    )

    server = A2AStarletteApplication(
        agent_card=get_agent_card(host, port), http_handler=request_handler
    )
    
    import uvicorn
    uvicorn.run(server.build(), host=host, port=port)


def get_agent_card(host: str, port: int):
    """Returns the Agent Card for the Semantic Kernel Critic Agent."""
    
    capabilities = AgentCapabilities(streaming=True)
    
    skill_review_blog = AgentSkill(
        id='review_blog',
        name='Review Blog',
        description=(
            'Reviews blog articles and provides constructive feedback on structure, clarity, '
            'engagement, accuracy, and grammar. Provides specific suggestions for improvement.'
        ),
        tags=['review', 'feedback', 'blog', 'writing', 'semantic-kernel'],
        examples=[
            'Review this blog article about machine learning',
            'Please provide feedback on my blog post about travel tips',
            'Check this article for grammar and clarity issues',
        ],
    )

    agent_card = AgentCard(
        name='SK Critic Agent',
        description=(
            'Semantic Kernel-based blog critic agent that provides professional editorial feedback '
            'on blog articles, focusing on structure, clarity, engagement, and overall quality.'
        ),
        url=f'http://localhost:{port}/',
        version='1.0.0',
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        capabilities=capabilities,
        skills=[skill_review_blog],
    )

    return agent_card


if __name__ == '__main__':
    main()
