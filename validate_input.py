"""pydantic models for validating input data."""
import typing as typ
from datetime import datetime

from pydantic import BaseModel, Field
from pydantic import field_validator
from sqlalchemy import create_engine
from sqlalchemy import exists
from sqlmodel import Session

from app import DATABASE_URL
from models import StatusEnum, User, TaskContent


class GenericTaskInput(BaseModel):
    """Pydantic model to validate input data for creating a task."""
    title: typ.Optional[str]
    description: typ.Optional[str]
    status: StatusEnum = StatusEnum.pending
    due_date: str = None
    created_by: typ.Optional[int] = None
    # created_at: datetime = Field(default_factory=datetime.today)
    # updated_at: datetime = Field(default_factory=datetime.today)

    @field_validator("due_date")
    def check_due_date_format(cls, value: str) -> str:
        if value is not None:
            try:
                # Parse the due_date string to check if it's in the correct format.
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Invalid date format. Must be in 'YYYY-MM-DD' format.")
        return value

    @field_validator("created_by")
    def user_exists(cls, value: int) -> None:
        if value is not None and not cls.user_exists_in_db(value):
            raise ValueError("User with this id does not exist")
        return value

    @classmethod
    def user_exists_in_db(cls, user_id: int) -> typ.Optional[int]:
        # Implement the logic to check if the user exists in the database
        # This could be a database query or any other method to check user existence
        engine = create_engine(DATABASE_URL, echo=True)
        session = Session(engine)

        return session.scalar(
            exists()
            .where(User.id == user_id)
            .select()
        )


class UpdateTask(GenericTaskInput):
    """Pydantic model to validate input data for updating a task."""
    id: int

    @field_validator("id")
    def task_id_exists_in_db(cls, task_id: int) -> typ.Optional[int]:
        """Check if the task id exists in the database."""
        engine = create_engine(DATABASE_URL, echo=True)
        session = Session(engine)
        is_exists = session.scalar(
            exists()
            .where(TaskContent.id == task_id)
            .select()
        )
        if not is_exists:
            raise ValueError("Task with this id does not exist")
        return task_id

