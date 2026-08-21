import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.app.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


def get_engine():
    db_url = settings.sync_database_url
    try:
        if db_url.startswith("sqlite"):
            engine = create_engine(
                db_url,
                connect_args={"check_same_thread": False},
                echo=False,
            )
        else:
            # MySQL with PyMySQL
            engine = create_engine(
                db_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False,
            )
            # Try a lightweight connection test
            with engine.connect() as conn:
                pass
            logger.info(f"Connected successfully to database: {db_url.split('@')[-1] if '@' in db_url else db_url}")
        return engine
    except Exception as e:
        logger.warning(
            f"Could not connect to {db_url} ({e}). Falling back to local SQLite database."
        )
        # Fallback to local SQLite so development/testing never blocks
        fallback_url = "sqlite:///./procureai.db"
        return create_engine(
            fallback_url,
            connect_args={"check_same_thread": False},
            echo=False,
        )


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
