"""
Test the POST request to create a task.

I made this script because I am lazy to manually test the POST request to create a task by POSTMAN.
NOT INTENTIONALLY TO RUN IN THE CI/CD PIPELINE.
"""
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_post_create_task():
    response = client.post("/create-task/", json={
        "title": "Test Task with created_by",
        "description": "This is a test task",
        "status": "pending",
        "due_date": "2022-12-31",
        "created_by": 1
    })
    assert response.status_code == 200
    assert response.json() == {"message": "Instance created successfully!"}


def test_post_create_task_no_created_by():
    response = client.post("/create-task/", json={
        "title": "Test Task NO created_by",
        "description": "This is a test task",
        "status": "pending",
        "due_date": "2022-12-31",
    })
    assert response.status_code == 200
    assert response.json() == {"message": "Instance created successfully!"}


if __name__ == "__main__":
    test_post_create_task()
    test_post_create_task_no_created_by()
