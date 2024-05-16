"""Get the instance by following FastAPI."""
import logging

import sqlalchemy
from fastapi import HTTPException
from fastapi import status
from pydantic import ValidationError
from sqlmodel import Session
from sqlmodel import create_engine

from app import DATABASE_URL
from core.common.validate_input import CheckTaskId
from core.models.models import CurrentTaskContent

logger = logging.getLogger(__name__)
engine = create_engine(DATABASE_URL, echo=True)


async def valid_undo_task(task_id: int) -> CheckTaskId:
    try:
        task_instance = CheckTaskId(id=task_id)
    except ValidationError as e:
        logger.error(f"Validation failed UNDO method: {e}")  # pylint: disable=logging-fstring-interpolation
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Unable to undo. Task not found',
        ) from e
    return task_instance


async def valid_task(task_id: int) -> CurrentTaskContent:
    try:
        _ = CheckTaskId(id=task_id)
    except ValidationError as e:
        logger.error(f"Validation failed GET method: {e}")  # pylint: disable=logging-fstring-interpolation
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Task not found'
        ) from e

    with Session(engine) as session:
        try:
            current_task = (
                session.query(CurrentTaskContent)
                .filter(CurrentTaskContent.id == task_id)
                .one()
            )
        except sqlalchemy.orm.exc.NoResultFound as err:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task not found: {task_id}",
            ) from err
        return current_task
