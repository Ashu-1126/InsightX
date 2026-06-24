"""
Sensor Intelligence Layer — MODULE 1
Simulates 6 industrial IoT sensor types across 6 plant zones.
Runs a background thread that stores readings every 5 seconds.
Provides current readings, historical trend data, and anomaly flags.
"""

import math
import random
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Any

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import DB_PATH

# ── Sensor simulation parameters ────────────────────────────────────────────
# Each entry: (base, amplitude, period_s, noise_std, spike_prob, spike_mult)
SENSOR_PROFILES: dict[str, tuple] = {
    "methane":     (3.5,  2.0,  300,  0.4,  0.015, 4.0),   # ppm
    "temperature": (32.0, 12.0, 600,  1.0,  0.010, 1.9),   # °C
    "humidity":    (55.0, 20.0, 900,  2.0,  0.005, 1.6),   # %
    "smoke":       (25.0, 20.0, 450,  3.0,  0.012, 8.0),   # µg/m³
    "pressure":    (4.5,  2.0,  720,  0.2,  0.008, 2.2),   # bar
    "vibration":   (6.0,  5.0,  240,  0.8,  0.018, 4.5),   # mm/s
}

# Per-zone environment multipliers (zone_c is chemical — higher baseline)
ZONE_MULTIPLIERS: dict[str, float] = {
    "zone_a": 1.0,
    "zone_b": 0.85,
    "zone_c": 1.35,   # chemical processing — elevated
    "zone_d": 0.90,
    "zone_e": 0.60,   # control room — cooler/cleaner
    "zone_f": 1.20,   # confined space / tanks — slightly elevated
}

ZONE_IDS = ["zone_a", "zone_b", "zone_c", "zone_d", "zone_e", "zone_f"]
SENSOR_TYPES = ["methane", "temperature", "humidity", "smoke", "pressure", "vibration"]
SENSOR_UNITS = {
    "methane": "ppm", "temperature": "°C", "humidity": "%",
    "smoke": "µg/m³", "pressure": "bar", "vibration": "mm/s",
}
THRESHOLDS = {
    # (warning, critical)
    "methane":     (5.0,  10.0),
    "temperature": (45.0, 65.0),
    "humidity":    (75.0, 90.0),
    "smoke":       (100.0, 200.0),
    "pressure":    (6.0,  8.5),
    "vibration":   (15.0, 25.0),
}

# In-memory cache of latest readings, keyed by sensor_id
_current_readings: dict[str, dict] = {}
_lock = threading.Lock()
_worker_started = False
_worker_lock = threading.Lock()

# Drift offsets per sensor (accumulates over time for realism)
_drift: dict[str, float] = {}

# Result caches for expensive DB queries
_history_cache: dict[str, tuple] = {}   # key -> (data, timestamp)
_anomaly_cache: dict = {"data": None, "ts": 0.0}


def _compute_value(sensor_type: str, zone_id: str, t: float) -> float:
    base, amp, period, noise, spike_prob, spike_mult = SENSOR_PROFILES[sensor_type]
    zone_mult = ZONE_MULTIPLIERS.get(zone_id, 1.0)

    # Sine wave trend
    value = base * zone_mult + amp * zone_mult * math.sin(2 * math.pi * t / period)

    # Gaussian noise
    value += random.gauss(0, noise)

    # Persistent drift (slow random walk)
    drift_key = f"{zone_id}_{sensor_type}"
    if drift_key not in _drift:
        _drift[drift_key] = 0.0
    _drift[drift_key] += random.gauss(0, 0.05)
    _drift[drift_key] = max(-base * 0.3, min(base * 0.3, _drift[drift_key]))
    value += _drift[drift_key]

    # Occasional spike
    if random.random() < spike_prob:
        value *= spike_mult

    return max(0.0, round(value, 2))


def _store_reading(conn: sqlite3.Connection, sensor_id: str, zone_id: str,
                   sensor_type: str, value: float) -> None:
    unit = SENSOR_UNITS[sensor_type]
    warn_thresh, crit_thresh = THRESHOLDS[sensor_type]
    is_warning = 1 if value >= warn_thresh else 0
    is_critical = 1 if value >= crit_thresh else 0
    ts = datetime.utcnow().isoformat()

    conn.execute(
        """INSERT INTO sensor_readings
           (sensor_id, zone_id, sensor_type, value, unit, timestamp, is_warning, is_critical)
           VALUES (?,?,?,?,?,?,?,?)""",
        (sensor_id, zone_id, sensor_type, value, unit, ts, is_warning, is_critical),
    )

    reading = {
        "sensor_id": sensor_id,
        "zone_id": zone_id,
        "sensor_type": sensor_type,
        "value": value,
        "unit": unit,
        "timestamp": ts,
        "is_warning": bool(is_warning),
        "is_critical": bool(is_critical),
    }
    with _lock:
        _current_readings[sensor_id] = reading


def _cleanup_old_readings(conn: sqlite3.Connection) -> None:
    cutoff = (datetime.utcnow() - timedelta(hours=6)).isoformat()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM sensor_readings WHERE timestamp < ?", (cutoff,))
    if c.fetchone()[0] > 0:
        conn.execute("DELETE FROM sensor_readings WHERE timestamp < ?", (cutoff,))


