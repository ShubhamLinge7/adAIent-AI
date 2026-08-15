"""
FastAPI application entry point for Industrial Troubleshooting Assistant.
"""
import logging
from contextlib import asynccontextmanager
import sys
from pathlib import Path
import socket

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import manuals, troubleshoot, chat
from app.api import backup
from app.auth import routes as auth_routes
from app.services.indexer import get_indexer
from app.services.llm import get_llm_service
from app.auth.auth_service import AuthService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_local_ip():
    """Get the local IP address for LAN/WiFi access."""
    try:
        # Create a socket connection to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "Unable to determine"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Runs indexing on startup and cleanup on shutdown.
    """
    logger.info("=" * 60)
    logger.info("adAIent - INDUSTRIAL TROUBLESHOOTING ASSISTANT")
    logger.info("=" * 60)
    
    # Display network access information
    local_ip = get_local_ip()
    logger.info("")
    logger.info("🌐 NETWORK ACCESS:")
    logger.info(f"   Local:    http://127.0.0.1:8000")
    logger.info(f"   LAN/WiFi: http://{local_ip}:8000")
    logger.info("")
    logger.info("📱 Access from other devices on your network:")
    logger.info(f"   Open browser → http://{local_ip}:8000")
    logger.info("=" * 60)
    logger.info("")
    
    # Index all manuals on startup
    logger.info("Indexing manuals on startup...")
    try:
        indexer = get_indexer()
        results = indexer.index_all_manuals(force_reindex=False)
        
        indexed_count = sum(1 for r in results if r.get("success"))
        skipped_count = sum(1 for r in results if r.get("skipped"))
        failed_count = sum(1 for r in results if not r.get("success") and not r.get("skipped"))
        
        logger.info(f"Indexing complete: {indexed_count} indexed, {skipped_count} skipped, {failed_count} failed")
    except Exception as e:
        logger.error(f"Indexing failed during startup: {e}")
    
    # Initialize LLM service
    logger.info("Initializing LLM service...")
    llm_service = get_llm_service()
    logger.info("LLM service initialized and ready")
    
    # Cleanup old audit logs (retain 7 days)
    logger.info("Cleaning up old audit logs...")
    try:
        from app.auth.auth_service import AuthService
        auth_service = AuthService()
        deleted_count = auth_service.cleanup_old_audit_logs(retention_days=7)
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} audit logs older than 7 days")
        else:
            logger.info("No old audit logs to delete")
    except Exception as e:
        logger.error(f"Failed to cleanup old audit logs: {e}")
    
    logger.info("Application startup complete")
    logger.info("=" * 60)
    
    yield  # Application runs here
    
    # Cleanup on shutdown
    logger.info("Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title="Industrial Troubleshooting Assistant",
    description="Multi-manual troubleshooting assistant for industrial maintenance (offline)",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local use
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router, tags=["Authentication"])
app.include_router(manuals.router, tags=["Manuals"])
app.include_router(troubleshoot.router, tags=["Troubleshooting"])
app.include_router(chat.router, tags=["Chat"])
app.include_router(backup.router, tags=["Backup"])


@app.get("/")
async def root():
    """Serve the main web interface - adAIent."""
    index_path = Path(__file__).parent.parent / "index_adaient.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {
        "service": "adAIent - Industrial AI Assistant",
        "version": "2.0.0",
        "status": "online",
        "endpoints": {
            "manuals": "/manuals",
            "troubleshoot": "/ask",
            "docs": "/docs"
        }
    }


@app.get("/login.html")
async def login_page():
    """Serve the login page."""
    login_path = Path(__file__).parent.parent / "login.html"
    if login_path.exists():
        return FileResponse(login_path)
    return {"error": "Login page not found"}


@app.get("/admin.html")
async def admin_page():
    """Serve the admin dashboard."""
    admin_path = Path(__file__).parent.parent / "admin.html"
    if admin_path.exists():
        return FileResponse(admin_path)
    return {"error": "Admin page not found"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    status = "healthy"
    details = {
        "app": "ok",
        "db": "unknown",
        "ollama": "unknown"
    }

    # Database check
    try:
        auth_service = AuthService()
        cursor = auth_service.conn.cursor()
        cursor.execute("SELECT 1")
        _ = cursor.fetchone()
        details["db"] = "ok"
    except Exception as e:
        details["db"] = "error"
        details["db_error"] = str(e)
        status = "degraded"

    # LLM (Ollama) check
    try:
        llm_service = get_llm_service()
        ollama_healthy = await llm_service.health_check()
        details["ollama"] = "ok" if ollama_healthy else "unavailable"
        if not ollama_healthy:
            status = "degraded"
    except Exception as e:
        details["ollama"] = "error"
        details["ollama_error"] = str(e)
        status = "degraded"
    
    return {
        "status": status,
        "details": details
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
