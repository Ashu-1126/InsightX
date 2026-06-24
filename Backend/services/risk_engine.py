"""
Compound Risk Detection Engine — MODULE 2 [CORE]

Correlates data from:
  • CCTV / CV events (incidents table)
  • Sensor readings (sensor_readings table)
  • Active permits (permits table)
  • Shift records
  • Maintenance logs

Detects compound risk conditions that no single sensor can detect alone.
Runs evaluation every 30 seconds and stores results in risk_assessments.
"""

import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Any

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import DB_PATH

# ── Risk Rule Definitions ────────────────────────────────────────────────────
# Each rule defines a compound risk scenario with its scoring parameters.
# Conditions are ANDed together; the rule fires if ALL conditions are met.

RISK_RULES: list[dict] = [
    {
        "id": "EXPLOSION_HOT_WORK_GAS",
        "name": "Explosion Risk: Hot Work + Elevated Gas",
        "category": "Explosion",
        "description": "Hot work permit active while methane exceeds warning threshold.",
        "severity": "critical",
        "base_score": 92,
        "probability": 0.88,
        "eta_minutes": 15,
        "conditions": [
            {"source": "sensor",  "sensor_type": "methane",     "operator": ">=", "threshold_key": "warning"},
            {"source": "permit",  "permit_type": "hot_work",    "status": "active"},
        ],
        "contributing": ["Hot work permit active", "Elevated methane concentration"],
        "actions": ["Suspend hot work immediately", "Evacuate zone", "Activate ventilation", "Notify fire team"],
    },
    {
        "id": "EXPLOSION_CRITICAL_GAS_HOT_WORK",
        "name": "IMMINENT Explosion: Critical Gas + Hot Work",
        "category": "Explosion",
        "description": "Methane at critical level with hot work permit — imminent explosion risk.",
        "severity": "critical",
        "base_score": 98,
        "probability": 0.97,
        "eta_minutes": 5,
        "conditions": [
            {"source": "sensor",  "sensor_type": "methane",     "operator": ">=", "threshold_key": "critical"},
            {"source": "permit",  "permit_type": "hot_work",    "status": "active"},
        ],
        "contributing": ["CRITICAL methane level", "Active hot work — immediate ignition risk"],
        "actions": ["EMERGENCY EVACUATION", "Kill all ignition sources", "Call fire brigade", "Activate gas suppression"],
    },
    {
        "id": "FIRE_GAS_COMPOUND",
        "name": "Fire + Elevated Gas: Explosion Cascade",
        "category": "Explosion",
        "description": "CV fire/smoke detection with elevated methane — cascade explosion risk.",
        "severity": "critical",
        "base_score": 95,
        "probability": 0.94,
        "eta_minutes": 8,
        "conditions": [
            {"source": "cv_event", "incident_type": "fire-smoke", "minutes": 10},
            {"source": "sensor",  "sensor_type": "methane",      "operator": ">=", "threshold_key": "warning"},
        ],
        "contributing": ["Active fire/smoke detected by CCTV", "Elevated methane in zone"],
        "actions": ["Emergency evacuation", "Activate fire suppression", "Call emergency services"],
    },
    {
        "id": "CONFINED_SPACE_OXYGEN",
        "name": "Asphyxiation Risk: Confined Space + Poor Air Quality",
        "category": "Asphyxiation",
        "description": "Confined space permit active with elevated smoke and humidity — oxygen displacement risk.",
        "severity": "high",
        "base_score": 84,
        "probability": 0.76,
        "eta_minutes": 25,
        "conditions": [
            {"source": "permit",  "permit_type": "confined_space", "status": "active"},
            {"source": "sensor",  "sensor_type": "smoke",          "operator": ">=", "threshold_key": "warning"},
        ],
        "contributing": ["Confined space entry permit active", "Poor air quality (smoke elevated)"],
        "actions": ["Verify atmospheric readings", "Deploy standby rescuer", "Increase ventilation", "Brief entry workers"],
    },
    {
        "id": "MAINTENANCE_HIGH_PRESSURE",
        "name": "Equipment Failure: Maintenance + Abnormal Pressure",
        "category": "Equipment Failure",
        "description": "Maintenance permit active while pressure exceeds warning threshold.",
        "severity": "high",
        "base_score": 81,
        "probability": 0.72,
        "eta_minutes": 30,
        "conditions": [
            {"source": "permit",  "permit_type": "maintenance",  "status": "active"},
            {"source": "sensor",  "sensor_type": "pressure",     "operator": ">=", "threshold_key": "warning"},
        ],
        "contributing": ["Active maintenance permit", "Elevated pressure reading"],
        "actions": ["Halt maintenance operations", "Relieve pressure to safe level", "Inspect pressure relief valves"],
    },
    {
        "id": "MAINTENANCE_HIGH_VIBRATION",
        "name": "Equipment Failure: Maintenance + High Vibration",
        "category": "Equipment Failure",
        "description": "Vibration exceeds threshold during active maintenance — catastrophic failure risk.",
        "severity": "high",
        "base_score": 79,
        "probability": 0.68,
        "eta_minutes": 35,
        "conditions": [
            {"source": "permit",   "permit_type": "maintenance", "status": "active"},
            {"source": "sensor",   "sensor_type": "vibration",   "operator": ">=", "threshold_key": "warning"},
        ],
        "contributing": ["Maintenance permit active", "Excessive vibration detected"],
        "actions": ["Stop maintenance work", "Inspect rotating equipment", "Check bearing temperature"],
    },
    {
        "id": "PPE_VIOLATION_HIGH_HEAT",
        "name": "Burn Risk: PPE Violation + High Temperature",
        "category": "Personnel Safety",
        "description": "PPE violation detected by CCTV with elevated temperature in zone.",
        "severity": "high",
        "base_score": 77,
        "probability": 0.65,
        "eta_minutes": 20,
        "conditions": [
            {"source": "cv_event", "incident_type": "ppe",      "minutes": 15},
            {"source": "sensor",  "sensor_type": "temperature", "operator": ">=", "threshold_key": "warning"},
        ],
        "contributing": ["PPE violation detected by CCTV", "High temperature in zone"],
        "actions": ["Enforce PPE compliance", "Remove unprotected workers", "Lower zone temperature if possible"],
    },
    {
        "id": "MULTI_SENSOR_CRITICAL",
        "name": "Multi-Hazard Zone: 3+ Sensors Critical",
        "category": "Multi-Hazard",
        "description": "Three or more sensors simultaneously at critical level — cascade failure imminent.",
        "severity": "critical",
        "base_score": 90,
        "probability": 0.85,
        "eta_minutes": 12,
        "conditions": [
            {"source": "multi_sensor_critical", "count": 3},
        ],
        "contributing": ["Multiple sensors at critical threshold simultaneously"],
        "actions": ["Immediate zone evacuation", "Halt all operations in zone", "Emergency safety audit"],
    },
    {
        "id": "CHEMICAL_TEMP_PERMIT",
        "name": "Chemical Release Risk: High Temp + Chemical Permit",
        "category": "Chemical Hazard",
        "description": "Chemical processing permit active with temperature above critical threshold.",
        "severity": "critical",
        "base_score": 88,
        "probability": 0.82,
        "eta_minutes": 18,
        "conditions": [
            {"source": "permit",  "permit_type": "chemical",    "status": "active"},
            {"source": "sensor",  "sensor_type": "temperature", "operator": ">=", "threshold_key": "critical"},
        ],
        "contributing": ["Chemical processing permit active", "Critical temperature exceeded"],
        "actions": ["Stop chemical process", "Cool zone", "Check reaction vessels", "Prepare containment"],
    },
    {
        "id": "FALL_SHIFT_CHANGE",
        "name": "Elevated Fall Risk: Fall Detected + Shift Change",
        "category": "Personnel Safety",
        "description": "Fall detected during shift change window — high-risk handover period.",
        "severity": "medium",
        "base_score": 65,
        "probability": 0.55,
        "eta_minutes": 60,
        "conditions": [
            {"source": "cv_event", "incident_type": "fall",    "minutes": 30},
            {"source": "shift_change", "window_minutes": 60},
        ],
        "contributing": ["Fall incident in zone", "Active shift change period"],
        "actions": ["Ensure proper shift handover", "Check injured worker status", "Review zone safety briefing"],
    },
]

