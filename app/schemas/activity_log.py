from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from app.models.activity_log import ActionType, EntityType


class ActivityLogBase(BaseModel):
    description: str = None
    meta: Optional[dict] = None

    action_type: ActionType = None
    entity_type: EntityType = None
    entity_id: Optional[int] = None


class ActivityLogCreate(ActivityLogBase):
    pass

class ActivityLogUpdate(BaseModel):
    pass


class ActivityLogInDBBase(ActivityLogBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ActivityLog(ActivityLogInDBBase):
    pass


class ActivityLogInDB(ActivityLogInDBBase):
    pass
