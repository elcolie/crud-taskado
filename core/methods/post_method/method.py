"""POST method to create task."""
import logging

from core.common.validate_input import GenericTaskInput, TaskSuccessMessage
from core.methods.crud import TaskRepository

logger = logging.getLogger(__name__)


def create_task(task_input: GenericTaskInput) -> TaskSuccessMessage:
    """Endpoint to create a task."""
    # Instantiate the logic class
    task_repository = TaskRepository()
    task_repository.create_task(task_input)

    return TaskSuccessMessage(
        message='Instance created successfully!',
    )