# ── State ─────────────────────────────────────────────────────────────────────
_active_risks: list[dict] = []
_active_risks_lock = threading.Lock()
_engine_started = False
_engine_lock = threading.Lock()

BROADCAST_CALLBACK = None  # Set by main.py after startup


def register_broadcast(callback) -> None:
    global BROADCAST_CALLBACK
    BROADCAST_CALLBACK = callback


# ── Data Fetchers ─────────────────────────────────────────────────────────────

def _get_sensor_state(zone_id: str) -> dict[str, dict]:
    """Return latest sensor reading per type for a zone."""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            """SELECT s.sensor_type, sr.value, s.threshold_warning, s.threshold_critical, s.unit
               FROM sensor_readings sr
               JOIN sensors s ON sr.sensor_id = s.id
               WHERE sr.zone_id = ?
               AND sr.timestamp = (
                   SELECT MAX(sr2.timestamp) FROM sensor_readings sr2
                   WHERE sr2.sensor_id = sr.sensor_id
               )""",
            (zone_id,),
        )
        result = {}
        for row in c.fetchall():
            stype, value, warn, crit, unit = row
            result[stype] = {
                "value": value,
                "threshold_warning": warn,
                "threshold_critical": crit,
                "unit": unit,
                "is_warning": value >= warn if warn else False,
                "is_critical": value >= crit if crit else False,
            }
        return result


