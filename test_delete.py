"""Test DELETE endpoint."""

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlmodel import Session

from app import DATABASE_URL
from main import app
from models import TaskContent, CurrentTaskContent
from test_gadgets import manual_create_task, test_this_func

client = TestClient(app)
engine = create_engine(DATABASE_URL, echo=True)


# Since `create_task()` is own by API. Change a bit to this one.


def test_delete_task() -> None:
    """Test happy path for deleting a task."""
    task_id = manual_create_task()
    response = client.delete(f"/{task_id}")

    with Session(engine) as session:
        # Check history in database
        history = session.query(TaskContent).filter(TaskContent.id == task_id).first()
        assert history.is_deleted is True

        # Check current_task in database
        current = session.query(CurrentTaskContent).filter(CurrentTaskContent.id == task_id).first()
        assert current is None
        assert 0 == session.query(CurrentTaskContent).count()

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Instance deleted successfully!"}


def test_delete_invalid_task() -> None:
    """Test invalid task id."""
    response = client.delete("/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Task not found"}


if __name__ == "__main__":
    test_this_func(test_delete_task)
    test_this_func(test_delete_invalid_task)
