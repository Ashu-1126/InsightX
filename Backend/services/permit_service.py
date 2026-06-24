"""
Digital Permit Intelligence Agent — MODULE 5
Manages Permit-to-Work system and detects unsafe permit overlaps.
"""

import json
import sqlite3
import uuid
from datetime import datetime
from typing import Any

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import DB_PATH

PERMIT_TYPES = {
    "hot_work":              "Hot Work Permit",
    "confined_space":        "Confined Space Entry",
    "electrical_isolation":  "Electrical Isolation",
    "maintenance":           "Maintenance Work",
    "height_work":           "Working at Height",
    "chemical":              "Chemical Handling",
}

# Unsafe permit overlap pairs — (type_a, type_b) → risk description
UNSAFE_OVERLAPS: list[dict] = [
    {
        "types": ("hot_work", "confined_space"),
        "severity": "critical",
        "risk": "Hot work near confined space — risk of ignition with asphyxiation gases",
        "action": "Isolate confined space from hot work area or suspend one permit",
    },
    {
        "types": ("hot_work", "chemical"),
        "severity": "critical",
        "risk": "Hot work in chemical zone — risk of chemical fire or explosion",
        "action": "Ensure chemical isolation before hot work; check LEL readings",
    },
    {
        "types": ("electrical_isolation", "maintenance"),
        "severity": "high",
        "risk": "Electrical isolation and maintenance permits co-active — LOTO verification required",
        "action": "Confirm lockout-tagout is verified before maintenance proceeds",
    },
    {
        "types": ("height_work", "maintenance"),
        "severity": "medium",
        "risk": "Height work and maintenance simultaneously — falling object risk",
        "action": "Establish exclusion zone below height work area",
    },
    {
        "types": ("confined_space", "chemical"),
        "severity": "critical",
        "risk": "Confined space entry in chemical zone — high asphyxiation and chemical exposure risk",
        "action": "Mandatory atmospheric testing; assign two standby rescuers",
    },
    {
        "types": ("hot_work", "maintenance"),
        "severity": "high",
        "risk": "Hot work during maintenance — unexpected equipment energization risk",
        "action": "Coordinate work sequence; verify equipment isolation before hot work",
    },
]


def _generate_permit_number() -> str:
    date_str = datetime.utcnow().strftime("%Y%m%d")
    short_id = uuid.uuid4().hex[:6].upper()
    return f"PTW-{date_str}-{short_id}"


def create_permit(
    permit_type: str,
    zone_id: str,
    worker_name: str,
    description: str,
    start_time: str,
    end_time: str,
    issued_by: str = "Safety Officer",
    hazards: list = None,
    precautions: list = None,
) -> dict:
    if permit_type not in PERMIT_TYPES:
        raise ValueError(f"Invalid permit type: {permit_type}")

    permit_number = _generate_permit_number()
    hazards_json = json.dumps(hazards or [])
    precautions_json = json.dumps(precautions or [])

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            """INSERT INTO permits
               (permit_number, permit_type, zone_id, worker_name, issued_by,
                description, hazards, precautions, start_time, end_time, status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (permit_number, permit_type, zone_id, worker_name, issued_by,
             description, hazards_json, precautions_json, start_time, end_time, "active"),
        )
        conn.commit()
        permit_id = c.lastrowid

    return get_permit(permit_id)


def get_permit(permit_id: int) -> dict:
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            """SELECT id, permit_number, permit_type, zone_id, worker_name,
                      issued_by, description, hazards, precautions,
                      start_time, end_time, status, created_at
               FROM permits WHERE id=?""",
            (permit_id,),
        )
        row = c.fetchone()
    if not row:
        return None
    return _row_to_dict(row)


def list_permits(status: str = None, zone_id: str = None) -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        query = """SELECT id, permit_number, permit_type, zone_id, worker_name,
                          issued_by, description, hazards, precautions,
                          start_time, end_time, status, created_at
                   FROM permits"""
        params = []
        filters = []
        if status:
            filters.append("status=?")
            params.append(status)
        if zone_id:
            filters.append("zone_id=?")
            params.append(zone_id)
        if filters:
            query += " WHERE " + " AND ".join(filters)
        query += " ORDER BY created_at DESC"
        c.execute(query, params)
        return [_row_to_dict(r) for r in c.fetchall()]


def update_permit_status(permit_id: int, status: str) -> dict:
    valid = {"active", "completed", "revoked", "pending"}
    if status not in valid:
        raise ValueError(f"Invalid status: {status}")
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE permits SET status=? WHERE id=?", (status, permit_id))
        conn.commit()
    return get_permit(permit_id)


def detect_overlaps(zone_id: str = None) -> list[dict]:
    """Detect active permits that create unsafe conditions when co-active."""
    filters = {"status": "active"}
    if zone_id:
        filters["zone_id"] = zone_id

    active = list_permits(status="active", zone_id=zone_id)
    now = datetime.utcnow().isoformat()
    # Only consider permits currently in their active window
    active = [p for p in active if p["start_time"] <= now <= p["end_time"]]

    found_overlaps = []
    for i, p1 in enumerate(active):
        for p2 in active[i + 1:]:
            if p1["zone_id"] != p2["zone_id"]:
                continue  # Only check same zone for now
            for rule in UNSAFE_OVERLAPS:
                types = rule["types"]
                if set([p1["permit_type"], p2["permit_type"]]) == set(types):
                    found_overlaps.append({
                        "permit_1": p1,
                        "permit_2": p2,
                        "zone_id": p1["zone_id"],
                        "severity": rule["severity"],
                        "risk_description": rule["risk"],
                        "recommended_action": rule["action"],
                        "detected_at": datetime.utcnow().isoformat(),
                    })
    return found_overlaps


def get_active_permits_summary() -> dict:
    active = list_permits(status="active")
    now = datetime.utcnow().isoformat()
    current = [p for p in active if p["start_time"] <= now <= p["end_time"]]
    overlaps = detect_overlaps()
    return {
        "total_active": len(current),
        "permits": current,
        "unsafe_overlaps": overlaps,
        "overlap_count": len(overlaps),
        "has_critical_overlap": any(o["severity"] == "critical" for o in overlaps),
    }


def _row_to_dict(row: tuple) -> dict:
    return {
        "id": row[0],
        "permit_number": row[1],
        "permit_type": row[2],
        "permit_type_label": PERMIT_TYPES.get(row[2], row[2]),
        "zone_id": row[3],
        "worker_name": row[4],
        "issued_by": row[5],
        "description": row[6],
        "hazards": json.loads(row[7] or "[]"),
        "precautions": json.loads(row[8] or "[]"),
        "start_time": row[9],
        "end_time": row[10],
        "status": row[11],
        "created_at": row[12],
    }
