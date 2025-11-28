from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.core.database import init_db
import threading
from app.deteccion import router as detection_router
from app.deteccion.engine import start_background_tasks

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="FastAPI Backend Server",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)


# Initialize database tables
@app.on_event("startup")
def on_startup():
    init_db()
    print("--- Iniciando la deteccion de placas con OCR ---")
    threading.Thread(target=start_background_tasks, daemon=True).start()


# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

# Router para la deteccion de las placas en tiempo real
app.include_router(detection_router.router, prefix="/detection", tags=["detection"])

@app.get("/")
def read_root():
    return {"message": "Welcome to ATP Server"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
