"""Get the queryset of tasks."""
import typing as typ
from datetime import date

import sqlalchemy
from sqlalchemy import and_, or_
from sqlmodel import Session

from app import engine
from core.models.models import (CurrentTaskContent, StatusEnum, TaskContent,
                                User)


def get_queryset(
    _due_date: typ.Optional[date],
    _status: typ.Optional[StatusEnum],
    _created_user: typ.Optional[User],
    _updated_user: typ.Optional[User],
) -> sqlalchemy.orm.query.Query:
    """Get the queryset of tasks."""
    with Session(engine) as session:
        if _updated_user is not None and _created_user is not None:
            # List out available id.
            available_id_list = (
                session.query(CurrentTaskContent)
                .filter(
                    or_(
                        CurrentTaskContent.updated_by == _updated_user.id,
                        _updated_user is None,
                    ),
                    or_(
                        CurrentTaskContent.created_by == _created_user.id,
                        _created_user is None,
                    ),
                )
                .all()
            )
        elif _updated_user is None and _created_user is not None:
            available_id_list = (
                session.query(CurrentTaskContent)
                .filter(
                    or_(
                        CurrentTaskContent.created_by == _created_user.id,
                        _created_user is None,
                    )
                )
                .all()
            )
        elif _updated_user is not None and _created_user is None:
            available_id_list = (
                session.query(CurrentTaskContent)
                .filter(
                    or_(
                        CurrentTaskContent.updated_by == _updated_user.id,
                        _updated_user is None,
                    ),
                )
                .all()
            )
        else:
            # elif _updated_user is None and _user is None:
            available_id_list = session.query(CurrentTaskContent).all()

        cleaned_id_list = [i.id for i in available_id_list]

        # Find the latest identifier from available_id_list
        _identifier_list = (
            session.query(CurrentTaskContent.identifier)
            .filter(CurrentTaskContent.id.in_(cleaned_id_list))  # type: ignore[attr-defined]  # pylint: disable=no-member  # noqa: E501
            .all()
        )
        cleaned_identifier_list = [i[0] for i in _identifier_list]

        final_query = (
            session.query(
                CurrentTaskContent,
                TaskContent,
                User,
            )
            .outerjoin(
                TaskContent,
                and_(
                    CurrentTaskContent.id == TaskContent.id,
                    CurrentTaskContent.identifier == TaskContent.identifier,
                    TaskContent.is_deleted == False,    # noqa: E712  # pylint: disable=singleton-comparison  # noqa: E501
                ),
            )
            .outerjoin(
                User,
                or_(TaskContent.created_by == User.id, TaskContent.created_by is None),  # noqa: E501  # pylint: disable=line-too-long
            )
            .filter(
                TaskContent.due_date == _due_date if _due_date else True,
                TaskContent.status == _status if _status else True,  # pylint: disable=no-member
                CurrentTaskContent.identifier.in_(cleaned_identifier_list),     # type: ignore[attr-defined]  # noqa: 501  # pylint: disable=line-too-long, no-member
            )
            .filter(
                or_(
                    CurrentTaskContent.created_by == _created_user.id
                    if _created_user is not None
                    else None,
                    _created_user is None,
                )
            )
            .filter(
                or_(
                    CurrentTaskContent.updated_by == _updated_user.id
                    if _updated_user is not None
                    else None,
                    _updated_user is None,
                )
            )
            .order_by(TaskContent.id.asc())  # type: ignore[attr-defined]  # pylint: disable=no-member  # noqa: E501
        )
        return final_query
