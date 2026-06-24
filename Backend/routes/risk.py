"""Compound Risk Detection API."""

from fastapi import APIRouter, Query
from typing import Optional

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services.risk_engine import (
    get_active_risks,
    get_zone_risk_score,
    get_risk_timeline,
    evaluate_now,
    RISK_RULES,
)

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("/active")
def active_risks():
    """All currently active compound risk assessments."""
    return get_active_risks()


@router.get("/zones")
def zone_risk_scores():
    """Risk score summary for each zone."""
    zone_ids = ["zone_a", "zone_b", "zone_c", "zone_d", "zone_e", "zone_f"]
    return [get_zone_risk_score(z) for z in zone_ids]


@router.get("/zone/{zone_id}")
def zone_risk(zone_id: str):
    """Risk details for a specific zone."""
    return get_zone_risk_score(zone_id)


@router.get("/timeline")
def risk_timeline(hours: int = Query(default=24, ge=1, le=168)):
    """Historical risk assessments over the last N hours."""
    return get_risk_timeline(hours)


@router.post("/evaluate")
def force_evaluate(zone_id: Optional[str] = None):
    """Force immediate risk evaluation (useful for demos)."""
    return evaluate_now(zone_id)


@router.get("/rules")
def get_risk_rules():
    """Return all compound risk rule definitions."""
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "category": r["category"],
            "description": r["description"],
            "severity": r["severity"],
            "base_score": r["base_score"],
            "probability": r["probability"],
            "eta_minutes": r["eta_minutes"],
            "condition_count": len(r["conditions"]),
        }
        for r in RISK_RULES
    ]
