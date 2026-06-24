"""
Emergency Response Orchestrator — MODULE 6
Triggered when a critical compound risk is detected.
Generates evacuation plans, notifies responders, preserves evidence,
and creates emergency event records.
"""

import asyncio
import json
import sqlite3
from datetime import datetime
from typing import Any

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import DB_PATH

ZONE_NAMES = {
    "zone_a": "Production Floor",
    "zone_b": "Storage Area",
    "zone_c": "Chemical Processing",
    "zone_d": "Loading Bay",
    "zone_e": "Control Room",
    "zone_f": "Confined Space",
}

# Zone adjacency — which zones must also be evacuated when a zone goes critical
ADJACENT_ZONES: dict[str, list[str]] = {
    "zone_a": ["zone_b", "zone_d"],
    "zone_b": ["zone_a", "zone_c"],
    "zone_c": ["zone_b", "zone_f"],
    "zone_d": ["zone_a", "zone_e"],
    "zone_e": ["zone_d"],
    "zone_f": ["zone_c"],
}

# Risk category → responders to notify
RESPONDERS: dict[str, list[str]] = {
    "Explosion":         ["Fire Brigade (ext. 100)", "Safety Officer (ext. 201)", "Plant Manager (ext. 300)", "Medical Team (ext. 102)"],
    "Asphyxiation":      ["Medical Team (ext. 102)", "Rescue Team (ext. 205)", "Safety Officer (ext. 201)"],
    "Equipment Failure": ["Maintenance Lead (ext. 210)", "Safety Officer (ext. 201)", "Engineering Team (ext. 215)"],
    "Chemical Hazard":   ["Chemical Safety Team (ext. 220)", "Fire Brigade (ext. 100)", "Medical Team (ext. 102)"],
    "Personnel Safety":  ["Medical Team (ext. 102)", "Zone Supervisor (ext. 204)", "Safety Officer (ext. 201)"],
    "Multi-Hazard":      ["Fire Brigade (ext. 100)", "Safety Officer (ext. 201)", "Plant Manager (ext. 300)", "Medical Team (ext. 102)", "Security (ext. 108)"],
}

BROADCAST_CALLBACK = None


def register_broadcast(callback) -> None:
    global BROADCAST_CALLBACK
    BROADCAST_CALLBACK = callback


def _generate_action_plan(risk: dict) -> list[str]:
    """Generate step-by-step action plan based on risk type."""
    base_actions = risk.get("recommended_actions", [])
    category = risk.get("risk_category", "")
    zone_name = ZONE_NAMES.get(risk["zone_id"], risk["zone_id"])
    score = risk.get("risk_score", 0)
    eta = risk.get("eta_to_incident", 30)

    plan = [
        f"⚠️  SENTINEL AI ALERT: {risk['risk_type']}",
        f"📍 Affected Zone: {zone_name}",
        f"🎯 Risk Score: {score}/100 | ETA: {eta} minutes",
        "─" * 50,
    ]

    # Severity-based preamble
    if score >= 90:
        plan.append("🔴 CRITICAL EMERGENCY — IMMEDIATE ACTION REQUIRED")
    elif score >= 75:
        plan.append("🟠 HIGH PRIORITY — Act within 5 minutes")
    else:
        plan.append("🟡 ELEVATED RISK — Monitor and prepare response")

    plan.append("")
    plan.append("RECOMMENDED ACTIONS:")
    for i, action in enumerate(base_actions, 1):
        plan.append(f"  {i}. {action}")

    return plan


def _get_evacuation_zones(zone_id: str, severity: str) -> list[str]:
    adjacent = ADJACENT_ZONES.get(zone_id, [])
    if severity == "critical":
        return [zone_id] + adjacent
    return [zone_id]


