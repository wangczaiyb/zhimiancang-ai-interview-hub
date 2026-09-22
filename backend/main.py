import os
from fastapi import FastAPI, Request, HTTPException, WebSocket
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal, ensure_schema
import app.models # Register all models

from app.api.v1 import (
    auth, public, jobs, resumes, applications,
    personal, interviews, enterprise, admin, files
)
from app.websocket.interview_ws import handle_interview_websocket
from app.websocket.notification_ws import handle_notification_websocket

# Create database tables automatically
Base.metadata.create_all(bind=engine)
# Lightweight incremental migration for columns added after initial release
ensure_schema()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="智面舱 AI Interview Hub 全栈后端 API 系统",
    version="3.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads static directory
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include API v1 Routers
api_v1_prefix = settings.API_V1_STR
app.include_router(auth.router, prefix=api_v1_prefix)
app.include_router(public.router, prefix=api_v1_prefix)
app.include_router(jobs.router, prefix=api_v1_prefix)
app.include_router(resumes.router, prefix=api_v1_prefix)
app.include_router(applications.router, prefix=api_v1_prefix)
app.include_router(personal.router, prefix=api_v1_prefix)
app.include_router(interviews.router, prefix=api_v1_prefix)
app.include_router(enterprise.router, prefix=api_v1_prefix)
app.include_router(admin.router, prefix=api_v1_prefix)
app.include_router(files.router, prefix=api_v1_prefix)

# WebSocket interview room endpoint
@app.websocket("/ws/interviews/{interview_id}")
async def websocket_interview_endpoint(websocket: WebSocket, interview_id: int):
    await handle_interview_websocket(websocket, interview_id)

# WebSocket notification push endpoint
@app.websocket("/ws/notifications/{user_id}")
async def websocket_notification_endpoint(websocket: WebSocket, user_id: int):
    await handle_notification_websocket(websocket, user_id)

# Global Exception Handler to ensure standard response structure {code, message, data}
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail, "data": None}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": f"服务器内部错误: {str(exc)}", "data": None}
    )

@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": "3.0.0",
        "status": "online",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
