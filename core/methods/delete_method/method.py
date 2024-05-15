import logging
import typing as typ

from sqlalchemy import desc
from sqlmodel import Session
from sqlmodel import create_engine

from app import DATABASE_URL
from core.common.validate_input import TaskSuccessMessage
from core.models.models import CurrentTaskContent, TaskContent

logger = logging.getLogger(__name__)
engine = create_engine(DATABASE_URL, echo=True)


def delete_task(task_instance: CurrentTaskContent) -> typ.Union[TaskSuccessMessage]:
    """Endpoint to delete a task."""
    with Session(engine) as session:
        # Delete the instance from the current_task table
        current_task_instance = (
            session.query(CurrentTaskContent)
            .filter(CurrentTaskContent.id == task_instance.id)
            .first()
        )

        # Mark the history as `is_deleted`
        task = (
            session.query(TaskContent)
            .filter(TaskContent.id == task_instance.id)
            .order_by(desc(TaskContent.created_at))
            .first()
        )
        task.is_deleted = True
        session.delete(current_task_instance)
        session.commit()
        return TaskSuccessMessage(
            message='Instance deleted successfully!',
        )
