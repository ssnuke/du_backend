import sqlmodel
from sqlmodel import SQLModel, Session
from .config import DATABASE_URL

if DATABASE_URL == "":
    raise NotImplementedError("DATABASE_URL needs to be set!!!")

engine = sqlmodel.create_engine(DATABASE_URL)

def init_db():
    try:
        print("Creating tables")
        SQLModel.metadata.create_all(engine)
    except Exception as e:
        print(f"Error creating tables: {e}")

def reset_db():
    """Drops all tables and recreates them"""
    try:
        print("Resetting database...")
        SQLModel.metadata.drop_all(engine)   # Drop all existing tables
        SQLModel.metadata.create_all(engine) # Recreate tables
        print("✅ Database reset successful!")
    except Exception as e:
        print(f"Error resetting database: {e}")

def get_session():
    with Session(engine) as session:
        yield session