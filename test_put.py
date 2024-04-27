"""
Test PUT method for the API.

Instead of clicking the POSTMAN I run this script instead.
Be careful, this script is not intended to run in the CI/CD pipeline.
Because it mutates the database.
"""
from fastapi.testclient import TestClient

from main import app
from fastapi import status
from test_delete import manual_create_task

client = TestClient(app)


def test_update_task() -> None:
    """Test happy path for updating a task."""
    task_id = manual_create_task()
    response = client.put("/", json={
        "id": task_id,
        "title": "New updated title",
        "description": "New desc",
        "status": "pending",
        "due_date": "2022-12-31",
        "created_by": 2
    })
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Instance updated successfully!"}


def test_wrong_due_date() -> None:
    """Test invalid date format."""
    task_id = manual_create_task()
    response = client.put("/", json={
        "id": task_id,
        "title": "New updated title",
        "description": "New desc",
        "status": "pending",
        "due_date": "2022-12-31T00:00:00",
    })
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {'detail': [{'type': 'value_error', 'loc': ['body', 'due_date'],
                                           'msg': "Value error, Invalid date format. Must be in 'YYYY-MM-DD' format.",
                                           'input': '2022-12-31T00:00:00', 'ctx': {'error': {}}}]}


def test_wrong_status_and_due_date() -> None:
    """Test wrong more than 1 issue."""
    task_id = manual_create_task()
    response = client.put("/", json={
        "id": task_id,
        "title": "New updated title",
        "description": "New desc",
        "status": "Invalid status",
        "due_date": "2022-12-31T00:00:00",
    })
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
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
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {'detail': [
        {'type': 'value_error', 'loc': ['body', 'id'], 'msg': 'Value error, Task with this id does not exist',
         'input': -6, 'ctx': {'error': {}}}]}


def test_wrong_id_by_string() -> None:
    """Test wrong id."""
    response = client.put("/", json={
        "id": "wrong_id",
        "title": "New updated title",
        "description": "New desc",
        "status": "pending",
        "due_date": "2022-12-31",
    })
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {'detail': [{'type': 'int_parsing', 'loc': ['body', 'id'],
                                           'msg': 'Input should be a valid integer, unable to parse string as an integer',
                                           'input': 'wrong_id'}]}


if __name__ == "__main__":
    test_update_task()
    test_wrong_due_date()
    test_wrong_status_and_due_date()
    test_wrong_id()
    test_wrong_id_by_string()
