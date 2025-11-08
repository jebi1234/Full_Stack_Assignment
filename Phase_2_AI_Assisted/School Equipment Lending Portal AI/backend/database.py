# File: backend/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Define the database URL. 
# 'sqlite:///./equipment.db' means it will create a file named 'equipment.db'
# in your current 'backend' directory.
SQLALCHEMY_DATABASE_URL = "sqlite:///./equipment.db"

# 2. Create the SQLAlchemy engine
# 'check_same_thread' is only needed for SQLite.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. Create a SessionLocal class
# This is what you'll use to create database sessions in your API.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Create a Base class
# All your database table models (like User, Equipment, etc.)
# will inherit from this class.
Base = declarative_base()

# File: backend/database.py


# --- ADD THIS FUNCTION AT THE BOTTOM ---

def get_db():
    """
    Database dependency generator.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()