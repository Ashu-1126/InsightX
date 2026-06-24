from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime
import sqlite3
from database import get_db
from realtime import broadcast_incident
import asyncio
from incident_service import create_incident

router = APIRouter()


class IncidentCreate(BaseModel):
    type: str
    description: str
    clip_path: str | None = None
    source: str = "manual"
    confidence: float | None = None
    evidence_image: str | None = None
    camera_id: int | None = None


class IncidentOut(BaseModel):
    id: int
    type: str
    description: str
    status: str
    created_at: str | None
    clip_path: str | None = None
    source: str | None = None
    confidence: float | None = None
    evidence_image: str | None = None
    report_path: str | None = None
    camera_id: int | None = None
    event_id: int | None = None


@router.post("/incidents/", response_model=IncidentOut)
def add_incident(
    incident: IncidentCreate, db: sqlite3.Connection = Depends(get_db)
):
    incident_obj = IncidentOut(
        **create_incident(
            incident_type=incident.type,
            description=incident.description,
            clip_path=incident.clip_path,
            source=incident.source,
            confidence=incident.confidence,
            evidence_image=incident.evidence_image,
            camera_id=incident.camera_id,
        )
    )
    # Broadcast to WebSocket clients
    asyncio.create_task(broadcast_incident(incident_obj.dict()))
    return incident_obj


@router.get("/incidents/", response_model=List[IncidentOut])
def get_incidents(
    status: str = None,
    type: str = None,
    db: sqlite3.Connection = Depends(get_db),
):
    valid_statuses = {"Open", "In Progress", "Closed"}
    valid_types = {"ppe", "fire-smoke", "fall", "pose", "manual"}
    if status and status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status filter")
    if type and type not in valid_types:
        raise HTTPException(status_code=400, detail="Invalid type filter")
    c = db.cursor()
    query = (
        "SELECT id, type, description, status, created_at, clip_path, "
        "source, confidence, evidence_image, report_path, camera_id, "
        "event_id "
        "FROM incidents"
    )
    params = []
    filters = []
    if status:
        filters.append("status = ?")
        params.append(status)
    if type:
        filters.append("type = ?")
        params.append(type)
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY created_at DESC"
    c.execute(query, params)
    return [
        IncidentOut(
            id=row[0],
            type=row[1],
            description=row[2],
            status=row[3],
            created_at=row[4],
            clip_path=row[5],
            source=row[6],
            confidence=row[7],
            evidence_image=row[8],
            report_path=row[9],
            camera_id=row[10],
            event_id=row[11],
        )
        for row in c.fetchall()
    ]


@router.get("/incidents/events")
def get_incident_events(db: sqlite3.Connection = Depends(get_db)):
    c = db.cursor()
    c.execute(
        (
            "SELECT id, incident_type, camera_id, state, started_at, "
            "last_seen_at, resolved_at, incident_count "
            "FROM incident_events ORDER BY id DESC"
        )
    )
    rows = c.fetchall()
    return [
        {
            "id": row[0],
            "incident_type": row[1],
            "camera_id": row[2],
            "state": row[3],
            "started_at": row[4],
            "last_seen_at": row[5],
            "resolved_at": row[6],
            "incident_count": row[7],
        }
        for row in rows
    ]


@router.patch("/incidents/{incident_id}/status")
def update_incident_status(
    incident_id: int, status: str, db: sqlite3.Connection = Depends(get_db)
):
    valid_statuses = {"Open", "In Progress", "Closed"}
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status value")
    c = db.cursor()
    c.execute("SELECT id FROM incidents WHERE id=?", (incident_id,))
    if not c.fetchone():
        raise HTTPException(status_code=404, detail="Incident not found.")
    c.execute(
        "UPDATE incidents SET status=? WHERE id=?", (status, incident_id)
    )
    c.execute(
        (
            "INSERT INTO incident_audit (incident_id, status, changed_at) "
            "VALUES (?, ?, ?)"
        ),
        (incident_id, status, datetime.utcnow().isoformat()),
    )
    db.commit()
    return {"message": "Status updated."}


@router.get("/incidents/audit/{incident_id}")
def get_incident_audit(
    incident_id: int, db: sqlite3.Connection = Depends(get_db)
):
    c = db.cursor()
    c.execute(
        (
            "SELECT status, changed_at FROM incident_audit "
            "WHERE incident_id=? ORDER BY changed_at DESC"
        ),
        (incident_id,),
    )
    return [{"status": row[0], "changed_at": row[1]} for row in c.fetchall()]


@router.post("/incidents/{incident_id}/feedback")
def submit_feedback(
    incident_id: int,
    comment: str = Body(...),
    db: sqlite3.Connection = Depends(get_db),
):
    if not comment or not comment.strip():
        raise HTTPException(status_code=400, detail="Comment is required")
    c = db.cursor()
    c.execute(
        "INSERT INTO feedback (incident_id, comment) VALUES (?, ?)",
        (incident_id, comment.strip()),
    )
    db.commit()
    return {"message": "Feedback submitted."}
