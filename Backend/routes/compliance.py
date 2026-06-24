"""Quality & Compliance Audit API — MODULE 7."""

from fastapi import APIRouter

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services.compliance_service import (
    run_compliance_audit,
    get_compliance_score,
    get_standard_info,
    COMPLIANCE_CHECKS,
)

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.get("/audit")
def full_audit():
    """Run a complete compliance audit against all standards."""
    return run_compliance_audit()


@router.get("/score")
def compliance_score():
    """Quick compliance score summary."""
    return get_compliance_score()


@router.get("/standards")
def standards():
    """List all compliance standards covered by the system."""
    return get_standard_info()


@router.get("/checks")
def list_checks():
    """List all compliance check definitions."""
    return [
        {
            "id": c["id"],
            "standard": c["standard"],
            "category": c["category"],
            "requirement": c["requirement"],
            "severity": c["severity"],
            "check_type": c["check_type"],
        }
        for c in COMPLIANCE_CHECKS
    ]
