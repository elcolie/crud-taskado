import logging
import typing as typ
from datetime import date

from fastapi import HTTPException, Query, status

from core.common.serializers import ListTaskSchemaOutput, get_user
from core.common.validate_input import (ErrorDetail, SummaryTask,
                                        validate_due_date, validate_status,
                                        validate_username)
from core.methods.crud import TaskRepository
from core.models.models import StatusEnum, User

logger = logging.getLogger(__name__)


class CommonTaskQueryParams:
    def __init__(
        self,
        due_date: str | date | None,
        task_status: str | StatusEnum | None,
        created_by__username: str | User | None,
        updated_by__username: str | User | None,
    ):
        self.due_date = due_date
        self.task_status = task_status
        self.created_by__username = created_by__username
        self.updated_by__username = updated_by__username


def validate_task_common_query_param(
    due_date: str = Query(None),
    task_status: str = Query(None),
    created_by__username: str = Query(None),
    updated_by__username: str = Query(None),
) -> CommonTaskQueryParams:
    errors: typ.List[ErrorDetail] = []
    due_date_instance: typ.Optional[date] = None
    status_instance: typ.Optional[StatusEnum] = None
    user_instance: typ.Optional[User] = None
    updated_user_instance: typ.Optional[User] = None
    try:
        due_date_instance = validate_due_date(due_date) if due_date else None
    except ValueError as e:
        logger.info(f"Due date validation failed. {e}")  # pylint: disable=logging-fstring-interpolation
        errors.append(ErrorDetail(loc=['due_date'], msg=str(e), type='ValueError'))
    try:
        status_instance = validate_status(task_status) if task_status else None
    except ValueError as e:
        logger.info(f"Status validation failed. {e}")  # pylint: disable=logging-fstring-interpolation
        errors.append(ErrorDetail(loc=['status'], msg=str(e), type='ValueError'))
    try:
        user_instance = (
            validate_username(created_by__username) if created_by__username else None
        )
    except ValueError as e:
        logger.info(f"Username validation failed. {e}")  # pylint: disable=logging-fstring-interpolation
        errors.append(
            ErrorDetail(loc=['created_by__username'], msg=str(e), type='ValueError')
        )
    try:
        updated_user_instance = (
            validate_username(updated_by__username) if updated_by__username else None
        )
    except ValueError as e:
        logger.info(f"Updated username validation failed. {e}")  # pylint: disable=logging-fstring-interpolation
        errors.append(
            ErrorDetail(loc=['updated_by__username'], msg=str(e), type='ValueError')
        )
    if len(errors) > 0:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail=[err.__dict__ for err in errors]
        )
    return CommonTaskQueryParams(
        due_date=due_date_instance,
        task_status=status_instance,
        created_by__username=user_instance,
        updated_by__username=updated_user_instance,
    )


def list_tasks(  # pylint: disable=too-many-locals
    commons: CommonTaskQueryParams,
) -> typ.List[SummaryTask]:
    """Endpoint to list all tasks."""
    task_repository = TaskRepository()
    tasks_results = task_repository.list_tasks(
        commons.due_date,
        commons.task_status,
        commons.created_by__username,
        commons.updated_by__username,
    )
    list_task_schema_output = ListTaskSchemaOutput()

    _list_tasks = []
    for _task in tasks_results:
        created_by: User = get_user(_task[0].created_by)
        updated_by: User = get_user(_task[0].updated_by)
        _list_tasks.append(
            {
                'id': _task[1].id,
                'title': _task[1].title,
                'description': _task[1].description,
                'due_date': _task[1].due_date,
                'status': _task[1].status,
                'created_by': _task[0].created_by,
                'updated_by': _task[0].updated_by,
                # Should wrap into single query.
                'created_by__username': created_by.username
                if created_by is not None
                else None,
                'updated_by__username': updated_by.username
                if updated_by is not None
                else None,
            }
        )
    serialized_tasks = list_task_schema_output.dump(_list_tasks, many=True)
    return [SummaryTask(**i) for i in serialized_tasks]
