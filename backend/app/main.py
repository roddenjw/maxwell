"""
Codex IDE - Backend Server
FastAPI application for fiction writing IDE
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn

from app.database import init_db
from app.services import embedding_service, graph_service, version_service
from app.api.routes import versioning


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Initializing Codex IDE backend...")

    # Initialize database
    print("📊 Setting up database...")
    init_db()

    # Initialize services
    print("🔌 Initializing ChromaDB...")
    # ChromaDB initializes on first use

    print("🕸️  Initializing KuzuDB...")
    # KuzuDB initializes on first use

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
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(versioning.router)


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
            "codex": True,  # Entity models ready
            "ai_generation": False,  # LangChain pending
            "analysis": False  # NLP services pending
        },
        "services": {
            "database": True,  # SQLite + Alembic initialized
            "nlp": False,  # spaCy pending
            "vector_store": True,  # ChromaDB initialized
            "graph_db": True,  # KuzuDB initialized
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
