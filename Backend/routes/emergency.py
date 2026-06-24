"""Emergency Response Orchestrator API."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services.orchestrator import (
    trigger_emergency_response,
    get_active_emergencies,
    resolve_emergency,
    get_evacuation_plan,
)

router = APIRouter(prefix="/emergency", tags=["emergency"])


class ManualTriggerBody(BaseModel):
    zone_id: str
    risk_type: str
    risk_category: str = "Multi-Hazard"
    severity: str = "critical"
    risk_score: float = 90.0
    description: str = "Manual emergency trigger"
    recommended_actions: Optional[list] = []


@router.post("/trigger")
def trigger_emergency(body: ManualTriggerBody):
    """Manually trigger emergency response for a zone."""
    risk = {
        "zone_id": body.zone_id,
        "risk_type": body.risk_type,
        "risk_category": body.risk_category,
        "severity": body.severity,
        "risk_score": body.risk_score,
        "description": body.description,
        "recommended_actions": body.recommended_actions,
        "probability": 0.9,
        "eta_to_incident": 10,
    }
    return trigger_emergency_response(risk)


@router.get("/active")
def active_emergencies():
    """List all currently active emergency events."""
    return get_active_emergencies()


@router.patch("/{event_id}/resolve")
def resolve_event(event_id: int):
    """Mark an emergency event as resolved."""
    return resolve_emergency(event_id)


@router.get("/plan/{zone_id}")
def evacuation_plan(zone_id: str):
    """Get evacuation plan for a specific zone."""
    return get_evacuation_plan(zone_id)
