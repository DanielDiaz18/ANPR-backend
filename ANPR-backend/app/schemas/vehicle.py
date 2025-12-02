from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class VehicleBase(BaseModel):
    plate_id: str


class VehicleCreate(VehicleBase):
    plate_id: str
    model: Optional[str] = None
    brand: Optional[str] = None


class VehicleUpdate(BaseModel):
    plate_id: str
    owner_id: Optional[int] = None


class VehicleInDBBase(VehicleBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Vehicle(VehicleInDBBase):
    pass


class VehicleInDB(VehicleInDBBase):
    pass
