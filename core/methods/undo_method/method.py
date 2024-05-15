import logging
import typing as typ
from datetime import datetime

from fastapi import HTTPException
from fastapi import status
from pydantic import ValidationError
from sqlalchemy import desc
from sqlmodel import Session
from sqlmodel import create_engine

from app import DATABASE_URL
from core.common.validate_input import TaskSuccessMessage, CheckTaskId, UndoError
from core.methods.crud import TaskRepository
from core.models.models import TaskContent, CurrentTaskContent

logger = logging.getLogger(__name__)
engine = create_engine(DATABASE_URL, echo=True)


def undo_task(task_id: int) -> typ.Union[TaskSuccessMessage]:
    """Endpoint to undo a task."""
    try:
        task_instance = CheckTaskId(id=task_id)
    except ValidationError as e:
        logger.error(f"Validation failed UNDO method: {e}")  # pylint: disable=logging-fstring-interpolation
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Unable to undo. Task not found',
        ) from e

    try:
        task_repository = TaskRepository()
        task_repository.undo_task(task_instance)
    except UndoError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Task is created and immediately run undo.',
        )
    return TaskSuccessMessage(
        message='Instance restored successfully!',
    )
