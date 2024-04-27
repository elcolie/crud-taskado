import logging
import typing as typ
import uuid
from datetime import date

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy import func
from sqlmodel import Session
from sqlalchemy import and_

# Database connection url
from app import DATABASE_URL
from models import StatusEnum, TaskContent
from serializers import TaskContentSchema
from validate_input import GenericTaskInput, UpdateTask, CheckTaskId

# Configure the logger
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create a logger object
logger = logging.getLogger(__name__)

# Create the database engine
engine = create_engine(DATABASE_URL, echo=True)

app = FastAPI()


class ErrorDetail(BaseModel):
    """Error details model."""
    loc: typ.List[str]
    msg: str
    type: str


class TaskValidationError(BaseModel):
    """Task validation error model."""
    message: str
    errors: typ.List[ErrorDetail]


class TaskSuccessMessage(BaseModel):
    message: str


def parse_date(date_str: str) -> date:
    """Function to parse date string."""
    try:
        year, month, day = date_str.split("-")
        return date(int(year), int(month), int(day))
    except ValueError:
        raise ValidationError("Invalid date format. Must be in 'YYYY-MM-DD' format.")


@app.post("/create-task/")
async def create_task(task_input: GenericTaskInput) -> typ.Union[
    TaskSuccessMessage,
]:
    """Endpoint to create a task."""
    try:
        instance = GenericTaskInput(**task_input.dict())
        logger.info("Validation successful!")
    except ValidationError as e:
        logger.error(f"Validation failed: {e}")
        out_payload = TaskValidationError(
            message="Validation failed!",
            errors=[
                ErrorDetail(
                    loc=error['loc'],
                    msg=error['msg'],
                    type=error['type'],
                )
                for error in e.errors()
            ],
        )
        # BaseModel raises 422 status code. Raise here to be safe.
        raise HTTPException(status_code=404, detail=out_payload)
    else:
        # Validation successful, save the data to the database
        with Session(engine) as session:
            # Parse the due_date string to date object
            instance.due_date = parse_date(instance.due_date)

            # Generate a unique identifier for the task
            _identifier = uuid.uuid4().hex

            # id is for human reference, identifier is for redo mechanism
            _max_id = session.query(func.max(TaskContent.id)).scalar()
            max_id = 0 if _max_id is None else _max_id
            id = max_id + 1
            task_content = TaskContent(**{
                'id': id,
                'identifier': _identifier,
                **instance.dict(),
            })
            session.add(task_content)
            session.commit()
    return TaskSuccessMessage(
        message="Instance created successfully!",
    )


@app.put("/")
async def update_task(payload: UpdateTask) -> typ.Union[
    TaskSuccessMessage,
    TaskValidationError,
]:
    """Endpoint to update a task."""
    try:
        task_content_instance = UpdateTask(**payload.dict())
    except ValidationError as e:
        logger.error(f"Validation failed UPDATE method: {e}")
        out_payload = TaskValidationError(
            message="Validation failed!",
            errors=[
                ErrorDetail(
                    loc=error['loc'],
                    msg=error['msg'],
                    type=error['type'],
                )
                for error in e.errors()
            ],
        )
        raise HTTPException(status_code=404, detail=out_payload)
    else:
        with Session(engine) as session:
            task = session.query(TaskContent).filter(TaskContent.id == payload.id).first()

            # In order to do undo mechanism. Create a new instance of the task.
            new_identifier = uuid.uuid4().hex

            # Create new revision.
            new_content = TaskContent(**{
                'id': task.id,  # Use existing id
                'identifier': new_identifier,
                'title': task_content_instance.title,  # Update the rest of the payload.
                'description': task_content_instance.description,
                'due_date': parse_date(task_content_instance.due_date),
                'status': task_content_instance.status,
                'created_by': task_content_instance.created_by,
            })
            session.add(new_content)
            session.commit()
            return TaskSuccessMessage(
                message="Instance updated successfully!",
            )


@app.delete("/{task_id}")
async def delete_task(task_id: int) -> typ.Union[TaskSuccessMessage]:
    """Endpoint to delete a task."""
    try:
        task_instance = CheckTaskId(id=task_id)
    except ValidationError as e:
        logger.error(f"Validation failed DELETE method: {e}")
        raise HTTPException(status_code=404, detail="Task not found")
    else:
        with Session(engine) as session:
            task = session.query(TaskContent).filter(TaskContent.id == task_instance.id).first()
            task.is_deleted = True
            session.commit()
            return TaskSuccessMessage(
                message="Instance deleted successfully!",
            )


@app.get("/{task_id}")
async def get_task(task_id: int) -> typ.Union[
    UpdateTask,
]:
    """Endpoint to get a task by id."""
    try:
        _ = CheckTaskId(id=task_id)
    except ValidationError as e:
        logger.error(f"Validation failed GET method: {e}")
        raise HTTPException(status_code=404, detail="Task not found")
    else:
        with Session(engine) as session:
            task_content_schema = TaskContentSchema()
            task = session.query(TaskContent).filter(
                TaskContent.id == task_id,
                TaskContent.is_deleted == False,
            ).first()
            # Task is deleted. Then id is here, but is_deleted is True.
            if task is None:
                raise HTTPException(status_code=404, detail="Task is deleted")
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


# TODO: filter and pagination.
@app.get("/")
async def list_tasks() -> typ.Dict[str, typ.Any]:
    """Endpoint to list all tasks."""
    with Session(engine) as session:
        task_content_schema = TaskContentSchema()
        # tasks = (
        #     session.query(TaskContent)
        #     .filter(
        #         TaskContent.id.in_(
        #             session.query(GenericTask.id).filter(GenericTask.is_deleted == False)
        #         )
        #     )
        #     .all()
        # )
        # Subquery to get the latest created_at for each identifier
        subquery = session.query(TaskContent.identifier, func.max(TaskContent.created_at).label('max_created_at')). \
            filter(TaskContent.is_deleted == False). \
            group_by(TaskContent.identifier). \
            subquery()

        # Query to fetch the latest undeleted TaskContent entries
        latest_task_contents = session.query(TaskContent). \
            join(subquery, and_(TaskContent.identifier == subquery.c.identifier,
                                TaskContent.created_at == subquery.c.max_created_at)). \
            filter(TaskContent.is_deleted == False). \
            all()

        tasks = latest_task_contents
        serialized_tasks = task_content_schema.dump(tasks, many=True)
        return {
            'count': len(serialized_tasks),
            'tasks': serialized_tasks,
        }
