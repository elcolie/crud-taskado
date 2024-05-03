"""Code of pagination."""
import enum

from pydantic import BaseModel


class SortEnum(enum.Enum):
    """Sort enum."""
    ASC = 'asc'
    DESC = 'desc'


class Pagination(BaseModel):
    """Pagination model."""
    perPage: int
    page: int
    order: SortEnum


def generate_query_params(
    due_date: str | None = None,
    task_status: str | None = None,
    created_by__username: str | None = None,
    updated_by__username: str | None = None,
    _page_number: int = 1,  # Page number
    _per_page: int = 10,  # Number of items per page
) -> str:
    """Generate query params."""
    query_params = []
    if due_date:
        query_params.append(f"due_date={due_date}")
    if task_status:
        query_params.append(f"task_status={task_status}")
    if created_by__username:
        query_params.append(f"created_by__username={created_by__username}")
    if updated_by__username:
        query_params.append(f"updated_by__username={updated_by__username}")
    if _page_number:
        query_params.append(f"_page_number={_page_number}")
    if _per_page:
        query_params.append(f"_per_page={_per_page}")
    query_params[0] = '?' + query_params[0]  # Add ? to the first element
    return '&'.join(query_params)
