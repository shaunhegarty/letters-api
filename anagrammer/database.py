import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

POSTGRES_HOSTNAME = os.environ.get("POSTGRES_HOSTNAME", "localhost")
SQLALCHEMY_DATABASE_URL = f"postgresql://api:letters@{POSTGRES_HOSTNAME}/words"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)