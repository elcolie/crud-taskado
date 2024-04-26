"""pydantic models for validating input data."""
import typing as typ
from pydantic import ValidationError, BaseModel, Field, validator, field_validator
from pydantic import ValidationError, BaseModel
from pydantic import ValidationError, BaseModel, Field
from datetime import date, datetime
from models import GenericTask, StatusEnum


class GenericTaskInput(BaseModel):
    """Pydantic model to validate input data for creating a task."""
    title: typ.Optional[str]
    description: typ.Optional[str]
    status: StatusEnum = StatusEnum.pending
    due_date: str = None
    created_by: typ.Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.today)
    updated_at: datetime = Field(default_factory=datetime.today)

    @field_validator("due_date")
    def check_due_date_format(cls, v):
        if v is not None:
            try:
                # Parse the due_date string to check if it's in the correct format.
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Invalid date format. Must be in 'YYYY-MM-DD' format.")
        return v
