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
        "title": "Test Task",
        "description": "This is a test task",
        "status": "pending",
        "due_date": "2022-12-31",
        "created_by": 1
    })
    assert response.status_code == 200
    assert response.json() == {"message": "Task created successfully!"}


if __name__ == "__main__":
    test_post_create_task()