def _get_active_permits(zone_id: str) -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            "SELECT permit_type, permit_number, worker_name, start_time, end_time "
            "FROM permits WHERE zone_id=? AND status='active' "
            "AND end_time >= ?",
            (zone_id, datetime.utcnow().isoformat()),
        )
        return [
            {"permit_type": r[0], "permit_number": r[1], "worker_name": r[2],
             "start_time": r[3], "end_time": r[4]}
            for r in c.fetchall()
        ]


def _get_recent_cv_events(zone_id: str, incident_type: str, minutes: int) -> list[dict]:
    cutoff = (datetime.utcnow() - timedelta(minutes=minutes)).isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # Map zone_id to camera_id
        c.execute("SELECT camera_id FROM zones WHERE id=?", (zone_id,))
        row = c.fetchone()
        camera_id = row[0] if row else None

        if camera_id:
            c.execute(
                "SELECT id, type, confidence, created_at FROM incidents "
                "WHERE type=? AND camera_id=? AND created_at >= ? "
                "ORDER BY created_at DESC LIMIT 5",
                (incident_type, camera_id, cutoff),
            )
        else:
            c.execute(
                "SELECT id, type, confidence, created_at FROM incidents "
                "WHERE type=? AND created_at >= ? "
                "ORDER BY created_at DESC LIMIT 5",
                (incident_type, cutoff),
            )
        return [
            {"id": r[0], "type": r[1], "confidence": r[2], "created_at": r[3]}
            for r in c.fetchall()
        ]


def _is_shift_change_window() -> bool:
    """Returns True if current time is within 30 mins of a shift change."""
    now = datetime.utcnow()
    shift_times = [6, 14, 22]  # hours UTC for shift changes
    for hour in shift_times:
        delta_mins = abs((now.hour * 60 + now.minute) - hour * 60)
        if delta_mins <= 30 or delta_mins >= (24 * 60 - 30):
            return True
    return False


def _count_critical_sensors(zone_id: str, sensors: dict[str, dict]) -> int:
    return sum(1 for s in sensors.values() if s.get("is_critical"))


