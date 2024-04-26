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
from serializers import TaskContentSchema
from validate_input import GenericTaskInput
from pydantic import BaseModel
# Create the database engine
engine = create_engine(DATABASE_URL, echo=True)

app = FastAPI()

class ErrorDetail(BaseModel):
    """Error details model."""
    loc: typ.List[str]
    msg: str
    type: str


class TaskValidationError(BaseModel):
    """Task validation error model."""
    message: str
    errors: typ.List[ErrorDetail]


def parse_date(date_str: str) -> date:
    """Function to parse date string."""
    try:
        year, month, day = date_str.split("-")
        return date(int(year), int(month), int(day))
    except ValueError:
        raise ValidationError("Invalid date format. Must be in 'YYYY-MM-DD' format.")


@app.post("/create-task/")
async def create_task(task_dict: typ.Dict, response_model=typ.Union[typ.Type[TaskValidationError], typ.Dict[str, str]]) -> typ.Any:
    """Endpoint to create a task."""
    task_data = task_dict.get('task')
    try:
        task_data = {  # Assuming you have some data here
            "title": task_data.get('title'),
            "description": task_data.get('description'),
            "due_date": task_data.get('due_date'),
            "status": task_data.get('status'),
            # "created_by": task_data.get('created_by'),
        }
        instance = GenericTaskInput(**task_data)
        print("Validation successful!")
    except ValidationError as e:
        print(f"Validation failed: {e}")
        # Very curious why I can't return a list of errors.
        return {
            'message': "Validation failed!",
            # str() because of *** TypeError: Object of type ValueError is not JSON serializable
            'errors': [
                {
                    'type': error['type'],
                    'loc': error['loc'],
                    'msg': error['msg'],
                }
                for error in
                e.errors()
            ],
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
            new_content = TaskContent(**{
                'id': id,
                'identifier': _identifier,
                **task_data,
            })
            session.add(new_task)
            session.add(new_content)
            session.commit()
    return {
        'message': "Instance created successfully!",
    }


@app.get("/")
async def list_tasks() -> typ.Dict[str, typ.Any]:
    """Endpoint to list all tasks."""
    with Session(engine) as session:
        task_content_schema = TaskContentSchema()
        tasks = (
            session.query(TaskContent)
            .filter(
                TaskContent.id.in_(
                    session.query(GenericTask.id).filter(GenericTask.is_deleted == False)
                )
            )
            .all()
        )
        serialized_tasks = task_content_schema.dump(tasks, many=True)
        return {
            'tasks': serialized_tasks,
        }

@app.get("/task/{task_id}")
async def get_task(task_id: int):
    """Endpoint to get a task by id."""
    with Session(engine) as session:
        task_content_schema = TaskContentSchema()
        task = session.query(TaskContent).filter(TaskContent.id == task_id).first()
        serialized_task = task_content_schema.dump(task)
        return {
            'task': serialized_task,
        }

@app.put("/{task_id}")
async def update_task(task_id: int, payload: typ.Dict):
    """Endpoint to update a task."""
    with Session(engine) as session:
        task_content_schema = TaskContentSchema()
        task = session.query(TaskContent).filter(TaskContent.id == task_id).first()

        # In order to do undo mechanism. Create a new instance of the task.
        new_identifier = uuid.uuid4().hex
        new_task = GenericTask(**{
            'id': task.id,  # Use the same id
            'identifier': new_identifier, # Generate a new identifier
        })

        new_content = TaskContent(**{
            'id': task.id,
            'identifier': new_identifier,
            **payload,
        })
        session.add(new_task)
        session.add(new_content)
        session.commit()

