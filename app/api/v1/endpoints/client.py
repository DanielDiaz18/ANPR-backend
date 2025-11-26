from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import delete, or_, update
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.logger import create_log
from app.models.activity_log import ActionType, EntityType
from app.models.client import Client
from app.models.vehicle import Vehicle
from app.schemas.client import ClientCreate, ClientUpdate
from app.schemas.user import User
from app.core.websocket import manager

router = APIRouter()


@router.get("/")
def get_clients(
    q: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    query = db.query(Client)
    if q:
        query = query.filter(
            or_(
                Client.name.ilike(f"%{q}%"),
                Client.phone.ilike(f"%{q}%"),
                Client.email.ilike(f"%{q}%"),
            )
        )
    clients = query.limit(limit).all()
    return {"clients": clients}


@router.get("/{client_id}")
def get_client(client_id: int, db: Session = Depends(get_db)):
    # Implement get client by ID logic
    return {"client_id": client_id}


@router.post("/")
def create_client(
    body: ClientCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    client = Client(
        name=body.name,
        email=body.email,
        phone=body.phone,
    )
    db.add(client)
    db.commit()
    db.refresh(client)

    # Create log
    create_log(
        db=db,
        action=ActionType.CREATE,
        entity=EntityType.CLIENT,
        entity_id=client.id,
        message=f"Client {client.name} created",
    )

    background_tasks.add_task(
        manager.broadcast_service_update, action="create", service_data=client.to_dict()
    )

    return {"message": "client created", "client": client}


@router.put("/{client_id}")
def update_client(
    client_id: int,
    body: ClientUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    update_stmt = (
        update(Client)
        .where(Client.id == client_id)
        .values(**body.dict(exclude_unset=True))
    )
    db.execute(update_stmt)
    db.commit()
    client = db.query(Client).filter(Client.id == client_id).first()

    # Create log
    create_log(
        db=db,
        action=ActionType.UPDATE,
        entity=EntityType.CLIENT,
        entity_id=client_id,
        message=f"Client {client_id} updated",
    )

    background_tasks.add_task(
        manager.broadcast_client_update, action="update", service_data=client.to_dict()
    )

    return {"message": "client updated", "client": client}


@router.delete("/{client_id}")
def delete_client(
    client_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    db.execute(delete(Client).where(Client.id == client_id))
    db.commit()

    # Create log
    create_log(
        db=db,
        action=ActionType.DELETE,
        entity=EntityType.CLIENT,
        entity_id=client_id,
        message=f"Client {client_id} deleted",
    )

    background_tasks.add_task(
        manager.broadcast_client_update, action="delete", service_data={"id": client_id}
    )
    return {"client_id": client_id, "message": "client deleted"}


@router.post("/{client_id}/vehicles")
def create_client(
    client_id: int,
    plate_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):

    update_stmt = (
        update(Vehicle).where(Client.id == client_id).values(client_id=client_id)
    )
    db.execute(update_stmt)
    db.commit()

    # Create log
    create_log(
        db=db,
        action=ActionType.UPDATE,
        entity=EntityType.CLIENT,
        entity_id=client_id,
        message=f"Vehicle {plate_id} assigned to Client {client_id}",
    )

    client = db.query(Client).filter(Client.id == client_id).first()

    background_tasks.add_task(
        manager.broadcast_client_update, action="update", service_data=client.to_dict()
    )

    return {"message": "client created", "client": client}
