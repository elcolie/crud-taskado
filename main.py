import logging
import typing as typ
import uuid
from datetime import date

import ipdb
import sqlalchemy
from fastapi import FastAPI, status
from fastapi import HTTPException
from fastapi import Response
from pydantic import BaseModel
from pydantic import ValidationError
from sqlalchemy import create_engine, or_
from sqlalchemy import func, and_
from sqlalchemy.orm import aliased
from sqlmodel import Session

# Database connection url
from app import DATABASE_URL
from models import StatusEnum, TaskContent, User, CurrentTaskContent
from serializers import TaskContentSchema
from validate_input import GenericTaskInput, UpdateTask, CheckTaskId, check_due_date_format

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

            # Update the timestamp on this task instance.
            current_task_instance = session.query(CurrentTaskContent).filter(
                CurrentTaskContent.id == payload.id).first()
            current_task_instance.updated_by = task_content_instance.created_by
            current_task_instance.updated_at = new_content.created_at

            session.add(new_content)
            session.add(current_task_instance)
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
            # Delete the instance from the current_task table
            current_task_instance = session.query(CurrentTaskContent).filter(
                CurrentTaskContent.id == task_instance.id).first()

            # Mark the history as `is_deleted`
            task = session.query(TaskContent).filter(TaskContent.id == task_instance.id).first()
            task.is_deleted = True
            session.delete(current_task_instance)
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
            try:
                current_task = session.query(CurrentTaskContent).filter(CurrentTaskContent.id == task_id).one()
            except sqlalchemy.orm.exc.NoResultFound:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task not found: {task_id}")

            task_content_schema = TaskContentSchema()
            task = session.query(TaskContent).filter(
                TaskContent.id == current_task.id,
                TaskContent.identifier == current_task.identifier,
                TaskContent.is_deleted == False,
            ).one()
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


def get_queryset(_due_date: typ.Optional[date]) -> sqlalchemy.orm.query.Query:
    """Get the queryset of tasks."""
    with (Session(engine) as session):
        # List out available id.
        available_id_list = session.query(CurrentTaskContent).all()
        available_identifier_list = [i.identifier for i in available_id_list]

        # Get task and id
        queryset_tasks = session.query(TaskContent).filter(
            TaskContent.identifier.in_(available_identifier_list),
            or_(TaskContent.due_date == _due_date, _due_date is None)
        ).subquery()

        # Get username and id
        username_query = session.query(User.username, User.id).subquery()

        # Join the queryset and username
        final_query = session.query(queryset_tasks, username_query).outerjoin(
            username_query, and_(queryset_tasks.c.created_by == username_query.c.id)
        )
        return final_query


def validate_due_date(str_due_date: str) -> typ.Optional[date]:
    """Validate the due date."""
    correct_format = check_due_date_format(str_due_date)
    year, month, day = correct_format.split("-")
    return date(int(year), int(month), int(day))


def validate_status(str_status: str) -> StatusEnum:
    """Validate the status."""
    for _status in StatusEnum:
        if _status.value == str_status:
            return _status
    raise ValueError("StatusEnum is invalid status value.")


def validate_username(str_username: str) -> User:
    """Validate the username."""
    with Session(engine) as session:
        user = session.query(User).filter(User.username == str_username).first()
        if user is None:
            raise ValueError("User does not exist.")
        return user


# query, filter and pagination.
@app.get("/")
async def list_tasks(
    response: Response,
    due_date: str = None, task_status: str = None, created_by__username: str = None,
) -> typ.Dict[str, typ.Union[typ.Any, typ.List[ErrorDetail]]]:
    """Endpoint to list all tasks."""
    errors: typ.List[ErrorDetail] = []

    due_date_instance: typ.Optional[date] = None
    try:
        due_date_instance = validate_due_date(due_date) if due_date else None
    except ValueError as e:
        logger.info(f"Due date validation failed. {e}")
        errors.append(ErrorDetail(loc=["due_date"], msg=str(e), type="ValueError"))
    try:
        status_instance = validate_status(task_status) if task_status else None
    except ValueError as e:
        logger.info(f"Status validation failed. {e}")
        errors.append(ErrorDetail(loc=["status"], msg=str(e), type="ValueError"))
    try:
        username_instance = validate_username(created_by__username) if created_by__username else None
    except ValueError as e:
        logger.info(f"Username validation failed. {e}")
        errors.append(ErrorDetail(loc=["created_by__username"], msg=str(e), type="ValueError"))

    if len(errors) > 0:
        response.status_code = status.HTTP_406_NOT_ACCEPTABLE
        return {
            'message': errors
        }

    task_content_schema_with_username = TaskContentSchema()
    tasks_queryset = get_queryset(
        _due_date=due_date_instance
    )

    serialized_tasks = task_content_schema_with_username.dump(tasks_queryset, many=True)
    return {
        'count': len(serialized_tasks),
        'tasks': serialized_tasks,
    }


# TODO. Undo the last action.
@app.post("/undo/{task_id}")
async def undo_task(task_id: int) -> typ.Union[TaskSuccessMessage]:
    """Endpoint to undo a task."""
    try:
        task_instance = CheckTaskId(id=task_id)
    except ValidationError as e:
        logger.error(f"Validation failed UNDO method: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unable to undo. Task not found")
    else:
        ipdb;
        ipdb.set_trace()
