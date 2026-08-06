"""FastAPI + WebSocket entrypoint for local-bridge."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import config
from app.api.endpoints import router
from app.utils.logger import log_warning

app = FastAPI(
    title="Realtime Translate JP To VN - Local Bridge",
    description="Bridge server for Japanese to Vietnamese real-time speech recognition & translation",
    version="1.0.0"
)

# Enable CORS for local web interface & extensions
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Mount static web UI if web/ directory exists
WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "web")
if os.path.exists(WEB_DIR):
    app.mount("/web", StaticFiles(directory=WEB_DIR, html=True), name="web")

@app.get("/")
async def root():
    """Root route returning web app interface if available or API status."""
    index_html = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(index_html):
        return FileResponse(index_html)
    return {
        "app": "Realtime Translate JP To VN Local Bridge",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "ws_endpoint": "ws://localhost:8765/ws/translate"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=config.host, port=config.port, reload=False)
