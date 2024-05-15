import logging
import typing as typ

from datetime import date

from fastapi import status, Response

from core.common.serializers import ListTaskSchemaOutput, get_user
from core.methods.crud import TaskRepository
from core.methods.get_list_method.get_queryset import get_queryset
from core.methods.get_list_method.pagination_gadgets import generate_query_params
from core.models.models import StatusEnum, User
from core.common.validate_input import ResponsePayload, ErrorDetail, validate_due_date, validate_status, validate_username, \
    SummaryTask
logger = logging.getLogger(__name__)


def list_tasks(  # pylint: disable=too-many-locals
    response: Response,
    due_date: str | None = None,
    task_status: str | None = None,
    created_by__username: str | None = None,
    updated_by__username: str | None = None,
    _page_number: int = 1,  # Page number
    _per_page: int = 10,  # Number of items per page
) -> typ.Union[ResponsePayload, typ.Dict[str, typ.List[ErrorDetail]]]:
    """Endpoint to list all tasks."""
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
        response.status_code = status.HTTP_406_NOT_ACCEPTABLE
        return {'message': errors}

    task_repository = TaskRepository()
    tasks_results = task_repository.list_tasks(
        due_date_instance, status_instance, user_instance, updated_user_instance
    )
    list_task_schema_output = ListTaskSchemaOutput()

    # Stick with class not using dictionary.

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
    start = (_page_number - 1) * _per_page
    end = start + _per_page
    data_length = len(serialized_tasks)

    if end >= data_length:
        if _page_number > 1:
            previous = generate_query_params(
                due_date=due_date,
                task_status=task_status,
                created_by__username=created_by__username,
                updated_by__username=updated_by__username,
                _page_number=_page_number - 1,
                _per_page=_per_page,
            )
        else:
            previous = None
        return ResponsePayload(
            count=data_length,
            tasks=[SummaryTask(**i) for i in serialized_tasks[start:end]],
            next=None,
            previous=previous,
        )

    if _page_number > 1:
        previous = generate_query_params(
            due_date=due_date,
            task_status=task_status,
            created_by__username=created_by__username,
            updated_by__username=updated_by__username,
            _page_number=_page_number - 1,
            _per_page=_per_page,
        )
    else:
        previous = None
    _next = generate_query_params(
        due_date=due_date,
        task_status=task_status,
        created_by__username=created_by__username,
        updated_by__username=updated_by__username,
        _page_number=_page_number + 1,
        _per_page=_per_page,
    )
    return ResponsePayload(
        count=data_length,
        tasks=[SummaryTask(**i) for i in serialized_tasks[start:end]],
        next=_next,
        previous=previous,
    )