def trigger_emergency_response(risk: dict) -> dict:
    """
    Main orchestrator entry point. Called when a critical or high risk is detected.
    Stores emergency event, generates plan, broadcasts alert.
    """
    zone_id = risk["zone_id"]
    category = risk.get("risk_category", "Multi-Hazard")
    severity = risk["severity"]
    score = risk.get("risk_score", 0)

    # Only auto-trigger for high/critical
    if score < 70:
        return {"triggered": False, "reason": "Risk score below response threshold (70)"}

    action_plan = _generate_action_plan(risk)
    evacuation_zones = _get_evacuation_zones(zone_id, severity)
    responders = RESPONDERS.get(category, RESPONDERS["Multi-Hazard"])

    # Store emergency event
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            """INSERT INTO emergency_events
               (risk_assessment_id, zone_id, event_type, severity,
                action_plan, evacuation_zones, responders_notified, status)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                risk.get("id"),
                zone_id,
                risk.get("risk_type", "Unknown Risk"),
                severity,
                json.dumps(action_plan),
                json.dumps([{"zone_id": z, "zone_name": ZONE_NAMES.get(z, z)} for z in evacuation_zones]),
                json.dumps(responders),
                "active",
            ),
        )
        conn.commit()
        event_id = c.lastrowid

    event = {
        "id": event_id,
        "risk": risk,
        "action_plan": action_plan,
        "evacuation_zones": [{"zone_id": z, "zone_name": ZONE_NAMES.get(z, z)} for z in evacuation_zones],
        "responders": responders,
        "triggered_at": datetime.utcnow().isoformat(),
        "status": "active",
        "triggered": True,
    }

    # Broadcast emergency alert
    if BROADCAST_CALLBACK:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(
                    BROADCAST_CALLBACK({"type": "emergency", "data": event})
                )
        except Exception as exc:
            print(f"[Orchestrator] Broadcast error: {exc}")

    print(f"[Orchestrator] Emergency triggered: {risk['risk_type']} in {zone_id} (score={score})")
    return event


def get_active_emergencies() -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            """SELECT id, risk_assessment_id, zone_id, event_type, severity,
                      action_plan, evacuation_zones, responders_notified, status, created_at
               FROM emergency_events WHERE status='active'
               ORDER BY created_at DESC""",
        )
        results = []
        for row in c.fetchall():
            results.append({
                "id": row[0],
                "risk_assessment_id": row[1],
                "zone_id": row[2],
                "zone_name": ZONE_NAMES.get(row[2], row[2]),
                "event_type": row[3],
                "severity": row[4],
                "action_plan": json.loads(row[5] or "[]"),
                "evacuation_zones": json.loads(row[6] or "[]"),
                "responders": json.loads(row[7] or "[]"),
                "status": row[8],
                "created_at": row[9],
            })
        return results


def resolve_emergency(event_id: int) -> dict:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE emergency_events SET status='resolved', resolved_at=? WHERE id=?",
            (datetime.utcnow().isoformat(), event_id),
        )
        conn.commit()
    return {"id": event_id, "status": "resolved", "resolved_at": datetime.utcnow().isoformat()}


def get_evacuation_plan(zone_id: str) -> dict:
    """Generate an evacuation plan for a given zone."""
    evacuation_zones = _get_evacuation_zones(zone_id, "critical")
    zone_name = ZONE_NAMES.get(zone_id, zone_id)

    plan = {
        "primary_zone": {"zone_id": zone_id, "zone_name": zone_name},
        "evacuation_zones": [{"zone_id": z, "zone_name": ZONE_NAMES.get(z, z)} for z in evacuation_zones],
        "muster_points": [
            {"id": "MP-1", "location": "Main Gate Assembly Area", "capacity": 200},
            {"id": "MP-2", "location": "East Parking Lot",        "capacity": 150},
            {"id": "MP-3", "location": "Admin Building Lobby",    "capacity": 100},
        ],
        "evacuation_routes": [
            f"Exit {zone_name} via Emergency Exit E-1 (North side)",
            "Proceed to muster point MP-1 at Main Gate",
            "Do NOT use elevators",
            "Assist injured personnel to nearest exit",
            "Report to zone supervisor at muster point",
        ],
        "do_not": [
            "Do NOT re-enter evacuated zones",
            "Do NOT use mobile phones near gas leak areas",
            "Do NOT start vehicles near chemical zones",
        ],
        "emergency_contacts": [
            "Fire Brigade: ext. 100 / 0800-FIRE",
            "Medical Emergency: ext. 102",
            "Safety Officer: ext. 201",
            "Plant Manager: ext. 300",
        ],
        "generated_at": datetime.utcnow().isoformat(),
    }
    return plan
