from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class ClientBase(BaseModel):
    name: str


class ClientCreate(ClientBase):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    enabled: Optional[bool] = True


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    enabled: Optional[bool] = None


class ClientInDBBase(ClientBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Client(ClientInDBBase):
    pass


class ClientInDB(ClientInDBBase):
    pass
