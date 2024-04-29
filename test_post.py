"""
Test the POST request to create a task.

I made this script because I am lazy to manually test the POST request to create a task by POSTMAN.
NOT INTENTIONALLY TO RUN IN THE CI/CD PIPELINE.
"""
from datetime import date

from sqlmodel import select

from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy import create_engine
from sqlmodel import Session

from app import DATABASE_URL
from main import app
from models import TaskContent, CurrentTaskContent, StatusEnum
from test_gadgets import test_this_func

# Create the database engine
engine = create_engine(DATABASE_URL, echo=True)


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
    with Session(engine) as session:
        task = session.exec(
            select(TaskContent)
            .where(TaskContent.title == "Test Task with created_by")
        ).one()
        assert task.title == "Test Task with created_by"
        assert task.description == "This is a test task"
        assert task.status == StatusEnum.pending
        assert task.due_date == date(2022, 12, 31)
        assert task.created_by == 1

        current_task = session.exec(select(CurrentTaskContent).where(CurrentTaskContent.id == task.id)).one()
        assert current_task.identifier == task.identifier
        assert current_task.id == task.id
        assert current_task.created_by == 1
        assert current_task.updated_by == 1
        assert current_task.created_at == task.created_at
        assert current_task.updated_at == task.created_at

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"message": "Instance created successfully!"}


def test_post_create_task_no_created_by() -> None:
    """Test happy path for creating a task without created_by."""
    response = client.post("/create-task/", json={
        "title": "Test Task NO created_by",
        "description": "This is a test task",
        "status": "pending",
        "due_date": "2022-12-31",
    })
    assert response.status_code == status.HTTP_201_CREATED
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
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {'detail': [{'type': 'value_error', 'loc': ['body', 'created_by'], 'msg': 'Value error, User with this id does not exist', 'input': 999, 'ctx': {'error': {}}}]}


def test_invalid_date_format() -> None:
    """Test invalid date format."""
    response = client.post("/create-task/", json={
        "title": "Test Task NO created_by",
        "description": "This is a test task",
        "status": "pending",
        "due_date": "2022-12-31T00:00:00",
    })
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {'detail': [{'type': 'value_error', 'loc': ['body', 'due_date'], 'msg': "Value error, Invalid date format. Must be in 'YYYY-MM-DD' format.", 'input': '2022-12-31T00:00:00', 'ctx': {'error': {}}}]}


def test_invalid_status() -> None:
    """Test invalid status."""
    response = client.post("/create-task/", json={
        "title": "Test Task NO created_by",
        "description": "This is a test task",
        "status": "invalid_status",
        "due_date": "2022-12-31",
    })
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
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
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert 3 == len(response.json()['detail'])
    assert response.json() == {'detail': [{'type': 'enum', 'loc': ['body', 'status'], 'msg': "Input should be 'pending', 'in_progress' or 'completed'", 'input': 'invalid_status', 'ctx': {'expected': "'pending', 'in_progress' or 'completed'"}}, {'type': 'value_error', 'loc': ['body', 'due_date'], 'msg': "Value error, Invalid date format. Must be in 'YYYY-MM-DD' format.", 'input': '2022-12-31T00:00:00', 'ctx': {'error': {}}}, {'type': 'value_error', 'loc': ['body', 'created_by'], 'msg': 'Value error, User with this id does not exist', 'input': 999, 'ctx': {'error': {}}}]}


if __name__ == "__main__":
    test_this_func(test_post_create_task)
    test_this_func(test_post_create_task_no_created_by)
    test_this_func(test_post_invalid_created_by)
    test_this_func(test_invalid_date_format)
    test_this_func(test_invalid_status)
    test_this_func(test_invalid_status_and_due_date_and_wrong_created_by)
