"""Digital Permit-to-Work Management API."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services.permit_service import (
    create_permit,
    list_permits,
    get_permit,
    update_permit_status,
    detect_overlaps,
    get_active_permits_summary,
    PERMIT_TYPES,
)

router = APIRouter(prefix="/permits", tags=["permits"])


class PermitCreate(BaseModel):
    permit_type: str
    zone_id: str
    worker_name: str
    description: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    issued_by: str = "Safety Officer"
    hazards: Optional[List[str]] = []
    precautions: Optional[List[str]] = []
    duration_hours: int = 8


@router.post("/")
def create_new_permit(body: PermitCreate):
    if body.permit_type not in PERMIT_TYPES:
        raise HTTPException(400, detail=f"Invalid permit_type. Valid: {list(PERMIT_TYPES.keys())}")

    start = body.start_time or datetime.utcnow().isoformat()
    end = body.end_time or (datetime.utcnow() + timedelta(hours=body.duration_hours)).isoformat()

    try:
        permit = create_permit(
            permit_type=body.permit_type,
            zone_id=body.zone_id,
            worker_name=body.worker_name,
            description=body.description,
            start_time=start,
            end_time=end,
            issued_by=body.issued_by,
            hazards=body.hazards,
            precautions=body.precautions,
        )
        # Check overlaps immediately after creation
        overlaps = detect_overlaps(zone_id=body.zone_id)
        return {
            "permit": permit,
            "overlap_warnings": overlaps,
            "has_unsafe_overlap": len(overlaps) > 0,
        }
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc))


@router.get("/")
def get_permits(
    status: Optional[str] = Query(default=None),
    zone_id: Optional[str] = Query(default=None),
):
    return list_permits(status=status, zone_id=zone_id)


@router.get("/summary")
def active_summary():
    """Active permits summary with overlap detection."""
    return get_active_permits_summary()


@router.get("/overlaps")
def check_overlaps(zone_id: Optional[str] = Query(default=None)):
    """Check for unsafe permit overlaps."""
    return detect_overlaps(zone_id=zone_id)


@router.get("/types")
def permit_types():
    return [{"type": k, "label": v} for k, v in PERMIT_TYPES.items()]


@router.get("/{permit_id}")
def get_single_permit(permit_id: int):
    p = get_permit(permit_id)
    if not p:
        raise HTTPException(404, detail="Permit not found")
    return p


@router.patch("/{permit_id}/status")
def update_status(permit_id: int, status: str):
    try:
        return update_permit_status(permit_id, status)
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc))
