from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    model = Column(String, nullable=True)
    brand = Column(String, nullable=True)
    plate_id = Column(String, unique=True, index=True, nullable=False)
    # description = Column(Text)
    # is_active = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("clients.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    services = relationship("Service", back_populates="vehicle")
    client = relationship("Client", back_populates="vehicles")
