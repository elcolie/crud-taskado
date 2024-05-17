"""FastAPI CRUD operations with SQLAlchemy."""
import logging
import typing as typ

from fastapi import Depends, FastAPI, status
# import all you need from fastapi-pagination
from fastapi_pagination import Page, add_pagination, paginate
from core.common.get_instance import valid_task, valid_undo_task
from core.common.validate_input import (CheckTaskId, GenericTaskInput,
                                        SummaryTask, TaskSuccessMessage,
                                        TaskValidationError, UpdateTask)
from core.methods.delete_method.method import delete_task
from core.methods.get_detail_method.method import get_task
from core.methods.get_list_method.method import (
    CommonTaskQueryParams, list_tasks, validate_task_common_query_param)
from core.methods.post_method.method import create_task
from core.methods.undo_method.method import undo_task
from core.methods.update_method.method import update_task
from core.models.models import CurrentTaskContent

# Configure the logger
logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create a logger object
logger = logging.getLogger(__name__)


app = FastAPI()


@app.post('/create-task/', status_code=status.HTTP_201_CREATED, response_model=TaskSuccessMessage)
async def _create_task(task_input: GenericTaskInput) -> typ.Any:
    """Endpoint to create a task."""
    return create_task(task_input)


@app.delete('/{task_id}', response_model=TaskSuccessMessage)
async def _delete_task(task_id: CurrentTaskContent = Depends(valid_task)) -> typ.Any:
    """Endpoint to delete a task."""
    return delete_task(task_id)


@app.get('/{task_id}', response_model=UpdateTask)
async def _get_task(task_id: CurrentTaskContent = Depends(valid_task)) -> typ.Any:
    return get_task(task_id)


@app.get('/', response_model=Page[SummaryTask])
async def _list_tasks(
    commons: typ.Annotated[CommonTaskQueryParams, Depends(validate_task_common_query_param)],
) -> typ.Any:
    return paginate(list_tasks(commons))


@app.post('/undo/{task_id}', response_model=TaskSuccessMessage)
async def _undo_task(task_id: CheckTaskId = Depends(valid_undo_task)) -> typ.Any:
    return undo_task(task_id)


@app.put('/', response_model=TaskSuccessMessage)
async def _update_task(
    payload: UpdateTask,
) -> typ.Union[TaskSuccessMessage, TaskValidationError,]:
    """Endpoint to update a task."""
    return update_task(payload)

add_pagination(app)
