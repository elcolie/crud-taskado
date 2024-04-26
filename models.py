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
    id: int = Field(primary_key=True)
    title: str = Field(nullable=True)
    description: str = Field(nullable=True)
    due_date: date = Field(default=None, nullable=True)
    status: StatusEnum = Field(default=StatusEnum.pending)
    created_by: int = Field(nullable=True, default=None, foreign_key="user.id")
    created_at: datetime = Field(default=date.today())
    updated_at: datetime = Field(default=date.today())


class User(SQLModel, table=True):
    """User model of this application."""
    id: int = Field(primary_key=True)
    username: str = Field(nullable=False)
