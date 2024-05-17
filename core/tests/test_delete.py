"""Test DELETE endpoint."""
import unittest

from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

from core.models.models import CurrentTaskContent, TaskContent
from core.tests.test_gadgets import (manual_create_task,
                                     prepare_users_for_test,
                                     remove_all_tasks_and_users)
from main import app
from app import engine

client = TestClient(app)


class TestDelete(unittest.TestCase):
    """Test DELETE endpoint."""

    def setUp(self) -> None:
        """Prepare the data for testing."""
        remove_all_tasks_and_users()
        prepare_users_for_test()

    def tearDown(self):
        """Remove all tasks and users."""
        remove_all_tasks_and_users()

    def test_delete_task(self) -> None:
        """Test happy path for deleting a task."""
        task_id = manual_create_task()
        response = client.delete(f"/{task_id}")

        with Session(engine) as session:
            # Check history in database
            history = (
                session.query(TaskContent).filter(TaskContent.id == task_id).first()
            )
            assert history.is_deleted is True

            # Check current_task in database
            current = (
                session.query(CurrentTaskContent)
                .filter(CurrentTaskContent.id == task_id)
                .first()
            )
            assert current is None
            assert 0 == session.query(CurrentTaskContent).count()

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {'message': 'Instance deleted successfully!'}

    def test_delete_invalid_task(self) -> None:
        """Test invalid task id."""
        response = client.delete('/999')
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {'detail': 'Task not found'}


if __name__ == '__main__':
    unittest.main()
