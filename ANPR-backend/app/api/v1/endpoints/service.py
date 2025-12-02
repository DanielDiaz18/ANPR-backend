from fastapi import APIRouter, Depends
from sqlalchemy import delete, insert, update
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.models.service import Service
from app.models.vehicle import Vehicle
from app.schemas.service import ServiceCreate, ServiceUpdate

router = APIRouter()


@router.get("/")
def get_services(db: Session = Depends(get_db)):
    services = db.query(Service).options(joinedload(Service.vehicle)).all()
    return {"services": services}


@router.post("/")
def create_service(body: ServiceCreate, db: Session = Depends(get_db)):
    plate_id = body.plate_id.upper().replace(" ", "").replace("-", "")
    vehicle = db.query(Vehicle).filter(Vehicle.plate_id == plate_id).first()
    vehicle_id = None
    if vehicle:
        vehicle_id = vehicle.id
    else:
        new_vehicle = Vehicle(plate_id=plate_id)
        db.add(new_vehicle)
        db.commit()
        db.refresh(new_vehicle)
        vehicle_id = new_vehicle.id

    insert_stmt = insert(Service).values(
        **body.dict(exclude={"plate_id"}), vehicle_id=vehicle_id
    )
    result = db.execute(insert_stmt)
    db.commit()
    service_id = result.inserted_primary_key[0]
    service = (
        db.query(Service)
        .filter(Service.id == service_id)
        .options(joinedload(Service.vehicle))
        .first()
    )

    return {"message": "service created", "service": service}


@router.get("/{service_id}")
def get_service(service_id: int, db: Session = Depends(get_db)):
    service = db.query(Service).filter(Service.id == service_id).first()
    return {"service": service}


@router.put("/{service_id}")
def update_service(service_id: int, body: ServiceUpdate, db: Session = Depends(get_db)):
    u = (
        update(Service)
        .where(Service.id == service_id)
        .values(**body.dict(exclude_unset=True))
    )
    db.execute(u)
    db.commit()
    service = (
        db.query(Service)
        .filter(Service.id == service_id)
        .options(joinedload(Service.vehicle))
        .first()
    )
    return {"service_id": service_id, "message": "service updated", "service": service}


@router.delete("/{service_id}")
def delete_service(service_id: int, db: Session = Depends(get_db)):
    service = db.query(Service).filter(Service.id == service_id).first()
    db.execute(delete(Service).where(Service.id == service_id))
    db.commit()
    return {"service_id": service_id, "message": "service deleted", "service": service}
