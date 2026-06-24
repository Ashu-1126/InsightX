from fastapi import FastAPI, Depends, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import sqlite3
from dotenv import load_dotenv
from database import init_db
from people import router as people_router
from incidents import router as incidents_router
from video import router as video_router
from detection import router as detection_router
from auth import router as auth_router
from realtime import router as realtime_router, manager as ws_manager
from settings import router as settings_router
from cameras import router as cameras_router
from report import router as report_router
from auth import decode_access_token, get_current_user
from database import DB_PATH
from incident_worker import start_incident_worker

# ── SENTINEL AI new modules ───────────────────────────────────────────────────
from routes.sensors import router as sensors_router
from routes.risk import router as risk_router
from routes.permits import router as permits_router
from routes.emergency import router as emergency_router
from routes.rag import router as rag_router
from routes.compliance import router as compliance_router
from routes.agents import router as agents_router
from services.sensor_service import start_sensor_simulation
from services.risk_engine import start_risk_engine, register_broadcast as risk_register_broadcast
from services.orchestrator import register_broadcast as orchestrator_register_broadcast

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# --- APP SETUP ---
app = FastAPI(
    title="SENTINEL AI — Industrial Safety Intelligence OS",
    version="2.0.0",
    description="Next-generation compound risk detection and emergency response platform.",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:8000,http://localhost:3000,http://127.0.0.1:3000,http://localhost:5500",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

CLIPS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../Database/incident_clips"))
REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../Database/incident_reports"))
IMAGES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../Database/incident_images"))


def _validate_user_token(authorization: str | None, token: str | None):
    bearer_token = None
    if authorization and authorization.startswith("Bearer "):
        bearer_token = authorization.split(" ", 1)[1]
    elif token:
        bearer_token = token
    payload = decode_access_token(bearer_token) if bearer_token else None
    if not payload:
        raise HTTPException(status_code=401, detail="Unauthorized")
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE id=?", (payload.get("id"),))
        if not c.fetchone():
            raise HTTPException(status_code=401, detail="User not found")


@app.get("/clips/{clip_name}")
def get_clip(
    clip_name: str,
    authorization: str | None = Header(default=None),
    token: str | None = Query(default=None),
):
    _validate_user_token(authorization, token)
    safe_name = os.path.basename(clip_name)
    if safe_name != clip_name or not safe_name.endswith(".mp4"):
        raise HTTPException(status_code=400, detail="Invalid clip name")
    file_path = os.path.join(CLIPS_DIR, safe_name)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Clip not found")
    return FileResponse(file_path, media_type="video/mp4")


@app.get("/reports/{report_name}")
def get_report(
    report_name: str,
    authorization: str | None = Header(default=None),
    token: str | None = Query(default=None),
):
    _validate_user_token(authorization, token)
    safe_name = os.path.basename(report_name)
    if safe_name != report_name or not safe_name.endswith(".json"):
        raise HTTPException(status_code=400, detail="Invalid report name")
    file_path = os.path.join(REPORTS_DIR, safe_name)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(file_path, media_type="application/json")


@app.get("/incident-images/{image_name}")
def get_incident_image(
    image_name: str,
    authorization: str | None = Header(default=None),
    token: str | None = Query(default=None),
):
    _validate_user_token(authorization, token)
    safe_name = os.path.basename(image_name)
    if safe_name != image_name or not safe_name.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Invalid image name")
    file_path = os.path.join(IMAGES_DIR, safe_name)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path, media_type="image/jpeg")


# --- INIT ---
init_db()
start_incident_worker()
start_sensor_simulation()
start_risk_engine()

# Wire the WebSocket broadcast into risk engine + orchestrator
risk_register_broadcast(ws_manager.broadcast)
orchestrator_register_broadcast(ws_manager.broadcast)

# --- INCLUDE ROUTERS ---
# Existing KavachG routers
app.include_router(auth_router)
app.include_router(realtime_router)
app.include_router(people_router,    dependencies=[Depends(get_current_user)])
app.include_router(incidents_router, dependencies=[Depends(get_current_user)])
app.include_router(video_router)
app.include_router(detection_router, dependencies=[Depends(get_current_user)])
app.include_router(settings_router,  dependencies=[Depends(get_current_user)])
app.include_router(cameras_router,   dependencies=[Depends(get_current_user)])
app.include_router(report_router,    dependencies=[Depends(get_current_user)])

# SENTINEL AI new routers
app.include_router(sensors_router,   dependencies=[Depends(get_current_user)])
app.include_router(risk_router,      dependencies=[Depends(get_current_user)])
app.include_router(permits_router,   dependencies=[Depends(get_current_user)])
app.include_router(emergency_router, dependencies=[Depends(get_current_user)])
app.include_router(rag_router,        dependencies=[Depends(get_current_user)])
app.include_router(compliance_router, dependencies=[Depends(get_current_user)])
app.include_router(agents_router,    dependencies=[Depends(get_current_user)])

# Sensor WebSocket (public — same as /ws/incidents)
from routes.sensors import router as sensor_ws_no_auth
# Already included above; WebSocket is handled inside the router


@app.get("/")
def root():
    return {
        "system": "SENTINEL AI",
        "version": "2.0.0",
        "status": "operational",
        "modules": [
            "sensor_intelligence",
            "compound_risk_engine",
            "permit_intelligence",
            "emergency_orchestrator",
            "rag_intelligence",
            "compliance_audit",
            "cv_detection",
            "incident_management",
            "multi_agent_architecture",
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
