"""Main for database connection."""
from decouple import config
from sqlmodel import create_engine

DATABASE_URL = config('DATABASE_URL')

engine = create_engine(DATABASE_URL, echo=True)
