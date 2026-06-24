"""AI Safety Intelligence API — RAG-powered queries and pattern detection."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services.rag_service import answer_query, detect_patterns, add_document, retrieve_documents
from services.risk_engine import get_active_risks
from services.sensor_service import get_anomalous_sensors
from services.permit_service import list_permits

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


class QueryBody(BaseModel):
    query: str
    include_live_context: bool = True


class DocumentBody(BaseModel):
    title: str
    content: str
    document_type: str = "general"
    tags: Optional[List[str]] = []


@router.post("/query")
def query_intelligence(body: QueryBody):
    """Ask the AI Safety Copilot a question."""
    if not body.query or not body.query.strip():
        raise HTTPException(400, detail="Query cannot be empty")

    context = {}
    if body.include_live_context:
        context["active_risks"] = get_active_risks()[:5]
        context["active_permits"] = list_permits(status="active")[:5]
        context["anomalous_sensors"] = get_anomalous_sensors(minutes=10)[:5]

    return answer_query(body.query, context=context, use_llm=True)


@router.get("/patterns")
def incident_patterns():
    """Detect recurring patterns in historical incident data."""
    return detect_patterns()


@router.post("/documents")
def add_kb_document(body: DocumentBody):
    """Add a document to the knowledge base."""
    return add_document(body.title, body.content, body.document_type, body.tags)


@router.get("/search")
def search_documents(q: str, top_k: int = 5):
    """Search the knowledge base by keyword."""
    if not q:
        raise HTTPException(400, detail="Search query required")
    return retrieve_documents(q, top_k)


@router.get("/context")
def get_live_context():
    """Return current live context used by the AI copilot."""
    return {
        "active_risks": get_active_risks(),
        "active_permits": list_permits(status="active"),
        "anomalous_sensors": get_anomalous_sensors(minutes=10),
    }
