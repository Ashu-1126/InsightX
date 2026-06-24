"""Multi-Agent Architecture API — FEATURE A."""

from fastapi import APIRouter
from pydantic import BaseModel

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from agents.master_orchestrator import dispatch, full_briefing, list_agents

router = APIRouter(prefix="/agents", tags=["multi-agent"])


class DispatchRequest(BaseModel):
    task: str
    context: dict | None = None
    agents: list[str] | None = None


@router.post("/dispatch")
def dispatch_task(body: DispatchRequest):
    """Route a task to appropriate sub-agent(s) and return synthesized result."""
    return dispatch(body.task, body.context, body.agents)


@router.get("/briefing")
def plant_briefing():
    """Run all agents in parallel and return a full plant safety briefing."""
    return full_briefing()


@router.get("/")
def agents_list():
    """List all registered agents with their tool descriptions."""
    return list_agents()
