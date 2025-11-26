from sqlalchemy.orm import Session
from datetime import datetime
from app.models.activity_log import ActivityLog, ActionType, EntityType


def create_log(
    db: Session,
    action: ActionType,
    entity: EntityType,
    entity_id: int,
    message: str,
    user_id: int = None,
    metadata: dict = None,
):
    """Create a log entry for an action"""
    log = ActivityLog(
        user_id=user_id,
        action_type=action,
        entity_type=entity,
        entity_id=entity_id,
        description=message,
        metadata=metadata,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
