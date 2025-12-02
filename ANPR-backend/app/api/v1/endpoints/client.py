from fastapi import APIRouter, Depends
from sqlalchemy import delete, or_, update
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientUpdate
from app.schemas.user import User

router = APIRouter()


@router.get("/")
def get_clients(
    q: str | None = None,
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
def create_client(body: ClientCreate, db: Session = Depends(get_db)):
    client = Client(
        name=body.name,
        email=body.email,
        phone=body.phone,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return {"message": "client created", "client": client}


@router.put("/{client_id}")
def update_client(client_id: int, body: ClientUpdate, db: Session = Depends(get_db)):
    update_stmt = (
        update(Client)
        .where(Client.id == client_id)
        .values(**body.dict(exclude_unset=True))
    )
    db.execute(update_stmt)
    db.commit()
    client = db.query(Client).filter(Client.id == client_id).first()
    return {"message": "client updated", "client": client}


@router.delete("/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    db.execute(delete(Client).where(Client.id == client_id))
    db.commit()
    return {"client_id": client_id, "message": "client deleted"}
