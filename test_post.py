"""
Test the POST request to create a task.

I made this script because I am lazy to manually test the POST request to create a task by POSTMAN.
NOT INTENTIONALLY TO RUN IN THE CI/CD PIPELINE.
"""
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_post_create_task() -> None:
    """Test happy path for creating a task."""
    response = client.post("/create-task/", json={
        "title": "Test Task with created_by",
        "description": "This is a test task",
        "status": "pending",
        "due_date": "2022-12-31",
        "created_by": 1
    })
    assert response.status_code == 200
    assert response.json() == {"message": "Instance created successfully!"}


def test_post_create_task_no_created_by() -> None:
    """Test happy path for creating a task without created_by."""
    response = client.post("/create-task/", json={
        "title": "Test Task NO created_by",
        "description": "This is a test task",
        "status": "pending",
        "due_date": "2022-12-31",
    })
    assert response.status_code == 200
    assert response.json() == {"message": "Instance created successfully!"}


def test_post_invalid_created_by() -> None:
    """Test created_by validator."""
    response = client.post("/create-task/", json={
        "title": "Test Task NO created_by",
        "description": "This is a test task",
        "status": "pending",
        "due_date": "2022-12-31",
        "created_by": 999
    })
    assert response.status_code == 422
    assert response.json() == {'detail': [{'type': 'value_error', 'loc': ['body', 'created_by'], 'msg': 'Value error, User with this id does not exist', 'input': 999, 'ctx': {'error': {}}}]}


def test_invalid_date_format() -> None:
    """Test invalid date format."""
    response = client.post("/create-task/", json={
        "title": "Test Task NO created_by",
        "description": "This is a test task",
        "status": "pending",
        "due_date": "2022-12-31T00:00:00",
    })
    assert response.status_code == 422
    assert response.json() == {'detail': [{'type': 'value_error', 'loc': ['body', 'due_date'], 'msg': "Value error, Invalid date format. Must be in 'YYYY-MM-DD' format.", 'input': '2022-12-31T00:00:00', 'ctx': {'error': {}}}]}


def test_invalid_status() -> None:
    """Test invalid status."""
    response = client.post("/create-task/", json={
        "title": "Test Task NO created_by",
        "description": "This is a test task",
        "status": "invalid_status",
        "due_date": "2022-12-31",
    })
    assert response.status_code == 422
    assert response.json() == {'detail': [{'type': 'enum', 'loc': ['body', 'status'], 'msg': "Input should be 'pending', 'in_progress' or 'completed'", 'input': 'invalid_status', 'ctx': {'expected': "'pending', 'in_progress' or 'completed'"}}]}


def test_invalid_status_and_due_date_and_wrong_created_by() -> None:
    """Test invalid status and due_date."""
    response = client.post("/create-task/", json={
        "title": "Test Task NO created_by",
        "description": "This is a test task",
        "status": "invalid_status",
        "due_date": "2022-12-31T00:00:00",
        "created_by": 999
    })
    assert response.status_code == 422
    assert 3 == len(response.json()['detail'])
    assert response.json() == {'detail': [{'type': 'enum', 'loc': ['body', 'status'], 'msg': "Input should be 'pending', 'in_progress' or 'completed'", 'input': 'invalid_status', 'ctx': {'expected': "'pending', 'in_progress' or 'completed'"}}, {'type': 'value_error', 'loc': ['body', 'due_date'], 'msg': "Value error, Invalid date format. Must be in 'YYYY-MM-DD' format.", 'input': '2022-12-31T00:00:00', 'ctx': {'error': {}}}, {'type': 'value_error', 'loc': ['body', 'created_by'], 'msg': 'Value error, User with this id does not exist', 'input': 999, 'ctx': {'error': {}}}]}


if __name__ == "__main__":
    test_post_create_task()
    test_post_create_task_no_created_by()
    test_post_invalid_created_by()
    test_invalid_date_format()
    test_invalid_status()
    test_invalid_status_and_due_date_and_wrong_created_by()
