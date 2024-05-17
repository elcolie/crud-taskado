"""POST method to create task."""
import logging

from fastapi import HTTPException, status
from pydantic import ValidationError

from core.common.validate_input import GenericTaskInput, TaskSuccessMessage
from core.methods.crud import TaskRepository

logger = logging.getLogger(__name__)


def create_task(task_input: GenericTaskInput) -> TaskSuccessMessage:
    """Endpoint to create a task."""
    # Instantiate the logic class
    task_repository = TaskRepository()
    try:
        _ = task_repository.create_task(task_input)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e) from e

    return TaskSuccessMessage(
        message='Instance created successfully!',
    )
