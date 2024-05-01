"""Deserialize the instance to a dictionary."""
from marshmallow import fields, Schema
from marshmallow import validate
from marshmallow.fields import Nested
from marshmallow_sqlalchemy import SQLAlchemySchema
from sqlalchemy import create_engine
from sqlmodel import Session

from app import DATABASE_URL
from models import TaskContent, User, StatusEnum


# Use this because marshmellow can exclude identifier field. But for clarity.
# I intentionally not use `exclude` to be explicit.

class BaseSchema(SQLAlchemySchema):
    class Meta:
        sqla_session = Session


class SmartNested(Nested):
    def serialize(self, attr, obj, accessor=None):
        if attr not in obj.__dict__:
            return {"id": int(getattr(obj, attr + "_id"))}
        return super(SmartNested, self).serialize(attr, obj, accessor)


class UserSchema(BaseSchema):
    """Schema for User."""
    class Meta(BaseSchema.Meta):
        model = User

    id = fields.Integer()
    username = fields.String()


class BaseTaskContentSchema(BaseSchema):
    """Schema for TaskContent."""
    class Meta(BaseSchema.Meta):
        """Meta class for TaskContentSchema."""
        model = TaskContent
        load_instance = True
        include_relationships = True

    id = fields.Integer()
    title = fields.String()
    description = fields.String()
    due_date = fields.Date()
    status = fields.String(validate=validate.OneOf([
        StatusEnum.pending, StatusEnum.in_progress, StatusEnum.completed]))
    created_by = fields.Integer()


class TaskContentSchema(BaseTaskContentSchema):
    username = fields.String()

    # Replace created_by with nested serialization
    # created_by = fields.Nested(UserSchema, only=("id", "username"))

    # TODO:
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
    # Create the database engine
    engine = create_engine(DATABASE_URL, echo=True)

    with Session(engine) as session:
        return session.query(User).filter(User.id == user_id).first()
