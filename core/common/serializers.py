"""Deserialize the instance to a dictionary."""
from marshmallow import fields, validate
from marshmallow_sqlalchemy import SQLAlchemySchema
from sqlmodel import Session

from app import engine
from core.models.models import StatusEnum, TaskContent, User


class BaseSchema(SQLAlchemySchema):
    """Base schema for SQLAlchemy."""

    class Meta:  # pylint: disable=too-few-public-methods
        """Meta class."""
        sqla_session = Session


class BaseTaskContentSchema(BaseSchema):
    """Schema for TaskContent."""

    class Meta(BaseSchema.Meta):  # pylint: disable=too-few-public-methods
        """Meta class for TaskContentSchema."""

        model = TaskContent
        load_instance = True
        include_relationships = True

    id = fields.Integer()
    title = fields.String()
    description = fields.String()
    due_date = fields.Date()
    status = fields.String(
        validate=validate.OneOf(
            [StatusEnum.PENDING, StatusEnum.IN_PROGRESS, StatusEnum.COMPLETED]
        )
    )
    created_by = fields.Integer()


class TaskContentSchema(BaseTaskContentSchema):
    """Task schema."""
    username = fields.String()

    # Replace created_by with nested serialization
    # created_by = fields.Nested(UserSchema, only=("id", "username"))
    # https://stackoverflow.com/questions/78389527/nested-payload-show-blank-dictionary-sqlalchemy-marshmallow
    # created_by = SmartNested(UserSchema)  # Got {}
    # created_by = fields.Nested(UserSchema, attribute="id")  # created_by does not show up.
    # created_by = Nested(UserSchema, attribute="username")  # created_by does not show up.


class ListTaskSchemaOutput(BaseTaskContentSchema):
    """List task schema."""

    created_by__username: str | None = fields.String()
    updated_by: int | None = fields.Integer()
    updated_by__username: str | None = fields.String()


def get_user(user_id: int) -> User:
    """Get user by id."""

    with Session(engine) as session:
        return session.query(User).filter(User.id == user_id).first()
