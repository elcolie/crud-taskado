"""Undo method to restore a task."""
import logging
import typing as typ

from fastapi import HTTPException, status
from sqlmodel import create_engine

from app import DATABASE_URL
from core.common.validate_input import (CheckTaskId, TaskSuccessMessage,
                                        UndoError)
from core.methods.crud import TaskRepository

logger = logging.getLogger(__name__)
engine = create_engine(DATABASE_URL, echo=True)


def undo_task(task_instance: CheckTaskId) -> typ.Union[TaskSuccessMessage]:
    """Endpoint to undo a task."""
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
