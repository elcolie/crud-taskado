"""Main for database connection."""
from decouple import config

DATABASE_URL = config('DATABASE_URL')
