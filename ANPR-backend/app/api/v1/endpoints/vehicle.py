from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy import delete, insert, or_, update
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.service import Service
from app.models.vehicle import Vehicle
from app.schemas.service import ServiceCreate, ServiceUpdate
from app.schemas.vehicle import VehicleCreate

router = APIRouter()


@router.get("/")
def get_vehicles(q: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Vehicle)
    if q:
        query = query.filter(
            or_(
                Vehicle.plate_id.ilike(f"%{q}%"),
                Vehicle.model.ilike(f"%{q}%"),
                Vehicle.brand.ilike(f"%{q}%"),
            )
        )
    vehicles = query.all()
    return {"vehicles": vehicles}


@router.post("/")
def create_vehicle(body: VehicleCreate, db: Session = Depends(get_db)):
    new_vehicle = Vehicle(**body.dict())
    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)
    return {"message": "vehicle created", "vehicle": new_vehicle}


@router.put("/{vehicle_id}")
def update_vehicle(vehicle_id: int, body: VehicleCreate, db: Session = Depends(get_db)):
    update_stmt = (
        update(Vehicle)
        .where(Vehicle.id == vehicle_id)
        .values(**body.dict(exclude_unset=True))
    )
    db.execute(update_stmt)
    db.commit()
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    return {"message": "vehicle updated", "vehicle": vehicle}


@router.delete("/{vehicle_id}")
def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    delete_stmt = delete(Vehicle).where(Vehicle.id == vehicle_id)
    db.execute(delete_stmt)
    db.commit()
    return {"vehicle_id": vehicle_id, "message": "Vehicle deleted"}
