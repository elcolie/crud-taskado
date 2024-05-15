"""Try implement using OOP. This supposed to be a data layer."""
import logging
import uuid

from pydantic import ValidationError
from sqlalchemy import func
from sqlmodel import Session
from sqlmodel import create_engine

from app import DATABASE_URL
from core.common.validate_input import GenericTaskInput, TaskValidationError, ErrorDetail
from core.common.validate_input import parse_date
from core.models.models import TaskContent, CurrentTaskContent

logger = logging.getLogger(__name__)
engine = create_engine(DATABASE_URL, echo=True)


class CreateTask:
    """Mixin class for creating a task."""

    @staticmethod
    def validate_input_task(task_input: GenericTaskInput) -> GenericTaskInput:
        """Create a task."""
        try:
            instance = GenericTaskInput(**task_input.dict())
            logger.info('Validation successful!')
        except ValidationError as e:
            logger.error(f"Validation failed: {e}")  # pylint: disable=logging-fstring-interpolation
            out_payload = TaskValidationError(
                message='Validation failed!',
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
            raise ValidationError(detail=out_payload) from e
        return instance

    @staticmethod
    def _create_task(instance: GenericTaskInput) -> None:
        """Create a task."""
        # Validation successful, save the data to the database
        with Session(engine) as session:
            # Parse the due_date string to date object
            due_date_instance = parse_date(instance.due_date) if instance.due_date else None

            # Generate a unique identifier for the task
            _identifier = uuid.uuid4().hex

            # id is for human reference, identifier is for redo mechanism
            _max_id = session.query(func.max(TaskContent.id)).scalar()
            max_id = 0 if _max_id is None else _max_id
            _id = max_id + 1

            instance_dict = instance.dict()
            instance_dict['due_date'] = due_date_instance

            # Add the history record.
            task_content = TaskContent(
                **{
                    'id': _id,
                    'identifier': _identifier,
                    **instance_dict,
                }
            )

            # Save the current task table.
            current_task = CurrentTaskContent(
                **{
                    'id': _id,
                    'identifier': _identifier,
                    'created_by': instance.created_by,
                    'updated_by': instance.created_by,
                    'created_at': task_content.created_at,
                    'updated_at': task_content.created_at,
                }
            )
            session.add(task_content)
            session.add(current_task)
            session.commit()

    def create_task(self, task_input: GenericTaskInput):
        validated_input_task = self.validate_input_task(task_input)
        self._create_task(validated_input_task)


class TaskRepository(CreateTask):
    """Task business logic."""

    def get_current_task(self):
        pass

    def get_task_content(self):
        pass
