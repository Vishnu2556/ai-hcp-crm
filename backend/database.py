import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# postgresql+psycopg2://<user>:<password>@<host>:5432/<db_name>
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://hcp_user:hcp_pass@localhost:5432/hcp_crm",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()