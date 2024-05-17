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
