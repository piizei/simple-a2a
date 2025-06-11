import logging
import asyncio  # added for scheduling events
import inspect  # for checking coroutine return

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from a2a.utils import (
    new_agent_text_message,
    new_task,
    new_text_artifact,
)
from agent import SemanticKernelWriterAgent


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SemanticKernelWriterAgentExecutor(AgentExecutor):
    """SemanticKernelWriterAgent Executor"""

    def __init__(self):
        self.agent = SemanticKernelWriterAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        query = context.get_user_input()
        task = context.current_task
        if not task:
            if context.message:
                task = new_task(context.message)
                # submit new task
                await event_queue.enqueue_event(task)
            else:
                logger.error("No task and no message in context")
                return

        async for partial in self.agent.stream(query, task.contextId):
            require_input = partial['require_user_input']
            is_done = partial['is_task_complete']
            text_content = partial['content']

            if require_input:
                # notify input is required
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        status=TaskStatus(
                            state=TaskState.input_required,
                            message=new_agent_text_message(
                                text_content,
                                task.contextId,
                                task.id,
                            ),
                        ),
                        final=True,
                        contextId=task.contextId,
                        taskId=task.id,
                    )
                )
            elif is_done:
                # send final artifact
                await event_queue.enqueue_event(
                    TaskArtifactUpdateEvent(
                        append=False,
                        contextId=task.contextId,
                        taskId=task.id,
                        lastChunk=True,
                        artifact=new_text_artifact(
                            name='blog_article',
                            description='Generated blog article.',
                            text=text_content,
                        ),
                    )
                )
                # notify task completion
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        status=TaskStatus(state=TaskState.completed),
                        final=True,
                        contextId=task.contextId,
                        taskId=task.id,
                    )
                )
            else:
                # send working status update
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        status=TaskStatus(
                            state=TaskState.working,
                            message=new_agent_text_message(
                                text_content,
                                task.contextId,
                                task.id,
                            ),
                        ),
                        final=False,
                        contextId=task.contextId,
                        taskId=task.id,
                    )
                )

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise Exception('cancel not supported')