import enum

from pydantic import BaseModel


class SortEnum(enum.Enum):
    ASC = "asc"
    DESC = "desc"


class Pagination(BaseModel):
    perPage: int
    page: int
    order: SortEnum

