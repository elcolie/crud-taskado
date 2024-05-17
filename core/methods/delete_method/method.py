"""DELETE method to delete a task."""
import logging
import typing as typ

from core.common.validate_input import TaskSuccessMessage
from core.methods.crud import TaskRepository
from core.models.models import CurrentTaskContent

logger = logging.getLogger(__name__)


def delete_task(task_instance: CurrentTaskContent) -> TaskSuccessMessage:
    """Endpoint to delete a task."""
    task_repository = TaskRepository()
    task_repository.delete_task(task_instance)

    return TaskSuccessMessage(
        message='Instance deleted successfully!',
    )
