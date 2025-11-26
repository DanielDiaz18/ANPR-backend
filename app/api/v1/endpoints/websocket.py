from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from app.core.websocket import manager
from app.core.database import get_db
from app.models.client import Client
from app.models.service import Service
from app.models.vehicle import Vehicle
from sqlalchemy.orm import joinedload
import json

router = APIRouter()


@router.websocket("/ws/services")
async def websocket_services(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    WebSocket endpoint for real-time service updates.
    Clients will receive notifications when services are created, updated, or deleted.
    """
    await manager.connect(websocket, topic="services")

    try:
        # Send initial data
        services = db.query(Service).all()
        initial_data = {
            "type": "initial_data",
            "action": "list",
            "data": [service.to_dict() for service in services],
        }
        await manager.send_personal_message(json.dumps(initial_data), websocket)

        # Keep connection alive and listen for messages
        while True:
            data = await websocket.receive_text()
            # Echo back or handle client messages if needed
            await manager.send_personal_message(f"Message received: {data}", websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket, topic="services")
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, topic="services")


@router.websocket("/ws/vehicles")
async def websocket_vehicles(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    WebSocket endpoint for real-time vehicle updates.
    Clients will receive notifications when vehicles are created, updated, or deleted.
    """
    await manager.connect(websocket, topic="vehicles")

    try:
        # Send initial data
        vehicles = db.query(Vehicle).all()
        initial_data = {
            "type": "initial_data",
            "action": "list",
            "data": [vehicle.to_dict() for vehicle in vehicles],
        }
        await manager.send_personal_message(json.dumps(initial_data), websocket)

        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Message received: {data}", websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket, topic="vehicles")
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, topic="vehicles")


@router.websocket("/ws/clients")
async def websocket_clients(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    WebSocket endpoint for real-time client updates.
    Clients will receive notifications when clients are created, updated, or deleted.
    """
    await manager.connect(websocket, topic="clients")

    try:
        # Send initial data
        clients = db.query(Client).all()
        initial_data = {
            "type": "initial_data",
            "action": "list",
            "data": [client.to_dict() for client in clients],
        }
        await manager.send_personal_message(json.dumps(initial_data), websocket)

        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Message received: {data}", websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket, topic="clients")
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, topic="clients")


@router.websocket("/ws/all")
async def websocket_all(websocket: WebSocket):
    """
    WebSocket endpoint for all real-time updates.
    Clients will receive notifications for all events (services, vehicles, etc.).
    """
    await manager.connect(websocket, topic="all")

    try:
        # Send connection confirmation
        await manager.send_personal_message(
            json.dumps({"type": "connection", "message": "Connected to all updates"}),
            websocket,
        )

        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Message received: {data}", websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket, topic="all")
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, topic="all")


@router.get("/ws/stats")
async def websocket_stats():
    """Get WebSocket connection statistics"""
    return {
        "active_connections": {
            "services": manager.get_active_connections_count("services"),
            "vehicles": manager.get_active_connections_count("vehicles"),
            "all": manager.get_active_connections_count("all"),
        }
    }
