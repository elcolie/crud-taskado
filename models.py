from datetime import date, datetime
import enum
from sqlmodel import Field, SQLModel


class StatusEnum(enum.Enum):
    """Enum class of status field."""
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"


class GenericTask(SQLModel, table=True):
    """Model class for GenericTask."""
    id: int = Field(primary_key=False)  # For human use
    identifier: str = Field(primary_key=True)   # For redo mechanism
    created_at: datetime = Field(default=date.today())  # For redo mechanism
    is_deleted: bool = Field(default=False)     # For redo mechanism


class TaskContent(SQLModel, table=True):
    """Model class for TaskContent."""
    identifier: str = Field(primary_key=True)   # For redo mechanism
    id: int = Field(primary_key=False)  # For human use
    title: str = Field(nullable=True)
    description: str = Field(nullable=True)
    due_date: date = Field(default=None, nullable=True)
    status: StatusEnum = Field(default=StatusEnum.pending)
    created_by: int = Field(nullable=True, default=None, foreign_key="user.id")
    created_at: datetime = Field(default=date.today())  # For redo mechanism
    updated_at: datetime = Field(default=date.today())


class User(SQLModel, table=True):
    """User model of this application."""
    id: int = Field(primary_key=True)
    username: str = Field(nullable=False)
