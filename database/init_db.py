import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import engine, Base
import backend.app.models  # register all models


def init_db(drop_first: bool = False):
    """
    Initializes database tables.
    If drop_first is True, drops all existing tables before re-creating.
    """
    print(f"Connecting to database engine: {engine.url}")
    if drop_first:
        print("Dropping existing tables...")
        Base.metadata.drop_all(bind=engine)
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully!")


if __name__ == "__main__":
    drop = "--drop" in sys.argv or "-d" in sys.argv
    init_db(drop_first=drop)
