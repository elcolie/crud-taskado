"""FastAPI CRUD operations with SQLAlchemy."""
import logging
import typing as typ

from fastapi import FastAPI
from fastapi import Response
from fastapi import status
from sqlalchemy import create_engine
from fastapi import Depends

# Database connection url
from app import DATABASE_URL
from core.common.get_instance import valid_task, valid_undo_task
from core.common.validate_input import GenericTaskInput, TaskSuccessMessage, TaskValidationError, ErrorDetail, \
    ResponsePayload, UpdateTask, CheckTaskId
from core.methods.delete_method.method import delete_task
from core.methods.get_detail_method.method import get_task
from core.methods.get_list_method.method import list_tasks
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

# Create the database engine
engine = create_engine(DATABASE_URL, echo=True)

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


@app.get('/')   # Use type annotation instead of response_model. Because of customized response.
async def _list_tasks(  # pylint: disable=too-many-locals
    response: Response,
    due_date: str | None = None,
    task_status: str | None = None,
    created_by__username: str | None = None,
    updated_by__username: str | None = None,
    _page_number: int = 1,  # Page number
    _per_page: int = 10,  # Number of items per page
) -> typ.Union[ResponsePayload, typ.Dict[str, typ.List[ErrorDetail]]]:
    return list_tasks(
        response,
        due_date,
        task_status,
        created_by__username,
        updated_by__username,
        _page_number,
        _per_page, )


@app.post('/undo/{task_id}', response_model=TaskSuccessMessage)
async def _undo_task(task_id: CheckTaskId = Depends(valid_undo_task)) -> typ.Any:
    return undo_task(task_id)


@app.put('/', response_model=TaskSuccessMessage)
async def _update_task(
    payload: UpdateTask,
) -> typ.Union[TaskSuccessMessage, TaskValidationError,]:
    """Endpoint to update a task."""
    return update_task(payload)
