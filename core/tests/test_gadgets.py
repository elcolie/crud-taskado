"""The utilities for testing the gadgets module."""
import typing as typ

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, desc
from sqlmodel import Session

from app import DATABASE_URL
from main import app
from core.models.models import CurrentTaskContent, TaskContent, User

client = TestClient(app)

# Create the database engine
engine = create_engine(DATABASE_URL, echo=True)


def prepare_users_for_test() -> None:
    """Create user for test."""
    with Session(engine) as session:
        session.query(User).delete()  # Remove all users
        session.commit()

        session.bulk_save_objects(
            [
                User(id=1, username='sarit'),
                User(id=2, username='elcolie'),
                User(id=10, username='test_user'),
            ]
        )
        session.commit()


def remove_all_tasks_and_users() -> None:
    """Remove all tasks history and current one."""

    with Session(engine) as session:
        session.query(TaskContent).delete()
        session.query(CurrentTaskContent).delete()
        session.query(User).delete()
        session.commit()


def test_this_func(test_case: typ.Callable) -> None:
    """
    Wrapper function to test.

    Start fresh everytime.
    Wrap with remove_all_tasks()

    """

    def wrapper():
        remove_all_tasks_and_users()
        prepare_users_for_test()
        test_case()
        remove_all_tasks_and_users()

    return wrapper()


def manual_create_task(
    has_user: bool = True,
    user_id: int = 10,
    title: str = 'Test Task with created_by',
    description: str = 'This is a test task',
    _status: str = 'pending',
    due_date: str = '2022-12-31',
) -> int:
    """Helper function to create a task with user."""
    if has_user:
        response_a = client.post(
            '/create-task/',
            json={
                'title': title,
                'description': description,
                'status': _status,
                'due_date': due_date,
                'created_by': user_id,
            },
        )
        # Raise error if unable to create user.
        assert response_a.status_code == status.HTTP_201_CREATED
    else:
        response_b = client.post(
            '/create-task/',
            json={
                'title': 'Test Task NO created_by',
                'description': 'This is a test task',
                'status': 'pending',
                'due_date': '2022-12-31',
            },
        )
        # Raise error if unable to create user.
        assert response_b.status_code == status.HTTP_201_CREATED

    with Session(engine) as session:
        task = (
            session.query(CurrentTaskContent)
            .order_by(desc(CurrentTaskContent.id))
            .first()
        )
    return task.id
