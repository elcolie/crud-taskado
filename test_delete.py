"""Test DELETE endpoint."""
import uuid
from datetime import date, datetime

import sqlalchemy
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlmodel import Session
from sqlalchemy import desc


from app import DATABASE_URL
from main import app
from models import TaskContent, User

client = TestClient(app)
engine = create_engine(DATABASE_URL, echo=True)


def create_task() -> int:
    """Helper function to create a task with user."""
    user_id = 10
    with Session(engine) as session:
        # Add a user
        try:
            user = User(
                id=user_id,
                username="test_user"
            )
            session.add(user)
            session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            print(f">> {e}")
            print(">> User exists no create new one.")
            session.rollback()
            # user = session.get(User, 10)

        latest_id = session.query(TaskContent.id).order_by(desc(TaskContent.id)).first()

        # Extract the latest id
        latest_id_value = latest_id[0] if latest_id else 1

        # Add a task
        task = TaskContent(
            id=latest_id_value + 1,
            identifier=uuid.uuid4().hex,
            title="Test Task with created_by",
            description="This is a test task",
            status="pending",
            due_date=date(2099, 12, 31),
            created_by=user_id,
            created_at=datetime.now(),  # On my OSX it is Bangkok time not UTC.
            updated_at=datetime.now(),
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        return task.id


def test_delete_task() -> None:
    """Test happy path for deleting a task."""
    task_id = create_task()
    response = client.delete(f"/{task_id}")
    assert response.status_code == 200
    assert response.json() == {"message": "Instance deleted successfully!"}


def test_delete_invalid_task() -> None:
    """Test invalid task id."""
    response = client.delete("/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


if __name__ == "__main__":
    test_delete_task()
    test_delete_invalid_task()
