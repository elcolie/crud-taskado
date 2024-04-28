"""Test LIST, filter, and pagination."""

import sqlalchemy
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlmodel import Session

from app import DATABASE_URL
from main import app
from models import TaskContent, User
from test_delete import manual_create_task

client = TestClient(app)

# Create the database engine
engine = create_engine(DATABASE_URL, echo=True)


def remove_all_tasks() -> None:
    """Remove all tasks in table first."""

    with Session(engine) as session:
        session.query(TaskContent).delete()
        session.commit()


def list_no_deleted_tasks() -> None:
    """List all tasks. Expect no deleted task."""
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
    fifth_task_id = manual_create_task()  # CAUTION. created_by is None list_tasks will fail.

    # Expect 3 tasks in the ListView
    # Expect 1 + 3 + 1 + 3 + 1= 9 revisions(aka rows) in the TaskContent table.

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
        "description": "New desc",
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


if __name__ == "__main__":
    remove_all_tasks()
    list_no_deleted_tasks()
