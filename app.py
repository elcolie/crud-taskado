"""Main for database connection."""
from decouple import config
from sqlalchemy import create_engine

# Database connection url
DATABASE_URL = config('DATABASE_URL')

# Create the database engine
# Add extra pool_size and max_overflow
# because of sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached
engine = create_engine(DATABASE_URL, echo=True, pool_size=20, max_overflow=40)
