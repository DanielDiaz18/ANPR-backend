from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from enum import Enum


class ServiceStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ServiceKind(str, Enum):
    ENGINE_WASH = "engine_wash"
    EXPRESS_WAX = "express_wax"
    SURFACE_MOISTURIZING = "surface_moisturizing"
    TIRE_SHINE = "tire_shine"


class ServiceBase(BaseModel):
    kind: ServiceKind


class ServiceCreate(ServiceBase):
    plate_id: str


class ServiceUpdate(BaseModel):
    kind: Optional[ServiceKind] = None
    closed_at: Optional[datetime] = None


class ServiceInDBBase(ServiceBase):
    id: int
    vehicle_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Service(ServiceInDBBase):
    pass


class ServiceInDB(ServiceInDBBase):
    pass
