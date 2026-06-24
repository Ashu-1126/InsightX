"""Sensor Intelligence API — real-time IoT data endpoints + WebSocket stream."""

import asyncio
import json
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from typing import List

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services.sensor_service import (
    get_current_readings,
    get_zone_summary,
    get_sensor_history,
    get_zone_history,
    get_anomalous_sensors,
    ZONE_IDS,
    SENSOR_TYPES,
    THRESHOLDS,
    SENSOR_UNITS,
)

router = APIRouter(prefix="/sensors", tags=["sensors"])

# WebSocket pool for real-time sensor push
_sensor_ws_clients: List[WebSocket] = []


@router.get("/current")
def current_readings():
    """All latest sensor readings across all zones."""
    return get_current_readings()


@router.get("/zones")
def zone_summary():
    """Per-zone sensor summary with warning/critical flags."""
    return get_zone_summary()


@router.get("/anomalies")
def anomalous_sensors(minutes: int = Query(default=5, ge=1, le=60)):
    """Sensors that have been anomalous in the last N minutes."""
    return get_anomalous_sensors(minutes)


@router.get("/history/{sensor_id}")
def sensor_history(
    sensor_id: str,
    minutes: int = Query(default=30, ge=5, le=360),
):
    """Historical readings for a specific sensor."""
    return get_sensor_history(sensor_id, minutes)


@router.get("/history/{zone_id}/{sensor_type}")
def zone_sensor_history(
    zone_id: str,
    sensor_type: str,
    minutes: int = Query(default=60, ge=5, le=360),
):
    """Historical readings for a sensor type in a specific zone."""
    if zone_id not in ZONE_IDS:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Invalid zone_id: {zone_id}")
    if sensor_type not in SENSOR_TYPES:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Invalid sensor_type: {sensor_type}")
    return get_zone_history(zone_id, sensor_type, minutes)


@router.get("/thresholds")
def get_thresholds():
    """Return sensor thresholds and units for all sensor types."""
    return [
        {
            "sensor_type": stype,
            "unit": SENSOR_UNITS[stype],
            "threshold_warning": THRESHOLDS[stype][0],
            "threshold_critical": THRESHOLDS[stype][1],
        }
        for stype in SENSOR_TYPES
    ]


@router.get("/types")
def get_sensor_types():
    return {"zone_ids": ZONE_IDS, "sensor_types": SENSOR_TYPES}


@router.websocket("/ws/sensors")
async def sensor_websocket(websocket: WebSocket):
    """Push real-time sensor readings every 5 seconds."""
    await websocket.accept()
    _sensor_ws_clients.append(websocket)
    try:
        while True:
            readings = get_current_readings()
            zones = get_zone_summary()
            await websocket.send_json({
                "type": "sensor_update",
                "readings": readings,
                "zones": zones,
            })
            await asyncio.sleep(5)
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        if websocket in _sensor_ws_clients:
            _sensor_ws_clients.remove(websocket)