# ── Rule Evaluation ───────────────────────────────────────────────────────────

def _evaluate_condition(cond: dict, zone_id: str, sensors: dict,
                        permits: list, zone_id_override: str = None) -> bool:
    src = cond["source"]

    if src == "sensor":
        sdata = sensors.get(cond["sensor_type"])
        if not sdata:
            return False
        op = cond["operator"]
        thresh_key = cond["threshold_key"]
        thresh_val = sdata[f"threshold_{thresh_key}"]
        val = sdata["value"]
        if thresh_val is None:
            return False
        if op == ">=":
            return val >= thresh_val
        if op == ">":
            return val > thresh_val
        if op == "<=":
            return val <= thresh_val
        return False

    if src == "permit":
        return any(p["permit_type"] == cond["permit_type"] for p in permits)

    if src == "cv_event":
        events = _get_recent_cv_events(zone_id, cond["incident_type"], cond.get("minutes", 15))
        return len(events) > 0

    if src == "multi_sensor_critical":
        return _count_critical_sensors(zone_id, sensors) >= cond.get("count", 2)

    if src == "shift_change":
        return _is_shift_change_window()

    return False


def _evaluate_zone(zone_id: str) -> list[dict]:
    sensors = _get_sensor_state(zone_id)
    permits = _get_active_permits(zone_id)
    zone_risks = []

    for rule in RISK_RULES:
        conditions_met = all(
            _evaluate_condition(cond, zone_id, sensors, permits)
            for cond in rule["conditions"]
        )
        if not conditions_met:
            continue

        # Score modifiers
        score = rule["base_score"]
        # Boost score if multiple sensors critical
        critical_count = _count_critical_sensors(zone_id, sensors)
        score = min(100, score + critical_count * 2)
        # Boost if multiple permits overlap
        if len(permits) >= 2:
            score = min(100, score + 5)

        # Build contributing factors detail
        sensor_details = []
        for stype, sdata in sensors.items():
            if sdata.get("is_critical"):
                sensor_details.append(f"{stype}: {sdata['value']} {sdata['unit']} [CRITICAL]")
            elif sdata.get("is_warning"):
                sensor_details.append(f"{stype}: {sdata['value']} {sdata['unit']} [WARNING]")

        permit_details = [f"{p['permit_type']} permit (#{p['permit_number']}) — {p['worker_name']}"
                          for p in permits]

        contributing_factors = rule["contributing"] + sensor_details + permit_details

        risk_record = {
            "rule_id": rule["id"],
            "zone_id": zone_id,
            "risk_type": rule["name"],
            "risk_category": rule["category"],
            "description": rule["description"],
            "severity": rule["severity"],
            "risk_score": score,
            "probability": round(min(0.99, rule["probability"] + critical_count * 0.01), 2),
            "eta_to_incident": max(1, rule["eta_minutes"] - critical_count * 2),
            "contributing_factors": contributing_factors,
            "recommended_actions": rule["actions"],
            "active_permits": permits,
            "sensor_snapshot": {
                stype: {"value": s["value"], "unit": s["unit"],
                        "is_warning": s["is_warning"], "is_critical": s["is_critical"]}
                for stype, s in sensors.items()
            },
            "detected_at": datetime.utcnow().isoformat(),
        }
        zone_risks.append(risk_record)

    return zone_risks


