"""Test UNDO mechanism."""
import time
import unittest
from datetime import date

from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

from app import engine
from core.models.models import CurrentTaskContent, StatusEnum, TaskContent
from core.tests.test_gadgets import (manual_create_task,
                                     prepare_users_for_test,
                                     remove_all_tasks_and_users)
from main import app

client = TestClient(app)


class UndoMech(unittest.TestCase):
    """Undo mechanism tests."""

    def setUp(self) -> None:
        """Prepare the data for testing."""
        remove_all_tasks_and_users()
        prepare_users_for_test()

    def tearDown(self):
        """Remove all tasks and users."""
        remove_all_tasks_and_users()

    def test_undo_delete(self) -> None:
        """Test happy path for deleting a task."""
        title = 'This is first created task'
        description = 'This is a test task'
        _status = 'completed'
        due_date = '1995-12-31'
        task_id = manual_create_task(
            title=title,
            description=description,
            _status=_status,
            due_date=due_date,
            has_user=True,
            user_id=10,
        )
        deleted_response = client.delete(f"/{task_id}")

        # Apply undo mechanism
        undo_response = client.post(f"/undo/{task_id}")

        # GET list must show the task
        get_response = client.get('/')

        assert deleted_response.status_code == status.HTTP_204_NO_CONTENT
        assert deleted_response.text == ''
        assert undo_response.status_code == status.HTTP_200_OK
        assert undo_response.json() == {'message': 'Instance restored successfully!'}
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json() == {
            'items': [
                {
                    'id': 1,
                    'title': 'This is first created task',
                    'description': 'This is a test task',
                    'due_date': '1995-12-31',
                    'status': 'StatusEnum.COMPLETED',
                    'created_by': 10,
                    'updated_by': 10,
                    'created_by_username': 'test_user',
                    'updated_by_username': 'test_user'
                }
            ],
            'total': 1,
            'page': 1,
            'size': 50,
            'pages': 1}

    def test_create_task_then_undo(self) -> None:
        """Create task then undo."""
        task_id = manual_create_task()
        # Apply undo mechanism
        undo_response = client.post(f"/undo/{task_id}")
        assert undo_response.status_code == status.HTTP_400_BAD_REQUEST
        assert undo_response.json() == {'detail': 'Task is created and immediately run undo.'}

    def test_undo_update(self) -> None:
        """Test happy path for updating a task."""
        task_id = manual_create_task()
        time.sleep(1)  # To distinguish the updated_at
        response = client.put(
            '/',
            json={
                'id': task_id,
                'title': 'Wrong title',
                'description': 'This is wrong one',
                'status': 'completed',
                'due_date': '1111-11-11',
                'created_by': 2,
            },
        )

        undo_response = client.post(f"/undo/{task_id}")

        with Session(engine) as session:
            # Check history in database
            history = (
                session.query(TaskContent).filter(TaskContent.id == task_id).first()
            )
            assert history.is_deleted is False
            assert history.title == 'Test Task with created_by'
            assert history.description == 'This is a test task'
            assert history.status == StatusEnum.PENDING
            assert history.due_date == date(2022, 12, 31)
            assert history.created_by == 10

            # Check current_task in database
            current = (
                session.query(CurrentTaskContent)
                .filter(CurrentTaskContent.id == task_id)
                .first()
            )
            assert current is not None
            assert current.updated_by == 2  # This will remain from previous action.

        # Apply undo mechanism
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {'message': 'Instance updated successfully!'}
        assert undo_response.status_code == status.HTTP_200_OK

    def test_two_updates_then_delete_and_undo(self) -> None:
        """Test happy path for updating a task."""
        task_id = manual_create_task()
        first_response = client.put(
            '/',
            json={
                'id': task_id,
                'title': 'First updated title',
                'description': 'First updated desc',
                'status': 'pending',
                'due_date': '1111-11-11',
                'created_by': 1,
            },
        )
        second_response = client.put(
            '/',
            json={
                'id': task_id,
                'title': 'Second updated title',
                'description': 'Second updated desc',
                'status': 'in_progress',
                'due_date': '2222-2-2',
                'created_by': 2,
            },
        )
        deleted_response = client.delete(f"/{task_id}")

        # Apply undo mechanism
        undo_response = client.post(f"/undo/{task_id}")

        with Session(engine) as session:
            # Check current_task in database
            current_content = (
                session.query(CurrentTaskContent)
                .filter(CurrentTaskContent.id == task_id)
                .first()
            )
            assert current_content is not None
            assert current_content.updated_by == 2
            assert current_content.created_by == 2

            content = (
                session.query(TaskContent)
                .filter(TaskContent.identifier == current_content.identifier)
                .first()
            )
            assert content is not None
            assert content.title == 'Second updated title'
            assert content.id == task_id
            assert content.description == 'Second updated desc'
            assert content.status == StatusEnum.IN_PROGRESS
            assert content.due_date == date(2222, 2, 2)
            assert content.created_by == 2

        assert first_response.status_code == status.HTTP_200_OK
        assert first_response.json() == {'message': 'Instance updated successfully!'}
        assert second_response.status_code == status.HTTP_200_OK
        assert second_response.json() == {'message': 'Instance updated successfully!'}
        assert deleted_response.status_code == status.HTTP_204_NO_CONTENT
        assert deleted_response.text == ''
        assert undo_response.status_code == status.HTTP_200_OK

    def test_undo_wrong_id(self) -> None:
        """Test wrong id."""
        task_id = manual_create_task()
        response = client.put(
            '/',
            json={
                'id': task_id + 99,
                'title': 'New updated title',
                'description': 'New desc',
                'status': 'pending',
                'due_date': '2022-12-31',
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json() == {
            'detail': [
                {
                    'type': 'value_error',
                    'loc': ['body', 'id'],
                    'msg': 'Value error, Task with this id does not exist',
                    'input': 100,
                    'ctx': {'error': {}},
                }
            ]
        }

    def test_create_update_delete_undo_undo(self) -> None:
        """Expect undo mechanism to work for all actions."""
        task_id = manual_create_task()
        first_response = client.put(
            '/',
            json={
                'id': task_id,
                'title': 'First updated title',
                'description': 'First updated desc',
                'status': 'pending',
                'due_date': '1111-11-11',
                'created_by': 1,
            },
        )

        deleted_response = client.delete(f"/{task_id}")

        # Apply undo mechanism
        undo_response = client.post(f"/undo/{task_id}")  # Undo delete

        # Apply undo mechanism
        undo_response_2 = client.post(f"/undo/{task_id}")  # Undo update

        with Session(engine) as session:
            # Check current_task in database
            current_content = (
                session.query(CurrentTaskContent)
                .filter(CurrentTaskContent.id == task_id)
                .first()
            )
            assert current_content is not None
            assert current_content.updated_by == 1
            assert current_content.created_by == 1  # Because of undo.

            content = (
                session.query(TaskContent)
                .filter(TaskContent.identifier == current_content.identifier)
                .first()
            )
            assert content is not None
            assert content.title == 'Test Task with created_by'
            assert content.id == task_id
            assert content.description == 'This is a test task'
            assert content.status == StatusEnum.PENDING
            assert content.due_date == date(2022, 12, 31)
            assert content.created_by == 10  # The original creator.

        assert first_response.status_code == status.HTTP_200_OK
        assert first_response.json() == {'message': 'Instance updated successfully!'}
        assert deleted_response.status_code == status.HTTP_204_NO_CONTENT
        assert deleted_response.text == ''
        assert undo_response.status_code == status.HTTP_200_OK
        assert undo_response_2.status_code == status.HTTP_200_OK


if __name__ == '__main__':
    unittest.main()
