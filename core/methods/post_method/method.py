import logging
import typing as typ

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlmodel import create_engine

from app import DATABASE_URL
from core.common.validate_input import (ErrorDetail, GenericTaskInput,
                                        TaskSuccessMessage,
                                        TaskValidationError, parse_date)
from core.methods.crud import TaskRepository

logger = logging.getLogger(__name__)
engine = create_engine(DATABASE_URL, echo=True)


def create_task(task_input: GenericTaskInput) -> typ.Union[TaskSuccessMessage,]:
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
