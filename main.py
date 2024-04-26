import typing as typ
from datetime import date
import uuid
from fastapi import FastAPI
from sqlalchemy import func
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlmodel import Session
# Database connection url
from app import DATABASE_URL
from models import StatusEnum, GenericTask, TaskContent
from validate_input import GenericTaskInput

# Create the database engine
engine = create_engine(DATABASE_URL, echo=True)

app = FastAPI()

def parse_date(date_str: str) -> date:
    """Function to parse date string."""
    try:
        year, month, day = date_str.split("-")
        return date(int(year), int(month), int(day))
    except ValueError:
        raise ValidationError("Invalid date format. Must be in 'YYYY-MM-DD' format.")


@app.post("/create-task/")
async def create_task(task_dict: typ.Dict):
    """Endpoint to create a task."""
    task_data = task_dict.get('task')
    try:
        task_data = {  # Assuming you have some data here
            "title": task_data.get('title'),
            "description": task_data.get('description'),
            "due_date": task_data.get('due_date'),
            "status": task_data.get('status'),
            "created_by": task_data.get('created_by'),
        }
        instance = GenericTaskInput(**task_data)
        print("Validation successful!")
    except ValidationError as e:
        print(f"Validation failed: {e}")
        return {
            'message': e.errors(),
        }
    else:
        # Validation successful, save the data to the database
        with Session(engine) as session:
            # Parse the due_date string to date object
            task_data['due_date'] = parse_date(instance.due_date)

            # Generate a unique identifier for the task
            _identifier = uuid.uuid4().hex

            # id is for human reference, identifier is for redo mechanism
            _max_id = session.query(func.max(GenericTask.id)).scalar()
            max_id = 0 if _max_id is None else _max_id
            id = max_id + 1

            new_task = GenericTask(**{
                'id': id,
                'identifier': _identifier,
            })
            import ipdb;
            ipdb.set_trace()
            new_content = TaskContent(**{
                'id': id,
                'identifier': _identifier,
                **task_data,
            })
            session.add(new_task)
            session.add(new_content)
            session.commit()
    return {
        'message': "I am good",
    }
