import typing as typ
from datetime import date

from fastapi import FastAPI
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlmodel import Session
# Database connection url
from app import DATABASE_URL
from models import StatusEnum, GenericTask
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
        import ipdb;
        ipdb.set_trace()
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
            task_data['due_date'] = parse_date(instance.due_date)
            new_task = GenericTask(**task_data)
            session.add(new_task)
            session.commit()
    return {
        'message': "I am good",
    }
