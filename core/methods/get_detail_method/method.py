"""GET detail of task."""
import logging

from fastapi import HTTPException, status

from core.common.serializers import TaskContentSchema
from core.common.validate_input import UpdateTask
from core.methods.crud import TaskRepository
from core.models.models import CurrentTaskContent, StatusEnum

logger = logging.getLogger(__name__)


def get_task(current_task: CurrentTaskContent) -> UpdateTask:
    """Endpoint to get a task by id."""
    task_repository = TaskRepository()
    task = task_repository.get_task_by_id(current_task)
    task_content_schema = TaskContentSchema()
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
