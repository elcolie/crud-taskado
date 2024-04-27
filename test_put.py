"""
Test PUT method for the API.

This script tests the PUT method for the API. It tests the happy path for updating a task, updating a task without created_by, and updating a task with an invalid created_by. It also tests the invalid date format and invalid status.
Instead of clicking the POSTMAN I run this script instead.
Be careful, this script is not intended to run in the CI/CD pipeline.
Because it mutates the database.
"""
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_update_task() -> None:
    """Test happy path for updating a task."""
    response = client.put("/", json={
        "id": 5,
        "title": "New updated title",
        "description": "New desc",
        "status": "pending",
        "due_date": "2022-12-31",
        "created_by": 2
    })
    assert response.status_code == 200
    assert response.json() == {"message": "Instance updated successfully!"}


def test_wrong_due_date() -> None:
    """Test invalid date format."""
    response = client.put("/", json={
        "id": 6,
        "title": "New updated title",
        "description": "New desc",
        "status": "pending",
        "due_date": "2022-12-31T00:00:00",
    })
    assert response.status_code == 422
    assert response.json() == {'detail': [{'type': 'value_error', 'loc': ['body', 'due_date'],
                                           'msg': "Value error, Invalid date format. Must be in 'YYYY-MM-DD' format.",
                                           'input': '2022-12-31T00:00:00', 'ctx': {'error': {}}}]}


def test_wrong_status_and_due_date() -> None:
    """Test wrong more than 1 issue."""
    response = client.put("/", json={
        "id": 6,
        "title": "New updated title",
        "description": "New desc",
        "status": "Invalid status",
        "due_date": "2022-12-31T00:00:00",
    })
    assert response.status_code == 422
    assert response.json() == {'detail': [
        {'type': 'enum', 'loc': ['body', 'status'], 'msg': "Input should be 'pending', 'in_progress' or 'completed'",
         'input': 'Invalid status', 'ctx': {'expected': "'pending', 'in_progress' or 'completed'"}},
        {'type': 'value_error', 'loc': ['body', 'due_date'],
         'msg': "Value error, Invalid date format. Must be in 'YYYY-MM-DD' format.", 'input': '2022-12-31T00:00:00',
         'ctx': {'error': {}}}]}


def test_wrong_id() -> None:
    """Test wrong id."""
    response = client.put("/", json={
        "id": -6,
        "title": "New updated title",
        "description": "New desc",
        "status": "pending",
        "due_date": "2022-12-31",
    })
    assert response.status_code == 422
    assert response.json() == {'detail': [{'type': 'value_error', 'loc': ['body', 'id'], 'msg': 'Value error, Task with this id does not exist', 'input': -6, 'ctx': {'error': {}}}]}


def test_wrong_id_by_string() -> None:
    """Test wrong id."""
    response = client.put("/", json={
        "id": "wrong_id",
        "title": "New updated title",
        "description": "New desc",
        "status": "pending",
        "due_date": "2022-12-31",
    })
    assert response.status_code == 422
    assert response.json() == {'detail': [{'type': 'int_parsing', 'loc': ['body', 'id'], 'msg': 'Input should be a valid integer, unable to parse string as an integer', 'input': 'wrong_id'}]}


if __name__ == "__main__":
    test_update_task()
    test_wrong_due_date()
    test_wrong_status_and_due_date()
    test_wrong_id()
    test_wrong_id_by_string()
