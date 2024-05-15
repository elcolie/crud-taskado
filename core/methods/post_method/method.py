import typing as typ


from fastapi import HTTPException
from pydantic import ValidationError
from fastapi import status

from app import DATABASE_URL
from core.methods.crud import TaskRepository
from sqlmodel import create_engine
from core.common.validate_input import GenericTaskInput, TaskSuccessMessage, TaskValidationError, ErrorDetail, parse_date
import logging

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