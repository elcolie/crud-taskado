import logging
import typing as typ
import uuid
from datetime import datetime

from fastapi import HTTPException
from pydantic import ValidationError
from sqlmodel import Session
from fastapi import status
from sqlmodel import create_engine
from app import DATABASE_URL

from core.models.models import TaskContent, CurrentTaskContent
from core.common.validate_input import UpdateTask, TaskSuccessMessage, TaskValidationError, ErrorDetail, parse_date

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
    with Session(engine) as session:
        task = (
            session.query(TaskContent).filter(TaskContent.id == payload.id).first()
        )

        # In order to do undo mechanism. Create a new instance of the task.
        new_identifier = uuid.uuid4().hex

        # Create new revision.
        new_content = TaskContent(
            **{
                'id': task.id,  # Use existing id
                'identifier': new_identifier,
                'title': task_content_instance.title,  # Update the rest of the payload.
                'description': task_content_instance.description,
                'due_date': parse_date(
                    task_content_instance.due_date
                ) if task_content_instance.due_date else None,
                'status': task_content_instance.status,
                'created_by': task_content_instance.created_by,
                'created_at': datetime.now(),
            }
        )

        # Update the timestamp on this task instance.
        current_task_instance = (
            session.query(CurrentTaskContent)
            .filter(CurrentTaskContent.id == payload.id)
            .first()
        )
        current_task_instance.identifier = new_identifier
        current_task_instance.updated_by = new_content.created_by
        current_task_instance.updated_at = new_content.created_at

        session.add(new_content)
        session.add(current_task_instance)
        session.commit()
        return TaskSuccessMessage(
            message='Instance updated successfully!',
        )
