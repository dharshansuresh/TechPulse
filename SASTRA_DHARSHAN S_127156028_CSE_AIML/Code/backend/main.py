"""
FastAPI Main Application entry point for Automotive Engineering AI Assistant.
Provides REST API endpoints, Swagger documentation, and health checks.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.logging_config import logger
from database.session import init_db
from backend.routes import documents, chat, search, analysis


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully.")
    yield
    # Shutdown actions
    logger.info("Shutting down application...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description=(
        "AI-powered platform for AUTOSAR High-Level Design (HLD) Document Analysis, "
        "evidence-grounded Question Answering, and architectural consistency verification."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(search.router)
app.include_router(analysis.router)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify backend operational readiness."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "connected",
        "chroma_storage": str(settings.CHROMA_PERSIST_DIR),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.DEBUG)
