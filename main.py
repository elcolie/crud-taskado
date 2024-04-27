import logging
import typing as typ
from datetime import date
import uuid
from fastapi import FastAPI
from sqlalchemy import func
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlmodel import Session

# Database connection url
from app import DATABASE_URL
from models import StatusEnum, TaskContent
from serializers import TaskContentSchema
from validate_input import GenericTaskInput, UpdateTask
from pydantic import BaseModel

import logging

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
    TaskValidationError,
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
        return out_payload
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
        return out_payload
    else:
        with Session(engine) as session:
            task = session.query(TaskContent).filter(TaskContent.id == payload.id).first()

            # In order to do undo mechanism. Create a new instance of the task.
            new_identifier = uuid.uuid4().hex

            # Create new revision.
            new_content = TaskContent(**{
                'id': task.id,  # Use existing id
                'identifier': new_identifier,
                'title': task_content_instance.title,   # Update the rest of the payload.
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

        from sqlalchemy import and_
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

@app.get("/task/{task_id}")
async def get_task(task_id: int):
    """Endpoint to get a task by id."""
    with Session(engine) as session:
        task_content_schema = TaskContentSchema()
        task = session.query(TaskContent).filter(TaskContent.id == task_id).first()
        serialized_task = task_content_schema.dump(task)
        return {
            'task': serialized_task,
        }

