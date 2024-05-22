"""FastAPI CRUD operations with SQLAlchemy."""
import logging
import typing as typ
from enum import Enum

from fastapi import Depends, FastAPI, status, Body
# import all you need from fastapi-pagination
from fastapi_pagination import Page, add_pagination, paginate

from core.common.get_instance import valid_task, valid_undo_task
from core.common.validate_input import (CheckTaskId, GenericTaskInput,
                                        SummaryTask, TaskSuccessMessage,
                                        TaskValidationError, UpdateTask)
from core.methods.delete_method.method import delete_task
from core.methods.get_detail_method.method import get_task
from core.methods.get_list_method.method import (
    ConcreteCommonTaskQueryParams, list_tasks,
    validate_task_common_query_param)
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

description = """
**CRUD Taskado** todo Task API with undo feature.

- You need to create an user before creating a task.
- You can create, update, delete, list and undo a task.
- You can `undo` the last `UPDATE`, `DELETE` to the task.
- You can filter the tasks by due_date, task_status, created_by_username, updated_by_username.

"""

tags_metadata = [
    dict(
        name="tasks",
        description="CRUD operations",
    ),
    dict(
        name="undo",
        description="Undo the last UPDATE, DELETE to the task",
    )
]


app = FastAPI(
    title="CRUD Taskado todo Task API",
    description=description,
    version='0.0.1',
    terms_of_service="https://creativecommons.org/terms/",
    contact=dict(
        name="Sarit",
        url="https://github.com/elcolie",
        email="cs.sarit@gmail.com"
    ),
    license_info=dict(
        name="Apache 2.0",
        url="https://www.apache.org/licenses/LICENSE-2.0.html"
    ),
    openapi_tags=tags_metadata,
    openapi_url="/api/v1/openapi.json",
)


class Tags(Enum):
    tasks = "tasks"
    undo = "undo"


@app.post('/create-task/',
          summary="Create todo task",
          status_code=status.HTTP_201_CREATED,
          response_model=TaskSuccessMessage,
          tags=[Tags.tasks]
          )
async def _create_task(
    task_input: typ.Annotated[
        GenericTaskInput,
        Body(
            openapi_examples={
                "normal": {
                    "summary": "Create a task",
                    "description": "Create a task with all fields",
                    "value": {
                        "description": "Nice item",
                        "title": "Buy a pickled plum juice",
                        "status": "pending",
                        "due_date": "2022-12-31",
                        "created_by": 1
                    }
                },
                "invalid_due_date": {
                    "name": "Invalid due date",
                    "description": "due_date format is YYYY-MM-DD",
                    "value": {
                        "title": "Buy a pickled plum juice smoothie",
                        "description": "Good for health",
                        "status": "pending",
                        "due_date": "2022-99-31",
                        "created_by": 1
                    }
                },
                "invalid_status": {
                    "name": "Invalid status",
                    "description": "Status must be either 'pending', 'in_progress' or 'done'",
                    "value": {
                        "title": "Buy a pickled plum juice",
                        "description": "Nice item",
                        "status": "done",
                        "due_date": "2022-12-31",
                        "created_by": 1
                    }
                }
            }
        )
    ]) -> typ.Any:
    """
    Endpoint to create a task.

    - **title**: The title of the task.
    - **description**: The description of the task.
    - **status**: The status of the task. It must be either 'pending', 'in_progress' or 'done'.
    - **due_date**: The due date of the task in 'YYYY-MM-DD' format.
    - **created_by**: The user id who created the task.
    """
    return create_task(task_input)


@app.delete('/{task_id}',
            summary="Delete todo task",
            status_code=status.HTTP_204_NO_CONTENT, tags=[Tags.tasks])
async def _delete_task(task_id: CurrentTaskContent = Depends(valid_task)) -> None:
    """
    Endpoint to delete a task.

    - **task_id**: The id of the task to delete.
    """
    delete_task(task_id)
    return


@app.get('/{task_id}',
         summary="Get task detail",
         response_model=UpdateTask, tags=[Tags.tasks])
async def _get_task(task_id: CurrentTaskContent = Depends(valid_task)) -> typ.Any:
    """
    Endpoint to get a task detail.

    - **task_id**: The id of the task to get.
    """
    return get_task(task_id)


@app.get('/',
         summary="List tasks",
         response_model=Page[SummaryTask], tags=[Tags.tasks])
async def _list_tasks(
    commons: typ.Annotated[
        ConcreteCommonTaskQueryParams,
        Depends(validate_task_common_query_param)
    ],
) -> typ.Any:
    """
    Endpoint to list all tasks.

    - **due_date**: The due date of the task in 'YYYY-MM-DD' format.
    - **task_status**: The status of the task. It must be either 'pending', 'in_progress' or 'done'.
    - **created_by_username**: The username of the user who created the task.
    - **updated_by_username**: The username of the user who updated the task.
    """
    return paginate(list_tasks(commons))


@app.post('/undo/{task_id}',
          summary="Undo task",
          response_model=TaskSuccessMessage, tags=[Tags.undo])
async def _undo_task(task_id: CheckTaskId = Depends(valid_undo_task)) -> typ.Any:
    """
    description="Undo last UPDATE, DELETE to the task",

    - **task_id**: The id of the task to undo.
    """
    return undo_task(task_id)


@app.put('/',
         summary="Update task",
         description="Make another revision of the task", response_model=TaskSuccessMessage, tags=[Tags.tasks])
async def _update_task(
    payload: typ.Annotated[
        UpdateTask,
        Body(
            openapi_examples={
                "normal": {
                    "summary": "Update a task",
                    "description": "Update a task with all fields",
                    "value": {
                        "id": 1,
                        "title": "Buy a pickled plum juice",
                        "description": "Nice item",
                        "status": "pending",
                        "due_date": "2022-12-31",
                        "created_by": 1
                    }
                },
                "invalid_due_date": {
                    "name": "Invalid due date",
                    "description": "due_date format is YYYY-MM-DD",
                    "value": {
                        "id": 1,
                        "title": "Buy a pickled plum juice smoothie",
                        "description": "Good for health",
                        "status": "pending",
                        "due_date": "2022-99-31",
                        "created_by": 1
                    }
                },
                "invalid_status": {
                    "name": "Invalid status",
                    "description": "Status must be either 'pending', 'in_progress' or 'done'",
                    "value": {
                        "id": 1,
                        "title": "Buy a pickled plum juice",
                        "description": "Nice item",
                        "status": "done",
                        "due_date": "2022-12-31",
                        "created_by": 1
                    }
                }
            }
        )
    ],
) -> TaskSuccessMessage | TaskValidationError:
    """Endpoint to update a task."""
    return update_task(payload)


add_pagination(app)
