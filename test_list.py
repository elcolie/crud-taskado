"""Test LIST, filter, and pagination."""
import typing as typ

import sqlalchemy
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlmodel import Session

from app import DATABASE_URL
from main import app
from models import User
from test_gadgets import test_this_func, manual_create_task

client = TestClient(app)

# Create the database engine
engine = create_engine(DATABASE_URL, echo=True)


def before_test() -> typ.Tuple[
    int, int, int, int, int, int
]:
    """Prepare the data for testing."""
    el_id = 2
    with Session(engine) as session:
        # Add a user
        try:
            user = User(
                id=el_id,
                username="elcolie"
            )
            session.add(user)
            session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            print(f">> {e}")
            print(">> User exists no create new one.")
            session.rollback()

    first_task_id = manual_create_task()
    second_task_id = manual_create_task()  # Update 2 times
    third_task_id = manual_create_task()  # Delete
    fourth_task_id = manual_create_task()  # Update 2 time and delete
    fifth_task_id = manual_create_task(has_user=False)

    # Expect 3 tasks in the ListView
    # Expect 1 + 3 + 1 + 3 + 1= 9 revisions(aka rows) in the TaskContent table.

    return el_id, first_task_id, second_task_id, third_task_id, fourth_task_id, fifth_task_id


def list_no_deleted_tasks() -> None:
    """List all tasks. Expect no deleted task."""
    el_id, first_task_id, second_task_id, third_task_id, fourth_task_id, fifth_task_id = before_test()
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


def filter_due_date_and_found() -> None:
    """Filter by exact due_date."""
    before_test()
    response = client.get("/?due_date=2022-12-31")
    assert response.status_code == status.HTTP_200_OK
    assert 5 == response.json()['count']


def filter_due_date_and_not_found() -> None:
    """Filter by exact due_date."""
    before_test()
    response = client.get("/?due_date=2022-12-3")
    assert response.status_code == status.HTTP_200_OK
    assert 0 == response.json()['count']


def filter_due_date_non_numeric_string() -> None:
    """Filter with non-numeric string."""
    response = client.get("/?due_date=some_string")


def filter_due_date_and_status() -> None:
    """Filter by status."""
    pass


def filter_due_date_and_status_and_username_all_wrong() -> None:
    """Filter by created_by."""
    response = client.get("/?due_date=2099-99-31&task_status=invalid_string&created_by__username=999")
    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
    assert response.json() == {'message': [
        {'loc': ['due_date'], 'msg': "Invalid date format. Must be in 'YYYY-MM-DD' format.", 'type': 'ValueError'},
        {'loc': ['status'], 'msg': 'StatusEnum is invalid status value.', 'type': 'ValueError'},
        {'loc': ['created_by__username'], 'msg': 'User does not exist.', 'type': 'ValueError'}]}


if __name__ == "__main__":
    # test_this_func(list_no_deleted_tasks)
    # test_this_func(filter_due_date_and_status_and_username_all_wrong)
    # test_this_func(filter_due_date_and_found)
    # test_this_func(filter_due_date_and_not_found)
    pass
