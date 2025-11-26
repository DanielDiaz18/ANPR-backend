from fastapi import APIRouter
from app.api.v1.endpoints import auth, service, users, vehicle, client, websocket

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(service.router, prefix="/service", tags=["service"])
api_router.include_router(vehicle.router, prefix="/vehicle", tags=["vehicle"])
api_router.include_router(client.router, prefix="/client", tags=["client"])
api_router.include_router(websocket.router, tags=["websocket"])
