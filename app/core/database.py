from sqlalchemy_serializer import SerializerMixin

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base(cls=SerializerMixin)
metadata = Base.metadata


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    # Import all models here to ensure they are registered with Base

    Base.metadata.create_all(bind=engine)
