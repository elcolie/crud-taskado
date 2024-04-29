import logging
import typing as typ
import uuid
from datetime import date

import ipdb
import sqlalchemy
from fastapi import FastAPI, status
from fastapi import HTTPException
from pydantic import BaseModel
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy import distinct
from sqlalchemy import func, and_
from sqlalchemy import select
from sqlmodel import Session

# Database connection url
from app import DATABASE_URL
from models import StatusEnum, TaskContent, User, CurrentTaskContent
from serializers import TaskContentSchema
from validate_input import GenericTaskInput, UpdateTask, CheckTaskId
from sqlalchemy.orm import aliased

# Create an alias for the User table
UserAlias = aliased(User)

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


@app.post("/create-task/", status_code=status.HTTP_201_CREATED)
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=out_payload)
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
            _id = max_id + 1

            # Add the history record.
            task_content = TaskContent(**{
                'id': _id,
                'identifier': _identifier,
                **instance.dict(),
            })

            # Save the current task table.
            current_task = CurrentTaskContent(**{
                'id': _id,
                'identifier': _identifier,
                'created_by': instance.created_by,
                'updated_by': instance.created_by,
                'created_at': task_content.created_at,
                'updated_at': task_content.created_at,
            })
            session.add(task_content)
            session.add(current_task)
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=out_payload)
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    else:
        with Session(engine) as session:
            task_content_schema = TaskContentSchema()
            task = session.query(TaskContent).filter(
                TaskContent.id == task_id,
                TaskContent.is_deleted == False,
            ).first()
            # Task is deleted. Then id is here, but is_deleted is True.
            if task is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task is deleted")
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


def get_queryset() -> sqlalchemy.orm.query.Query:
    """Get the queryset of tasks."""
    with (Session(engine) as session):
        # List out add id that is deleted.
        deleted_id_list = session.query(distinct(TaskContent.id)).filter(TaskContent.is_deleted == True).all()

        # List out all undeleted tasks.
        # Extract the ids from the id_list
        ids = [id_[0] for id_ in deleted_id_list]

        # Get only the latest revision of each task
        stmt = (
            select(
                # Group by id and get the latest created_at
                TaskContent.id,
                func.max(TaskContent.created_at).label('max_created_at')
            )
            # Exclude the deleted tasks.
            .where(~TaskContent.id.in_(ids))
            .group_by(TaskContent.id)
        )

        # Join the result to get the full task content
        queryset = session.query(TaskContent).join(
            stmt,
            and_(
                TaskContent.id == stmt.c.id,
                TaskContent.created_at == stmt.c.max_created_at,
            )
        ).subquery()
        logger.info("==================================")
        logger.info(f"len(queryset): {len(session.query(queryset).all())}")
        for i in session.query(queryset).all():
            logger.info(i)

        # Create subquery for username query
        # Tasks with username
        username_query = session.query(TaskContent, UserAlias.username).join(UserAlias).subquery()
        logger.info(f"len(username_query): {len(session.query(username_query).all())}")

        # Find the first created_by in the queryset
        min_created_at_stmt = (
            select(
                # Group by id and get the latest created_at
                TaskContent.id,
                func.min(TaskContent.created_at).label('min_created_at')
            )
            # Exclude the deleted tasks.
            .where(~TaskContent.id.in_(ids))
            .group_by(TaskContent.id)
        ).subquery()

        import ipdb; ipdb.set_trace()

        # Left join. But SQLAlchemy use outerjoin.
        final_query = session.query(queryset, username_query, min_created_at_stmt).outerjoin(
            username_query, and_(queryset.c.identifier == username_query.c.identifier)
        )

        len(session.execute(final_query).all())
        logger.info("===========List the final queryset=======================")
        for idx, i in enumerate(session.execute(final_query).all()):
            logger.info(f"[{idx}]: {i}")

        return final_query


# TODO: query, filter and pagination.
@app.get("/")
async def list_tasks() -> typ.Dict[str, typ.Any]:
    """Endpoint to list all tasks."""
    task_content_schema_with_username = TaskContentSchema()
    tasks_queryset = get_queryset()
    serialized_tasks = task_content_schema_with_username.dump(tasks_queryset, many=True)
    print("===================================")
    for idx, i in enumerate(tasks_queryset):
        logger.info(f"[{idx}]: {i}")
    return {
        'count': len(serialized_tasks),
        'tasks': serialized_tasks,
    }