def _update_zone_risk_levels(conn: sqlite3.Connection) -> None:
    """Update zone risk_level based on current sensor state."""
    for zone_id in ZONE_IDS:
        critical_count = 0
        warning_count = 0
        for stype in SENSOR_TYPES:
            sid = f"{zone_id}_{stype}"
            reading = _current_readings.get(sid)
            if reading:
                if reading["is_critical"]:
                    critical_count += 1
                elif reading["is_warning"]:
                    warning_count += 1
        if critical_count >= 1:
            level = "critical"
        elif warning_count >= 2:
            level = "warning"
        else:
            level = "safe"
        conn.execute("UPDATE zones SET risk_level=? WHERE id=?", (level, zone_id))


def _simulation_loop() -> None:
    interval = 5  # seconds between readings
    cleanup_counter = 0
    while True:
        t = time.time()
        try:
            with sqlite3.connect(DB_PATH) as conn:
                for zone_id in ZONE_IDS:
                    for stype in SENSOR_TYPES:
                        sensor_id = f"{zone_id}_{stype}"
                        value = _compute_value(stype, zone_id, t)
                        _store_reading(conn, sensor_id, zone_id, stype, value)
                _update_zone_risk_levels(conn)
                cleanup_counter += 1
                if cleanup_counter >= 72:  # every 6 minutes
                    _cleanup_old_readings(conn)
                    cleanup_counter = 0
                conn.commit()
        except Exception as exc:
            print(f"[SensorService] Error in simulation loop: {exc}")

        time.sleep(interval)


def start_sensor_simulation() -> None:
    global _worker_started
    with _worker_lock:
        if _worker_started:
            return
        t = threading.Thread(target=_simulation_loop, daemon=True, name="SensorSimulator")
        t.start()
        _worker_started = True
        print("[SensorService] IoT sensor simulation started.")


# ── Public API ───────────────────────────────────────────────────────────────

def get_current_readings() -> list[dict]:
    with _lock:
        return list(_current_readings.values())


def get_zone_summary() -> list[dict[str, Any]]:
    """Return one summary object per zone with all sensor values."""
    zones: dict[str, dict] = {}
    with _lock:
        for sensor_id, reading in _current_readings.items():
            zone_id = reading["zone_id"]
            if zone_id not in zones:
                zones[zone_id] = {
                    "zone_id": zone_id,
                    "sensors": {},
                    "has_warning": False,
                    "has_critical": False,
                }
            zones[zone_id]["sensors"][reading["sensor_type"]] = reading
            if reading["is_warning"]:
                zones[zone_id]["has_warning"] = True
            if reading["is_critical"]:
                zones[zone_id]["has_critical"] = True
    return list(zones.values())


def get_sensor_history(sensor_id: str, minutes: int = 30) -> list[dict]:
    cache_key = f"{sensor_id}:{minutes}"
    now = time.time()
    cached = _history_cache.get(cache_key)
    if cached and (now - cached[1]) < 5:   # 5 s TTL matches simulation interval
        return cached[0]

    cutoff = (datetime.utcnow() - timedelta(minutes=minutes)).isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            """SELECT value, unit, timestamp, is_warning, is_critical
               FROM sensor_readings
               WHERE sensor_id=? AND timestamp >= ?
               ORDER BY timestamp ASC
               LIMIT 360""",
            (sensor_id, cutoff),
        )
        result = [
            {
                "value": row[0], "unit": row[1], "timestamp": row[2],
                "is_warning": bool(row[3]), "is_critical": bool(row[4]),
            }
            for row in c.fetchall()
        ]
    _history_cache[cache_key] = (result, now)
    return result


def get_zone_history(zone_id: str, sensor_type: str, minutes: int = 60) -> list[dict]:
    sensor_id = f"{zone_id}_{sensor_type}"
    return get_sensor_history(sensor_id, minutes)


def get_anomalous_sensors(minutes: int = 5) -> list[dict]:
    """Return all sensors that have been anomalous in the last N minutes."""
    now = time.time()
    if _anomaly_cache["data"] is not None and (now - _anomaly_cache["ts"]) < 5:
        return _anomaly_cache["data"]

    cutoff = (datetime.utcnow() - timedelta(minutes=minutes)).isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            """SELECT sensor_id, zone_id, sensor_type, MAX(value), unit,
                      MAX(is_warning), MAX(is_critical), MAX(timestamp)
               FROM sensor_readings
               WHERE timestamp >= ? AND (is_warning=1 OR is_critical=1)
               GROUP BY sensor_id""",
            (cutoff,),
        )
        result = [
            {
                "sensor_id": row[0], "zone_id": row[1], "sensor_type": row[2],
                "peak_value": row[3], "unit": row[4],
                "is_warning": bool(row[5]), "is_critical": bool(row[6]),
                "last_seen": row[7],
            }
            for row in c.fetchall()
        ]
    _anomaly_cache["data"] = result
    _anomaly_cache["ts"] = now
    return result
