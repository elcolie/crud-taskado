"""Test LIST, filter, and pagination."""
import typing as typ
import unittest

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from app import DATABASE_URL
from main import app
from test_gadgets import manual_create_task, remove_all_tasks_and_users, prepare_users_for_test

client = TestClient(app)

# Create the database engine
engine = create_engine(DATABASE_URL, echo=True)


class TestList(unittest.TestCase):
    """Test List, filter, and pagination."""

    def setUp(self) -> None:
        """Prepare the data for testing."""
        remove_all_tasks_and_users()
        prepare_users_for_test()

    def tearDown(self):
        """Remove all tasks and users."""
        remove_all_tasks_and_users()

    def before_test(self) -> typ.Tuple[
        int, int, int, int, int, int
    ]:
        """Prepare the data for testing."""
        first_task_id = manual_create_task()
        second_task_id = manual_create_task()  # Update 2 times
        third_task_id = manual_create_task()  # Delete
        fourth_task_id = manual_create_task()  # Update 2 time and delete
        fifth_task_id = manual_create_task(has_user=False)

        # Expect 3 tasks in the ListView
        # Expect 1 + 3 + 1 + 3 + 1= 9 revisions(aka rows) in the TaskContent table.

        el_id = 2  # Legacy support
        return el_id, first_task_id, second_task_id, third_task_id, fourth_task_id, fifth_task_id

    def test_list_no_deleted_tasks(self) -> None:
        """List all tasks. Expect no deleted task."""
        el_id, first_task_id, second_task_id, third_task_id, fourth_task_id, fifth_task_id = self.before_test()
        second_task_response = client.put("/", json={
            "id": second_task_id,
            "title": "Intermediate title",
            "description": "New desc",
            "status": "pending",
            "due_date": "2022-12-31",
            "created_by": el_id
        })
        second_task_final_response = client.put("/", json={
            "id": second_task_id,
            "title": "Final title",
            "description": "Final desc",
            "status": "pending",
            "due_date": "2022-12-31",
            "created_by": el_id
        })

        deleted_response = client.delete(f"/{third_task_id}")

        # Last task in 2 updates and 1 delete
        fourth_task_updated_response = client.put("/", json={
            "id": fourth_task_id,
            "title": "Intermediate title",
            "description": "New desc",
            "status": "pending",
            "due_date": "2022-12-31",
            "created_by": el_id
        })
        fourth_task_last_updated_response = client.put("/", json={
            "id": fourth_task_id,
            "title": "Final title",
            "description": "New desc",
            "status": "pending",
            "due_date": "2022-12-31",
            "created_by": el_id
        })

        fourth_deleted_response = client.delete(f"/{fourth_task_id}")

        list_response = client.get("/")

        assert list_response.status_code == status.HTTP_200_OK
        assert 3 == list_response.json()['count']
        assert second_task_response.status_code == status.HTTP_200_OK
        assert second_task_final_response.status_code == status.HTTP_200_OK
        assert deleted_response.status_code == status.HTTP_200_OK
        assert fourth_task_updated_response.status_code == status.HTTP_200_OK
        assert fourth_task_last_updated_response.status_code == status.HTTP_200_OK
        assert fourth_deleted_response.status_code == status.HTTP_200_OK

    def test_filter_due_date_and_found(self) -> None:
        """Filter by exact due_date."""
        self.before_test()
        response = client.get("/?due_date=2022-12-31")
        assert response.status_code == status.HTTP_200_OK
        assert 5 == response.json()['count']

    def test_filter_due_date_and_not_found(self) -> None:
        """Filter by exact due_date."""
        self.before_test()
        response = client.get("/?due_date=2022-12-3")
        assert response.status_code == status.HTTP_200_OK
        assert 0 == response.json()['count']

    def test_filter_due_date_non_numeric_string(self) -> None:
        """Filter with non-numeric string."""
        response = client.get("/?due_date=some_string")
        assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
        assert response.json() == {'message': [
            {'loc': ['due_date'], 'msg': "Invalid date format. Must be in 'YYYY-MM-DD' format.", 'type': 'ValueError'}]}

    def test_filter_status_and_found(self) -> None:
        """Filter by status."""
        self.before_test()
        response = client.get("/?task_status=pending")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] == 5

    def test_filter_status_and_not_found(self) -> None:
        """Filter by status."""
        self.before_test()
        response = client.get("/?task_status=completed")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] == 0

    def test_filter_due_date_and_status_and_found(self) -> None:
        """Filter by status."""
        self.before_test()
        response = client.get("/?due_date=2022-12-31&task_status=pending")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] == 5

    def test_filter_due_date_and_status_and_not_found(self) -> None:
        """Filter by status."""
        self.before_test()
        response = client.get("/?due_date=2022-12-31&task_status=completed")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] == 0

    def test_filter_created_by_username(self) -> None:
        """Found task based on given username."""
        self.before_test()
        response = client.get("/?created_by__username=test_user")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] == 4

    def test_filter_created_by_username_not_found(self) -> None:
        """Not found task based on given username."""
        self.before_test()
        response = client.get("/?created_by__username=taksin")
        assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
        assert response.json() == {
            'message': [{'loc': ['created_by__username'], 'msg': 'User does not exist.', 'type': 'ValueError'}]}

    def test_filter_due_date_and_status_and_username(self) -> None:
        """Filter by created_by."""
        self.before_test()
        response = client.get("/?due_date=2022-12-31&task_status=pending&created_by__username=test_user")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] == 4

    def test_filter_due_date_and_status_and_wrong_username(self) -> None:
        """Filter by created_by."""
        # User does exist in database, but has no task.
        response = client.get("/?due_date=2022-12-31&task_status=pending&created_by__username=elcolie")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {'count': 0, 'tasks': []}


if __name__ == "__main__":
    unittest.main()
