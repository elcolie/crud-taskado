"""Try implement using OOP. This supposed to be a data layer."""
import logging
import uuid
from datetime import date, datetime

import sqlalchemy
from pydantic import ValidationError
from sqlalchemy import desc, func
from sqlmodel import Session

from app import engine
from core.common.validate_input import (CheckTaskId, ErrorDetail,
                                        GenericTaskInput, TaskValidationError,
                                        UndoError, UpdateTask, parse_date)
from core.methods.get_list_method.get_queryset import get_queryset
from core.models.models import (CurrentTaskContent, StatusEnum, TaskContent,
                                User)

logger = logging.getLogger(__name__)


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
        """Create a task."""
        validated_input_task = self.validate_input_task(task_input)
        self._create_task(validated_input_task)


class DeleteTask:
    """Mixin class for deleting a task."""

    @staticmethod
    def _delete_task(task_instance: CurrentTaskContent) -> None:
        """Delete a task."""
        with Session(engine) as session:
            # Delete the instance from the current_task table
            current_task_instance = (
                session.query(CurrentTaskContent)
                .filter(CurrentTaskContent.id == task_instance.id)
                .first()
            )

            # Mark the history as `is_deleted`
            task = (
                session.query(TaskContent)
                .filter(TaskContent.id == task_instance.id)
                .order_by(desc(TaskContent.created_at))
                .first()
            )
            task.is_deleted = True
            session.delete(current_task_instance)
            session.commit()

    def delete_task(self, task_instance: CurrentTaskContent):
        """Delete a task."""
        self._delete_task(task_instance)


class ListTask:
    """Mixin class for listing tasks."""

    def list_tasks(
        self,
        due_date_instance: date | None,
        status_instance: StatusEnum | None,
        user_instance: User | None,
        updated_user_instance: User | None
    ) -> sqlalchemy.orm.query.Query:
        """List tasks."""
        tasks_results = get_queryset(
            _due_date=due_date_instance,
            _status=status_instance,
            _created_user=user_instance,
            _updated_user=updated_user_instance,
        )
        return tasks_results


class DetailTask:
    """Mixin class for getting task."""

    def get_task_by_id(self, current_task: CurrentTaskContent) -> TaskContent:
        """Get task by id."""
        with Session(engine) as session:
            task = (
                session.query(TaskContent)
                .filter(
                    TaskContent.id == current_task.id,
                    TaskContent.identifier == current_task.identifier,
                    TaskContent.is_deleted == False,  # noqa E712  # pylint: disable=singleton-comparison
                )
                .one()
            )
        return task


class UndoTask:
    """Mixin class for undoing."""

    def undo_task(self, task_instance: CheckTaskId) -> None:
        """Undo a task."""
        with Session(engine) as session:
            # Get the last revision of the task
            task = (
                session.query(TaskContent)
                .filter(TaskContent.id == task_instance.id)
                .order_by(TaskContent.created_at.desc())  # type: ignore[attr-defined]  # pylint: disable=no-member
                .first()
            )

            current_task_instance = (
                session.query(CurrentTaskContent)
                .filter(CurrentTaskContent.id == task.id)
                .first()
            )

            # Undo the PUT operation
            if current_task_instance is not None:
                # Remove the latest of tast_content
                last_task_instance = (
                    session.query(TaskContent)
                    .filter(TaskContent.id == task.id)
                    .order_by(desc(TaskContent.created_at))
                    .first()
                )

                session.delete(last_task_instance)
                session.commit()

                new_last_task_instance = (
                    session.query(TaskContent)
                    .filter(TaskContent.id == task.id)
                    .order_by(desc(TaskContent.created_at))
                    .first()
                )

                if new_last_task_instance is None:
                    # It means task is created and immediately run undo.
                    raise UndoError('Task is created and immediately run undo.')
                # Change the identifier on current_task_instance
                current_task_instance.identifier = new_last_task_instance.identifier

            else:
                # Undo the DELETE operation
                # Get the current task instance
                current_task_instance = CurrentTaskContent(
                    **{
                        'identifier': task.identifier,
                        'id': task.id,
                        'created_by': task.created_by,
                        'updated_by': task.created_by,
                        'created_at': task.created_at,
                        'updated_at': datetime.now(),
                    }
                )

            # Mark the history as `is_deleted`
            task.is_deleted = False

            # Save the current task table.
            session.add(current_task_instance)
            session.commit()


class ModifyTask:
    """Mixin class for updating a task."""

    def update(self, task_content_instance: UpdateTask, payload: UpdateTask) -> None:
        """Update a task."""
        with Session(engine) as session:
            task = (
                session.query(TaskContent).filter(TaskContent.id == payload.id).first()
            )

            # In order to do undo mechanism. Create a new instance of the task.
            new_identifier = uuid.uuid4().hex

            # Create new revision.
            new_content = TaskContent(
                **{
                    'id': task.id,  # Use existing id
                    'identifier': new_identifier,
                    'title': task_content_instance.title,  # Update the rest of the payload.
                    'description': task_content_instance.description,
                    'due_date': parse_date(
                        task_content_instance.due_date
                    ) if task_content_instance.due_date else None,
                    'status': task_content_instance.status,
                    'created_by': task_content_instance.created_by,
                    'created_at': datetime.now(),
                }
            )

            # Update the timestamp on this task instance.
            current_task_instance = (
                session.query(CurrentTaskContent)
                .filter(CurrentTaskContent.id == payload.id)
                .first()
            )
            current_task_instance.identifier = new_identifier
            current_task_instance.updated_by = new_content.created_by
            current_task_instance.updated_at = new_content.created_at

            session.add(new_content)
            session.add(current_task_instance)
            session.commit()


class TaskRepository(ModifyTask,
                     UndoTask,
                     DetailTask,
                     ListTask,
                     DeleteTask,
                     CreateTask):
    """Task business logic."""
