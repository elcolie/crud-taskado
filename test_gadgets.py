"""The utilities for testing the gadgets module."""
import typing as typ

from sqlmodel import Session

from app import DATABASE_URL
from models import User, TaskContent, CurrentTaskContent

from sqlalchemy import create_engine

# Create the database engine
engine = create_engine(DATABASE_URL, echo=True)


def prepare_users_for_test() -> None:
    """Create user for test."""
    with Session(engine) as session:
        session.query(User).delete()    # Remove all users
        session.commit()

        session.bulk_save_objects([
            User(id=1, username="sarit"),
            User(id=2, username="elcolie"),
            User(id=10, username="test_user"),
        ])
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
