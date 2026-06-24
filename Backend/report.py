from fastapi import APIRouter, Depends, Response
import csv
import io
import sqlite3
from database import get_db

router = APIRouter()


@router.get("/report/fall", response_class=Response)
def generate_fall_report(db: sqlite3.Connection = Depends(get_db)):
    c = db.cursor()
    c.execute(
        (
            "SELECT id, type, description, status, created_at, clip_path, "
            "camera_id, event_id "
            "FROM incidents WHERE type=? ORDER BY created_at DESC"
        ),
        ("fall",),
    )
    rows = c.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "ID",
            "Type",
            "Description",
            "Status",
            "Created At",
            "Clip Path",
            "Camera ID",
            "Event ID",
        ]
    )
    for row in rows:
        writer.writerow(row)
    csv_content = output.getvalue()
    output.close()

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=fall_report.csv"
        },
    )


@router.get("/report/incidents", response_class=Response)
def generate_incidents_report(db: sqlite3.Connection = Depends(get_db)):
    c = db.cursor()
    c.execute(
        (
            "SELECT id, type, description, status, created_at, clip_path, "
            "source, confidence, evidence_image, report_path, camera_id, "
            "event_id "
            "FROM incidents ORDER BY created_at DESC"
        )
    )
    rows = c.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "ID",
            "Type",
            "Description",
            "Status",
            "Created At",
            "Clip Path",
            "Source",
            "Confidence",
            "Evidence Image",
            "Report Path",
            "Camera ID",
            "Event ID",
        ]
    )
    for row in rows:
        writer.writerow(row)
    csv_content = output.getvalue()
    output.close()

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=incidents_report.csv"
        },
    )


@router.get("/report/incident-events", response_class=Response)
def generate_incident_events_report(db: sqlite3.Connection = Depends(get_db)):
    c = db.cursor()
    c.execute(
        (
            "SELECT id, incident_type, camera_id, state, started_at, "
            "last_seen_at, resolved_at, incident_count "
            "FROM incident_events ORDER BY id DESC"
        )
    )
    rows = c.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Event ID",
            "Incident Type",
            "Camera ID",
            "State",
            "Started At",
            "Last Seen At",
            "Resolved At",
            "Incident Count",
        ]
    )
    for row in rows:
        writer.writerow(row)
    csv_content = output.getvalue()
    output.close()

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                "attachment; filename=incident_events_report.csv"
            )
        },
    )
