"""Model classes for this application."""
import enum
from datetime import date, datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class StatusEnum(enum.Enum):
    """Enum class of status field."""

    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'


class TaskContent(SQLModel, table=True):  # type: ignore[call-arg]
    """Model class for TaskContent history."""

    identifier: str = Field(primary_key=True)  # For redo mechanism
    id: int = Field(primary_key=False)  # For human use
    title: str = Field(nullable=True)
    description: str = Field(nullable=True)
    due_date: date = Field(default=None, nullable=True)
    status: StatusEnum = Field(default=StatusEnum.PENDING)
    is_deleted: bool = Field(default=False)  # For redo mechanism
    created_by: int = Field(nullable=True, default=None, foreign_key='user.id')
    created_at: datetime = Field(default=datetime.now())  # For redo mechanism


class CurrentTaskContent(SQLModel, table=True):  # type: ignore[call-arg]
    """Model class for current."""

    # https://github.com/tiangolo/sqlmodel/issues/114
    __table_args__ = (UniqueConstraint('identifier', 'id'),)

    identifier: str = Field(primary_key=True)  # For redo mechanism
    id: int = Field(primary_key=False)  # For human use
    created_by: int = Field(nullable=True, default=None, foreign_key='user.id')
    updated_by: int = Field(nullable=True, default=None, foreign_key='user.id')
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())


class User(SQLModel, table=True):  # type: ignore[call-arg]
    """User model of this application."""

    id: int = Field(primary_key=True)
    username: str = Field(nullable=False)
