"""List tasks method."""
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


class ConcreteCommonTaskQueryParams:
    """Concrete common task query params. It is filled with instances."""
    def __init__(
        self,
        due_date: date | None,
        task_status: StatusEnum | None,
        created_by_username: User | None,
        updated_by_username: User | None,
    ):
        self.due_date = due_date
        self.task_status = task_status
        self.created_by_username = created_by_username
        self.updated_by_username = updated_by_username


def validate_task_common_query_param(
    due_date: str = Query(None),
    task_status: str = Query(None),
    created_by_username: str = Query(None),
    updated_by_username: str = Query(None),
) -> ConcreteCommonTaskQueryParams:
    """
    Validate the task common query params.
    If it is not valid collect the error until end and raise it.
    """
    errors: typ.List[ErrorDetail] = []

    def validate_and_collect_error(
        validation_func: typ.Callable[[typ.Any], typ.Any],
        value: typ.Any,
        field_name: str
    ) -> typ.Any:
        try:
            return validation_func(value) if value else None
        except ValueError as e:
            logger.info('%s validation failed. %s', field_name, e)
            errors.append(ErrorDetail(loc=[field_name], msg=str(e), type='ValueError'))
            return None

    due_date_instance: date | None = validate_and_collect_error(
        validate_due_date, due_date, 'due_date')
    status_instance: StatusEnum | None = validate_and_collect_error(
        validate_status, task_status, 'status')
    user_instance: User | None = validate_and_collect_error(
        validate_username, created_by_username, 'created_by_username')
    updated_user_instance: User | None = validate_and_collect_error(
        validate_username, updated_by_username, 'updated_by_username')

    if len(errors) > 0:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail=[err.__dict__ for err in errors]
        )
    return ConcreteCommonTaskQueryParams(
        due_date=due_date_instance,
        task_status=status_instance,
        created_by_username=user_instance,
        updated_by_username=updated_user_instance,
    )


def list_tasks(
    commons: ConcreteCommonTaskQueryParams,
) -> typ.List[SummaryTask]:
    """Endpoint to list all tasks."""
    task_repository = TaskRepository()
    tasks_results = task_repository.list_tasks(
        commons.due_date,
        commons.task_status,
        commons.created_by_username,
        commons.updated_by_username,
    )
    list_task_schema_output = ListTaskSchemaOutput()

    raw_list_tasks = []
    for _task in tasks_results:
        created_by: User = get_user(_task[0].created_by)
        updated_by: User = get_user(_task[0].updated_by)
        raw_list_tasks.append(
            {
                'id': _task[1].id,
                'title': _task[1].title,
                'description': _task[1].DESCRIPTION,
                'due_date': _task[1].due_date,
                'status': _task[1].status,
                'created_by': _task[0].created_by,
                'updated_by': _task[0].updated_by,
                # Should wrap into single query.
                'created_by_username': created_by.username
                if created_by is not None
                else None,
                'updated_by_username': updated_by.username
                if updated_by is not None
                else None,
            }
        )
    serialized_tasks = list_task_schema_output.dump(raw_list_tasks, many=True)
    return [SummaryTask(**i) for i in serialized_tasks]
