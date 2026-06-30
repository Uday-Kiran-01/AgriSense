"""
AgriSense AI — FastAPI Backend
Main application entry point.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db, SessionLocal
from .routers.agrisense import router
from .services.seed import seed_demo_data
from .logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: initialize DB and seed demo data
    logger.info("Starting AgriSense AI Backend...")
    init_db()
    logger.info("Database initialized")

    # Seed demo data if no farmers exist
    db = SessionLocal()
    try:
        from .models import Farmer
        if db.query(Farmer).count() == 0:
            seed_demo_data(db)
    finally:
        db.close()

    yield

    # Shutdown
    logger.info("Shutting down AgriSense AI Backend")


app = FastAPI(
    title="AgriSense AI",
    description=(
        "Explainable AI Decision Support Platform for Agricultural Finance. "
        "Helps farmers and financial institutions make transparent financing "
        "decisions by transforming fragmented data into AI-powered insights."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(router)


@app.get("/")
def root():
    return {
        "name": "AgriSense AI",
        "version": "1.0.0",
        "description": "Explainable AI Decision Support for Agricultural Finance",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
