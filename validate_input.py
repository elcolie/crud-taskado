"""pydantic models for validating input data."""
import typing as typ
from datetime import datetime

from pydantic import BaseModel, field_validator
from sqlalchemy import create_engine, exists
from sqlmodel import Session

from app import DATABASE_URL
from models import StatusEnum, TaskContent, User


def check_due_date_format(value: str) -> str:
    """Check due date format and return string."""
    if value is not None:
        try:
            # Parse the due_date string to check if it's in the correct format.
            datetime.strptime(value, '%Y-%m-%d')
        except ValueError as err:
            raise ValueError("Invalid date format. Must be in 'YYYY-MM-DD' format.") from err
    return value


class GenericTaskInput(BaseModel):
    """Pydantic model to validate input data for creating a task."""

    title: str | None
    description: str | None
    status: StatusEnum = StatusEnum.PENDING
    due_date: str | None = None
    created_by: int | None = None

    # created_at: datetime = Field(default_factory=datetime.today)
    # updated_at: datetime = Field(default_factory=datetime.today)

    # https://docs.pydantic.dev/latest/api/functional_validators/#pydantic.functional_validators.field_validator
    @field_validator('due_date')
    @classmethod
    def check_due_date_format(cls, value: str) -> str:
        """Check due date format and return string."""
        return check_due_date_format(value)

    @field_validator('created_by')
    @classmethod
    def user_exists(cls, value: int) -> int | None:
        """Check if the user exists in the database."""
        if value is not None and not cls.user_exists_in_db(value):
            # 422 status code raise in the BaseModel.
            raise ValueError('User with this id does not exist')
        return value

    @classmethod
    def user_exists_in_db(cls, user_id: int) -> int | None:
        """Short call to check with database."""
        # Implement the logic to check if the user exists in the database
        # This could be a database query or any other method to check user existence
        engine = create_engine(DATABASE_URL, echo=True)
        session = Session(engine)

        return session.scalar(exists().where(User.id == user_id).select())


class CheckTaskId(BaseModel):
    """Pydantic model to validate input data for DELETE. It can be reused with PUT too."""

    id: int

    @field_validator('id')
    @classmethod
    def task_id_exists_in_db(cls, task_id: int) -> typ.Optional[int]:
        """Check if the task id exists in the database."""
        engine = create_engine(DATABASE_URL, echo=True)
        session = Session(engine)
        is_exists = session.scalar(exists().where(TaskContent.id == task_id).select())
        if not is_exists:
            raise ValueError('Task with this id does not exist')
        return task_id


class UpdateTask(CheckTaskId, GenericTaskInput):
    """Include id to the model by mixin."""
