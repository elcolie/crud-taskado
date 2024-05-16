"""Update method to update a task."""
import logging
import typing as typ

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlmodel import create_engine

from app import DATABASE_URL
from core.common.validate_input import (ErrorDetail, TaskSuccessMessage,
                                        TaskValidationError, UpdateTask)
from core.methods.crud import TaskRepository

logger = logging.getLogger(__name__)
engine = create_engine(DATABASE_URL, echo=True)


def update_task(
    payload: UpdateTask,
) -> typ.Union[TaskSuccessMessage, TaskValidationError,]:
    """Endpoint to update a task."""
    try:
        task_content_instance = UpdateTask(**payload.dict())
    except ValidationError as e:
        logger.error(f"Validation failed UPDATE method: {e}")  # pylint: disable=logging-fstring-interpolation
        out_payload = TaskValidationError(
            message='Validation failed!',
            errors=[
                ErrorDetail(
                    loc=error['loc'],
                    msg=error['msg'],
                    type=error['type'],
                )
                for error in e.errors()
            ],
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=out_payload) from e
    task_repository = TaskRepository()
    task_repository.update(task_content_instance, payload)
    return TaskSuccessMessage(
        message='Instance updated successfully!',
    )
