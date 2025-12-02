from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

from app.schemas.service import ServiceKind


class ActivityLog(Base):
    __tablename__ = "activities-log"

    id = Column(Integer, primary_key=True, index=True)
    log = Column(Text, nullable=False)
    type = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
