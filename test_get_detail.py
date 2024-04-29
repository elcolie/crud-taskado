"""Test GET detail by specify task_id."""
import typing as typ
import sys
import time

import httpx
from fastapi.testclient import TestClient
from fastapi import status
from main import app
from test_gadgets import manual_create_task, test_this_func

client = TestClient(app)


def get_valid_task_detail() -> None:
    """Happy path get correct instance."""
    task_id = manual_create_task()
    response = client.get(f"/{task_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'title': 'Test Task with created_by', 'description': 'This is a test task',
                               'status': 'pending', 'due_date': '2022-12-31', 'created_by': 10, 'id': 1}


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
    assert get_response.json() == {'detail': f'Task not found: {task_id}'}


def make_task_with_two_updates() -> typ.Tuple[
    int, httpx.Response, httpx.Response
]:
    """Make two updates."""
    task_id = manual_create_task()
    first_response = client.put("/", json={
        "id": task_id,
        "title": "First updated title",
        "description": "First updated desc",
        "status": "pending",
        "due_date": "2029-12-31",
        "created_by": 2
    })
    second_response = client.put("/", json={
        "id": task_id,
        "title": "Second updated title",
        "description": "Second updated desc",
        "status": "pending",
        "due_date": "2099-12-31",
        "created_by": 1
    })
    return task_id, first_response, second_response


def update_two_times_then_get() -> None:
    """Update 2 times and then GET the task. Expect found the instance."""
    task_id, first_response, second_response = make_task_with_two_updates()

    # GET the instance
    get_response = client.get(f"/{task_id}")
    assert first_response.status_code == status.HTTP_200_OK
    assert second_response.status_code == status.HTTP_200_OK
    assert get_response.status_code == status.HTTP_200_OK


def update_two_times_then_delete() -> None:
    """Update 2 times and then delete. Expect not found the task."""
    task_id, first_response, second_response = make_task_with_two_updates()

    # Delete the task
    deleted_response = client.delete(f"/{task_id}")

    # GET the instance
    get_response = client.get(f"/{task_id}")
    assert first_response.status_code == status.HTTP_200_OK
    assert second_response.status_code == status.HTTP_200_OK
    assert deleted_response.status_code == status.HTTP_200_OK
    assert get_response.status_code == status.HTTP_404_NOT_FOUND
    assert get_response.json() == {'detail': f'Task not found: {task_id}'}


if __name__ == "__main__":
    test_this_func(get_valid_task_detail)
    test_this_func(use_wrong_id)
    test_this_func(use_negative_id)
    test_this_func(use_string_id)
    test_this_func(get_deleted_task)
    test_this_func(update_two_times_then_get)
    test_this_func(update_two_times_then_delete)
