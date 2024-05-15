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
from core.common.validate_input import TaskSuccessMessage, CheckTaskId
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

    with Session(engine) as session:
        # Get the last revision of the task
        task = (
            session.query(TaskContent)
            .filter(TaskContent.id == task_instance.id)
            .order_by(TaskContent.created_at.desc())  # type: ignore[attr-defined]  # pylint: disable=no-member
            .first()
        )

        current_task_instance = (
            session.query(CurrentTaskContent)
            .filter(CurrentTaskContent.id == task.id)
            .first()
        )

        # Undo the PUT operation
        if current_task_instance is not None:
            # Remove the latest of tast_content
            last_task_instance = (
                session.query(TaskContent)
                .filter(TaskContent.id == task.id)
                .order_by(desc(TaskContent.created_at))
                .first()
            )

            session.delete(last_task_instance)
            session.commit()

            new_last_task_instance = (
                session.query(TaskContent)
                .filter(TaskContent.id == task.id)
                .order_by(desc(TaskContent.created_at))
                .first()
            )

            if new_last_task_instance is None:
                # It means task is created and immediately run undo.
                raise HTTPException(
                    status_code=status.HTTP_425_TOO_EARLY,
                    detail='Unable to undo new created task.',
                )
            # Change the identifier on current_task_instance
            current_task_instance.identifier = new_last_task_instance.identifier

        else:
            # Undo the DELETE operation
            # Get the current task instance
            current_task_instance = CurrentTaskContent(
                **{
                    'identifier': task.identifier,
                    'id': task.id,
                    'created_by': task.created_by,
                    'updated_by': task.created_by,
                    'created_at': task.created_at,
                    'updated_at': datetime.now(),
                }
            )

        # Mark the history as `is_deleted`
        task.is_deleted = False

        # Save the current task table.
        session.add(current_task_instance)
        session.commit()
        return TaskSuccessMessage(
            message='Instance restored successfully!',
        )
