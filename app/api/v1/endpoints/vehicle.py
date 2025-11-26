from typing import Optional, Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import delete, insert, or_, update
from sqlalchemy.orm import Session
from app.api.v1.endpoints.auth import get_current_active_user
from app.core.database import get_db
from app.core.logger import create_log
from app.models.activity_log import ActionType, ActivityLog, EntityType
from app.models.service import Service
from app.models.vehicle import Vehicle
from app.schemas.service import ServiceCreate, ServiceUpdate
from app.schemas.vehicle import VehicleCreate

router = APIRouter()


@router.get("/")
def get_vehicles(
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    # user=Depends(get_current_active_user),
):
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


@router.get("/{vehicle_id}")
def get_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    # user=Depends(get_current_active_user),
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"vehicle": vehicle}


@router.post("/")
def create_vehicle(
    body: VehicleCreate,
    db: Session = Depends(get_db),
    # user=Depends(get_current_active_user),
):
    new_vehicle = Vehicle(**body.dict())
    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)

    # Create log
    create_log(
        db=db,
        action=ActionType.CREATE,
        entity=EntityType.VEHICLE,
        entity_id=new_vehicle.id,
        message=f"Vehicle {new_vehicle.plate_id} created",
    )

    return {"message": "vehicle created", "vehicle": new_vehicle}


@router.put("/{vehicle_id}")
def update_vehicle(
    vehicle_id: int,
    body: VehicleCreate,
    db: Session = Depends(get_db),
    # user=Depends(get_current_active_user),
):
    update_stmt = (
        update(Vehicle)
        .where(Vehicle.id == vehicle_id)
        .values(**body.dict(exclude_unset=True))
    )
    db.execute(update_stmt)
    db.commit()
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

    # Create log
    create_log(
        db=db,
        action=ActionType.UPDATE,
        entity=EntityType.VEHICLE,
        entity_id=vehicle_id,
        message=f"Vehicle {vehicle_id} updated",
    )

    return {"message": "vehicle updated", "vehicle": vehicle}


@router.delete("/{vehicle_id}")
def delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    # user=Depends(get_current_active_user),
):
    delete_stmt = delete(Vehicle).where(Vehicle.id == vehicle_id)
    db.execute(delete_stmt)
    db.commit()

    # Create log
    create_log(
        db=db,
        action=ActionType.DELETE,
        entity=EntityType.VEHICLE,
        entity_id=vehicle_id,
        message=f"Vehicle {vehicle_id} deleted",
    )

    return {"vehicle_id": vehicle_id, "message": "Vehicle deleted"}
