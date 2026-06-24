import sqlite3
from datetime import datetime

from database import DB_PATH
from incident_report import generate_incident_report


EVENT_IDLE_SECONDS = 45


def _resolve_stale_events(cursor, now_iso: str) -> None:
    cursor.execute(
        (
            "UPDATE incident_events "
            "SET state='resolved', resolved_at=? "
            "WHERE state IN ('start','active') "
            "AND ((julianday(?) - julianday(last_seen_at)) * 86400.0) > ?"
        ),
        (now_iso, now_iso, EVENT_IDLE_SECONDS),
    )


def _get_or_create_event(
    cursor,
    incident_type: str,
    camera_id: int | None,
    now_iso: str,
) -> int:
    cursor.execute(
        (
            "SELECT id, state, incident_count FROM incident_events "
            "WHERE incident_type=? "
            "AND ((camera_id IS NULL AND ? IS NULL) OR camera_id=?) "
            "AND state IN ('start','active') "
            "ORDER BY id DESC LIMIT 1"
        ),
        (incident_type, camera_id, camera_id),
    )
    row = cursor.fetchone()
    if row:
        event_id, state, incident_count = row
        next_state = "active" if state == "start" else state
        cursor.execute(
            (
                "UPDATE incident_events "
                "SET state=?, last_seen_at=?, incident_count=? "
                "WHERE id=?"
            ),
            (next_state, now_iso, int(incident_count or 0) + 1, event_id),
        )
        return int(event_id)

    cursor.execute(
        (
            "INSERT INTO incident_events "
            "(incident_type, camera_id, state, started_at, last_seen_at, "
            "incident_count) VALUES (?, ?, 'start', ?, ?, 1)"
        ),
        (incident_type, camera_id, now_iso, now_iso),
    )
    return int(cursor.lastrowid)


def create_incident(
    incident_type: str,
    description: str,
    clip_path: str | None = None,
    source: str = "manual",
    confidence: float | None = None,
    evidence_image: str | None = None,
    camera_id: int | None = None,
) -> dict:
    with sqlite3.connect(DB_PATH) as db:
        c = db.cursor()
        now_iso = datetime.utcnow().isoformat()

        event_id = None
        if source == "auto-monitoring":
            _resolve_stale_events(c, now_iso)
            event_id = _get_or_create_event(
                c,
                incident_type,
                camera_id,
                now_iso,
            )

        c.execute(
            (
                "INSERT INTO incidents "
                "(type, description, clip_path, source, confidence, "
                "evidence_image, camera_id, event_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            ),
            (
                incident_type,
                description,
                clip_path,
                source,
                confidence,
                evidence_image,
                camera_id,
                event_id,
            ),
        )
        incident_id = c.lastrowid

        c.execute(
            (
                "INSERT INTO incident_audit "
                "(incident_id, status, changed_at) VALUES (?, ?, ?)"
            ),
            (incident_id, "Open", datetime.utcnow().isoformat()),
        )

        c.execute(
            (
                "SELECT id, type, description, status, created_at, clip_path, "
                "source, confidence, evidence_image, report_path, "
                "camera_id, event_id "
                "FROM incidents WHERE id=?"
            ),
            (incident_id,),
        )
        row = c.fetchone()

        incident = {
            "id": row[0],
            "type": row[1],
            "description": row[2],
            "status": row[3],
            "created_at": row[4],
            "clip_path": row[5],
            "source": row[6],
            "confidence": row[7],
            "evidence_image": row[8],
            "report_path": row[9],
            "camera_id": row[10],
            "event_id": row[11],
        }

        report_name = generate_incident_report(incident)
        c.execute(
            "UPDATE incidents SET report_path=? WHERE id=?",
            (report_name, incident_id),
        )
        db.commit()

        incident["report_path"] = report_name
        return incident
