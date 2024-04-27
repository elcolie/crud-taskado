from decouple import config
from sqlmodel import create_engine, Session, SQLModel  # SQLModel will be import from env.py

DATABASE_URL = config('DATABASE_URL')

engine = create_engine(DATABASE_URL, echo=True)
