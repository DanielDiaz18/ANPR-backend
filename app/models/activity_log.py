from sqlalchemy_serializer import SerializerMixin
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
    JSON,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class ActionType(str, enum.Enum):
    """Enum for different action types"""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    READ = "read"
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    SEARCH = "search"
    EXPORT = "export"
    IMPORT = "import"
    UPLOAD = "upload"
    DOWNLOAD = "download"


class EntityType(str, enum.Enum):
    """Enum for different entity types"""

    USER = "user"
    VEHICLE = "vehicle"
    CLIENT = "client"
    SERVICE = "service"
    AUTH = "auth"
    SYSTEM = "system"


class ActivityLog(Base):  # , SerializerMixin):
    """Model for tracking all user actions and transactions"""

    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)

    # User who performed the action
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Action details
    action_type = Column(Enum(ActionType), nullable=False, index=True)
    entity_type = Column(Enum(EntityType), nullable=False, index=True)
    entity_id = Column(Integer, nullable=True)  # ID of the affected entity

    description = Column(Text, nullable=False)
    meta = Column(
        JSON, nullable=True
    )  # Additional data like request body, changes, etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationship
    user = relationship("User", backref="activity_logs")
