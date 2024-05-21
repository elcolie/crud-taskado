"""Update method to update a task."""
import logging

from fastapi import HTTPException, status
from pydantic import ValidationError

from core.common.validate_input import (ErrorDetail, TaskSuccessMessage,
                                        TaskValidationError, UpdateTask)
from core.methods.crud import TaskRepository

logger = logging.getLogger(__name__)


def update_task(
    payload: UpdateTask,
) -> TaskSuccessMessage | TaskValidationError:
    """Endpoint to update a task."""
    task_content_instance = UpdateTask(**payload.dict())
    task_repository = TaskRepository()
    task_repository.update(task_content_instance, payload)
    return TaskSuccessMessage(
        message='Instance updated successfully!',
    )
