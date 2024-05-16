"""DELETE method to delete a task."""
import logging
import typing as typ

from sqlmodel import create_engine

from app import DATABASE_URL
from core.common.validate_input import TaskSuccessMessage
from core.methods.crud import TaskRepository
from core.models.models import CurrentTaskContent

logger = logging.getLogger(__name__)
engine = create_engine(DATABASE_URL, echo=True)


def delete_task(task_instance: CurrentTaskContent) -> typ.Union[TaskSuccessMessage]:
    """Endpoint to delete a task."""
    task_repository = TaskRepository()
    task_repository.delete_task(task_instance)

    return TaskSuccessMessage(
        message='Instance deleted successfully!',
    )
