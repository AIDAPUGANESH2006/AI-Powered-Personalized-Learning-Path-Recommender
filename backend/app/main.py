from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.assessment import router as assessment_router
from app.api.auth import router as auth_router
from app.api.catalog import router as catalog_router
from app.api.chat import router as chat_router
from app.api.feedback import router as feedback_router
from app.api.health import router as health_router
from app.api.profile import router as profile_router
from app.api.recommendations import router as rec_router
from app.api.roadmap import router as roadmap_router
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-Powered Personalized Learning Path Recommender",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router,     prefix="/api")
app.include_router(auth_router,       prefix="/api")
app.include_router(profile_router,    prefix="/api")
app.include_router(catalog_router,    prefix="/api")
app.include_router(rec_router,        prefix="/api")
app.include_router(roadmap_router,    prefix="/api")
app.include_router(assessment_router, prefix="/api")
app.include_router(feedback_router,   prefix="/api")
app.include_router(chat_router,       prefix="/api")


@app.get("/")
def root() -> dict:
    return {
        "message": "PathWise AI API",
        "docs": "/docs",
        "health": "/api/health",
    }
