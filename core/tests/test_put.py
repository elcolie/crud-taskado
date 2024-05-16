"""
Test PUT method for the API.

Instead of clicking the POSTMAN I run this script instead.
Be careful, this script is not intended to run in the CI/CD pipeline.
Because it mutates the database.
"""
import datetime
import time
import unittest

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import asc, create_engine, desc
from sqlmodel import Session

from app import DATABASE_URL
from core.models.models import CurrentTaskContent, StatusEnum, TaskContent
from core.tests.test_gadgets import (manual_create_task,
                                     prepare_users_for_test,
                                     remove_all_tasks_and_users)
from main import app

engine = create_engine(DATABASE_URL, echo=True)
client = TestClient(app)


class TestPut(unittest.TestCase):
    """Test put."""

    def setUp(self) -> None:
        """Prepare the data for testing."""
        remove_all_tasks_and_users()
        prepare_users_for_test()

    def tearDown(self):
        """Remove all tasks and users."""
        remove_all_tasks_and_users()

    def test_update_task(self) -> None:
        """Test happy path for updating a task."""
        task_id = manual_create_task()
        time.sleep(1)  # To distinguish the updated_at
        user_id = 2
        response = client.put(
            '/',
            json={
                'id': task_id,
                'title': 'New updated title',
                'description': 'New desc',
                'status': 'completed',
                'due_date': '2333-12-31',
                'created_by': user_id,
            },
        )
        with Session(engine) as session:
            first_task_content = (
                session.query(TaskContent)
                .filter(TaskContent.id == task_id)
                .order_by(asc(TaskContent.created_at))
                .first()
            )
            last_task_content = (
                session.query(TaskContent)
                .filter(TaskContent.id == task_id)
                .order_by(desc(TaskContent.created_at))
                .first()
            )
            current_task_content = (
                session.query(CurrentTaskContent)
                .filter(CurrentTaskContent.identifier == last_task_content.identifier)
                .first()
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {'message': 'Instance updated successfully!'}
        assert last_task_content.title == 'New updated title'
        assert last_task_content.description == 'New desc'
        assert last_task_content.status == StatusEnum.COMPLETED
        assert last_task_content.due_date == datetime.date(2333, 12, 31)
        assert last_task_content.created_by == user_id
        assert last_task_content.created_at > first_task_content.created_at
        assert current_task_content.created_by == 10
        assert current_task_content.updated_by == user_id

    def test_wrong_due_date(self) -> None:
        """Test invalid date format."""
        task_id = manual_create_task()
        response = client.put(
            '/',
            json={
                'id': task_id,
                'title': 'New updated title',
                'description': 'New desc',
                'status': 'pending',
                'due_date': '2022-12-31T00:00:00',
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json() == {
            'detail': [
                {
                    'type': 'value_error',
                    'loc': ['body', 'due_date'],
                    'msg': "Value error, Invalid date format. Must be in 'YYYY-MM-DD' format.",
                    'input': '2022-12-31T00:00:00',
                    'ctx': {'error': {}},
                }
            ]
        }

    def test_wrong_status_and_due_date(self) -> None:
        """Test wrong more than 1 issue."""
        task_id = manual_create_task()
        response = client.put(
            '/',
            json={
                'id': task_id,
                'title': 'New updated title',
                'description': 'New desc',
                'status': 'Invalid status',
                'due_date': '2022-12-31T00:00:00',
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json() == {
            'detail': [
                {
                    'type': 'enum',
                    'loc': ['body', 'status'],
                    'msg': "Input should be 'pending', 'in_progress' or 'completed'",
                    'input': 'Invalid status',
                    'ctx': {'expected': "'pending', 'in_progress' or 'completed'"},
                },
                {
                    'type': 'value_error',
                    'loc': ['body', 'due_date'],
                    'msg': "Value error, Invalid date format. Must be in 'YYYY-MM-DD' format.",
                    'input': '2022-12-31T00:00:00',
                    'ctx': {'error': {}},
                },
            ]
        }

    def test_wrong_id(self) -> None:
        """Test wrong id."""
        response = client.put(
            '/',
            json={
                'id': -6,
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
                    'input': -6,
                    'ctx': {'error': {}},
                }
            ]
        }

    def test_wrong_id_by_string(self) -> None:
        """Test wrong id."""
        response = client.put(
            '/',
            json={
                'id': 'wrong_id',
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
                    'type': 'int_parsing',
                    'loc': ['body', 'id'],
                    'msg': 'Input should be a valid integer, unable to parse string as an integer',
                    'input': 'wrong_id',
                }
            ]
        }


if __name__ == '__main__':
    unittest.main()
