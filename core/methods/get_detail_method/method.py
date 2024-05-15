import logging

from fastapi import HTTPException
from fastapi import status
from sqlmodel import create_engine

from app import DATABASE_URL
from core.common.serializers import TaskContentSchema
from core.common.validate_input import UpdateTask
from core.methods.crud import TaskRepository
from core.models.models import CurrentTaskContent, StatusEnum

logger = logging.getLogger(__name__)
engine = create_engine(DATABASE_URL, echo=True)


def get_task(current_task: CurrentTaskContent) -> UpdateTask:
    """Endpoint to get a task by id."""
    task_repository = TaskRepository()
    task = task_repository.get_task_by_id(current_task)
    task_content_schema = TaskContentSchema()
    # Task is deleted. Then id is here, but is_deleted is True.
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Task is deleted'
        )
    serialized_task = task_content_schema.dump(task)

    # Get the status enum string
    enum_string = serialized_task['status']

    # Split the string into the enum class name and the member name
    _, enum_member_name = enum_string.split('.')

    # Get the enum member by its name within the enum class
    enum_member = getattr(StatusEnum, enum_member_name)

    serialized_task['status'] = enum_member
    out_payload = UpdateTask(**serialized_task)
    return out_payload
