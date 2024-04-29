"""Test GET detail by specify task_id."""
import sys

from fastapi.testclient import TestClient
from fastapi import status
from main import app
from test_gadgets import manual_create_task

client = TestClient(app)


def get_valid_task_detail() -> None:
    """Happy path get correct instance."""
    task_id = manual_create_task()
    response = client.get(f"/{task_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'title': 'Test Task with created_by', 'description': 'This is a test task',
                               'status': 'pending', 'due_date': '2099-12-31', 'created_by': 10, 'id': task_id}


def use_wrong_id() -> None:
    """Test wrong id."""
    task_id = manual_create_task()
    response = client.get(f"/{task_id + 999}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Task not found'}


def use_negative_id() -> None:
    """Test negative id."""
    task_id = manual_create_task()
    response = client.get(f"/{task_id - sys.maxsize}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Task not found'}


def use_string_id() -> None:
    """Test string id."""
    _ = manual_create_task()
    response = client.get(f"/some-string")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY  # Because raises by BaseModel
    assert response.json() == {'detail': [{'type': 'int_parsing', 'loc': ['path', 'task_id'],
                                           'msg': 'Input should be a valid integer, unable to parse string as an integer',
                                           'input': 'some-string'}]}


def get_deleted_task() -> None:
    """Test get deleted task."""
    task_id = manual_create_task()
    deleted_response = client.delete(f"/{task_id}")
    get_response = client.get(f"/{task_id}")
    assert deleted_response.status_code == status.HTTP_200_OK
    assert get_response.status_code == status.HTTP_404_NOT_FOUND  # Because raises by BaseModel
    assert get_response.json() == {'detail': 'Task is deleted'}


if __name__ == "__main__":
    get_valid_task_detail()
    use_wrong_id()
    use_negative_id()
    use_string_id()
    get_deleted_task()
