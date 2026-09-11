from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.health import router as health_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Voice-first government welfare scheme discovery for Indian citizens",
    version="0.1.0",
)

# Enable CORS for local development and mobile client communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to YojanaVaani Backend API",
        "docs": "/docs",
        "health": "/health",
    }
