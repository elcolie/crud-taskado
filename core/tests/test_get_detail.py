"""Test GET detail by specify task_id."""
import sys
import typing as typ
import unittest

import httpx
from fastapi import status
from fastapi.testclient import TestClient

from main import app
from core.tests.test_gadgets import (manual_create_task, prepare_users_for_test,
                          remove_all_tasks_and_users)

client = TestClient(app)


class TestGetDetail(unittest.TestCase):
    """Test get detail."""

    def setUp(self) -> None:
        """Prepare the data for testing."""
        remove_all_tasks_and_users()
        prepare_users_for_test()

    def tearDown(self):
        """Remove all tasks and users."""
        remove_all_tasks_and_users()

    def make_task_with_two_updates(
        self,
    ) -> typ.Tuple[int, httpx.Response, httpx.Response]:
        """Make two updates."""
        task_id = manual_create_task()
        first_response = client.put(
            '/',
            json={
                'id': task_id,
                'title': 'First updated title',
                'description': 'First updated desc',
                'status': 'pending',
                'due_date': '2029-12-31',
                'created_by': 2,
            },
        )
        second_response = client.put(
            '/',
            json={
                'id': task_id,
                'title': 'Second updated title',
                'description': 'Second updated desc',
                'status': 'pending',
                'due_date': '2099-12-31',
                'created_by': 1,
            },
        )
        return task_id, first_response, second_response

    def test_get_valid_task_detail(self) -> None:
        """Happy path get correct instance."""
        task_id = manual_create_task()
        response = client.get(f"/{task_id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'title': 'Test Task with created_by',
            'description': 'This is a test task',
            'status': 'pending',
            'due_date': '2022-12-31',
            'created_by': 10,
            'id': 1,
        }

    def test_use_wrong_id(self) -> None:
        """Test wrong id."""
        task_id = manual_create_task()
        response = client.get(f"/{task_id + 999}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {'detail': 'Task not found'}

    def test_use_negative_id(self) -> None:
        """Test negative id."""
        task_id = manual_create_task()
        response = client.get(f"/{task_id - sys.maxsize}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {'detail': 'Task not found'}

    def test_use_string_id(self) -> None:
        """Test string id."""
        _ = manual_create_task()
        response = client.get('/some-string')
        assert (
            response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        )  # Because raises by BaseModel
        assert response.json() == {
            'detail': [
                {
                    'type': 'int_parsing',
                    'loc': ['path', 'task_id'],
                    'msg': 'Input should be a valid integer, unable to parse string as an integer',
                    'input': 'some-string',
                }
            ]
        }

    def test_get_deleted_task(self) -> None:
        """Test get deleted task."""
        task_id = manual_create_task()
        deleted_response = client.delete(f"/{task_id}")
        get_response = client.get(f"/{task_id}")
        assert deleted_response.status_code == status.HTTP_200_OK
        assert (
            get_response.status_code == status.HTTP_404_NOT_FOUND
        )  # Because raises by BaseModel
        assert get_response.json() == {'detail': f"Task not found: {task_id}"}

    def test_update_two_times_then_get(self) -> None:
        """Update 2 times and then GET the task. Expect found the instance."""
        task_id, first_response, second_response = self.make_task_with_two_updates()

        # GET the instance
        get_response = client.get(f"/{task_id}")
        assert first_response.status_code == status.HTTP_200_OK
        assert second_response.status_code == status.HTTP_200_OK
        assert get_response.status_code == status.HTTP_200_OK

    def test_update_two_times_then_delete(self) -> None:
        """Update 2 times and then delete. Expect not found the task."""
        task_id, first_response, second_response = self.make_task_with_two_updates()

        # Delete the task
        deleted_response = client.delete(f"/{task_id}")

        # GET the instance
        get_response = client.get(f"/{task_id}")
        assert first_response.status_code == status.HTTP_200_OK
        assert second_response.status_code == status.HTTP_200_OK
        assert deleted_response.status_code == status.HTTP_200_OK
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
        assert get_response.json() == {'detail': f"Task not found: {task_id}"}


if __name__ == '__main__':
    unittest.main()
