from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy import delete, insert, update
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.core.websocket import manager
from app.models.service import Service
from app.models.vehicle import Vehicle
from app.schemas.service import ServiceCreate, ServiceUpdate

router = APIRouter()


@router.get("/")
def get_services(db: Session = Depends(get_db)):
    services = db.query(Service).all()
    return {"services": services}


@router.post("/")
async def create_service(
    body: ServiceCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
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
    service = db.query(Service).filter(Service.id == service_id).first()

    # Broadcast WebSocket update
    background_tasks.add_task(
        manager.broadcast_service_update,
        action="create",
        service_data=service.to_dict(),
    )

    return {"message": "service created", "service": service}


@router.get("/{service_id}")
def get_service(service_id: int, db: Session = Depends(get_db)):
    service = db.query(Service).filter(Service.id == service_id).first()
    return {"service": service}


@router.put("/{service_id}")
async def update_service(
    service_id: int,
    body: ServiceUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    u = (
        update(Service)
        .where(Service.id == service_id)
        .values(**body.dict(exclude_unset=True))
    )
    db.execute(u)
    db.commit()
    service = db.query(Service).filter(Service.id == service_id).first()

    # Broadcast WebSocket update
    background_tasks.add_task(
        manager.broadcast_service_update,
        action="update",
        service_data=service.to_dict(),
    )

    return {"service_id": service_id, "message": "service updated", "service": service}


@router.delete("/{service_id}")
async def delete_service(
    service_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    service = db.query(Service).filter(Service.id == service_id).first()

    if not service:
        return {"service_id": service_id, "message": "service not found"}
    service_data = service.to_dict()

    db.execute(delete(Service).where(Service.id == service_id))
    db.commit()

    # Broadcast WebSocket update
    background_tasks.add_task(
        manager.broadcast_service_update,
        action="delete",
        service_data=service_data,
    )

    return {"service_id": service_id, "message": "service deleted", "service": service}
