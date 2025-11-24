"""
Codex IDE - Backend Server
FastAPI application for fiction writing IDE
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="Codex IDE API",
    description="Backend API for the Codex fiction writing IDE",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
            "manuscripts": False,
            "versioning": False,
            "codex": False,
            "ai_generation": False,
            "analysis": False
        },
        "services": {
            "database": False,
            "nlp": False,
            "vector_store": False,
            "graph_db": False
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
