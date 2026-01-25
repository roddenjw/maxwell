"""
Codex IDE - Backend Server
FastAPI application for fiction writing IDE
"""

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn

from app.database import init_db
from app.services import (
    codex_service,
    embedding_service,
    graph_service,
    version_service,
    EMBEDDING_AVAILABLE,
    GRAPH_AVAILABLE
)
from app.services.nlp_service import nlp_service
from app.api.routes import versioning, manuscripts, codex, timeline, chapters, stats, realtime, fast_coach, recap, export, onboarding, outlines, brainstorming, worlds, entity_states, foreshadowing, import_routes, share


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Initializing Codex IDE backend...")

    # Initialize database
    print("📊 Setting up database...")
    init_db()

    # Initialize services
    if nlp_service.is_available():
        print("🧠 NLP service available (spaCy en_core_web_lg)")
    else:
        print("⚠️  NLP service not available (install spaCy and download en_core_web_lg)")

    if EMBEDDING_AVAILABLE:
        print("🔌 ChromaDB available")
    else:
        print("⚠️  ChromaDB not available (requires Python < 3.13)")

    if GRAPH_AVAILABLE:
        print("🕸️  KuzuDB available")
    else:
        print("⚠️  KuzuDB not available (requires Python < 3.13)")

    print("✅ Backend ready!")

    yield

    # Shutdown
    print("👋 Shutting down Codex IDE backend...")


# Create FastAPI app
app = FastAPI(
    title="Codex IDE API",
    description="Backend API for the Codex fiction writing IDE",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(versioning.router)
app.include_router(manuscripts.router)
app.include_router(codex.router)
app.include_router(timeline.router)
app.include_router(chapters.router)
app.include_router(stats.router)
app.include_router(realtime.router)
app.include_router(fast_coach.router)
app.include_router(recap.router)
app.include_router(export.router)
app.include_router(onboarding.router)
app.include_router(outlines.router)
app.include_router(brainstorming.router)
app.include_router(worlds.router)
app.include_router(entity_states.router)
app.include_router(foreshadowing.router)
app.include_router(import_routes.router)
app.include_router(share.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Codex IDE API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "codex-ide-backend"
    }


@app.get("/api/status")
async def api_status():
    """API status endpoint"""
    return {
        "api_version": "0.1.0",
        "features": {
            "manuscripts": True,  # Database models ready
            "versioning": True,  # ✅ Git service ready
            "codex": True,  # ✅ Entity CRUD ready
            "timeline": True,  # ✅ Timeline orchestrator ready
            "ai_generation": False,  # LangChain pending
            "analysis": nlp_service.is_available()  # ✅ spaCy NLP
        },
        "services": {
            "database": True,  # SQLite + Alembic initialized
            "nlp": nlp_service.is_available(),  # ✅ spaCy (if model downloaded)
            "vector_store": EMBEDDING_AVAILABLE,  # ChromaDB (needs Python < 3.13)
            "graph_db": GRAPH_AVAILABLE,  # KuzuDB (needs Python < 3.13)
            "git": True  # ✅ pygit2 ready
        }
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": "The requested resource was not found"
            }
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal server error occurred"
            }
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