def _store_risk(risk: dict) -> int:
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # Mark previous active risks for this zone/rule as resolved
        c.execute(
            "UPDATE risk_assessments SET is_active=0, resolved_at=? "
            "WHERE zone_id=? AND risk_type=? AND is_active=1",
            (datetime.utcnow().isoformat(), risk["zone_id"], risk["risk_type"]),
        )
        c.execute(
            """INSERT INTO risk_assessments
               (zone_id, risk_score, severity, risk_type, risk_category,
                probability, eta_to_incident, contributing_factors, triggered_by)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                risk["zone_id"],
                risk["risk_score"],
                risk["severity"],
                risk["risk_type"],
                risk["risk_category"],
                risk["probability"],
                risk["eta_to_incident"],
                json.dumps(risk["contributing_factors"]),
                json.dumps({"permits": risk["active_permits"],
                            "sensors": risk["sensor_snapshot"]}),
            ),
        )
        conn.commit()
        return c.lastrowid


def _engine_loop() -> None:
    ZONE_IDS = ["zone_a", "zone_b", "zone_c", "zone_d", "zone_e", "zone_f"]
    while True:
        try:
            all_risks = []
            for zone_id in ZONE_IDS:
                zone_risks = _evaluate_zone(zone_id)
                all_risks.extend(zone_risks)

            # Store new/updated risks
            for risk in all_risks:
                risk_id = _store_risk(risk)
                risk["id"] = risk_id

            # Mark zones with no active risks as having risks resolved
            active_zone_ids = {r["zone_id"] for r in all_risks}
            for zone_id in ZONE_IDS:
                if zone_id not in active_zone_ids:
                    with sqlite3.connect(DB_PATH) as conn:
                        conn.execute(
                            "UPDATE risk_assessments SET is_active=0, resolved_at=? "
                            "WHERE zone_id=? AND is_active=1",
                            (datetime.utcnow().isoformat(), zone_id),
                        )
                        conn.commit()

            with _active_risks_lock:
                _active_risks.clear()
                _active_risks.extend(all_risks)

            # Broadcast if callback registered
            if BROADCAST_CALLBACK and all_risks:
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.ensure_future(
                            BROADCAST_CALLBACK({"type": "risk_update", "data": all_risks})
                        )
                except Exception:
                    pass

        except Exception as exc:
            print(f"[RiskEngine] Error in evaluation loop: {exc}")

        time.sleep(30)


def start_risk_engine() -> None:
    global _engine_started
    with _engine_lock:
        if _engine_started:
            return
        t = threading.Thread(target=_engine_loop, daemon=True, name="RiskEngine")
        t.start()
        _engine_started = True
        print("[RiskEngine] Compound risk detection engine started.")


# ── Public API ────────────────────────────────────────────────────────────────

def get_active_risks() -> list[dict]:
    with _active_risks_lock:
        return list(_active_risks)


def get_zone_risk_score(zone_id: str) -> dict:
    with _active_risks_lock:
        zone_risks = [r for r in _active_risks if r["zone_id"] == zone_id]
    if not zone_risks:
        return {"zone_id": zone_id, "risk_score": 0, "severity": "safe", "risk_count": 0}
    top = max(zone_risks, key=lambda r: r["risk_score"])
    return {
        "zone_id": zone_id,
        "risk_score": top["risk_score"],
        "severity": top["severity"],
        "risk_count": len(zone_risks),
        "top_risk": top["risk_type"],
    }


def get_risk_timeline(hours: int = 24) -> list[dict]:
    cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            """SELECT id, zone_id, risk_score, severity, risk_type, risk_category,
                      probability, eta_to_incident, created_at, is_active
               FROM risk_assessments WHERE created_at >= ?
               ORDER BY created_at DESC LIMIT 200""",
            (cutoff,),
        )
        return [
            {
                "id": r[0], "zone_id": r[1], "risk_score": r[2],
                "severity": r[3], "risk_type": r[4], "risk_category": r[5],
                "probability": r[6], "eta_to_incident": r[7],
                "created_at": r[8], "is_active": bool(r[9]),
            }
            for r in c.fetchall()
        ]


def evaluate_now(zone_id: str = None) -> list[dict]:
    """Force immediate evaluation. Useful for demo/testing."""
    ZONE_IDS = ["zone_a", "zone_b", "zone_c", "zone_d", "zone_e", "zone_f"]
    zones = [zone_id] if zone_id else ZONE_IDS
    results = []
    for zid in zones:
        results.extend(_evaluate_zone(zid))
    return results
