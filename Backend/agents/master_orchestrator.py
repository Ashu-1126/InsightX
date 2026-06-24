"""
Master Orchestrator — SENTINEL AI Multi-Agent Coordination Layer

Dispatches tasks to specialized sub-agents and synthesizes their outputs
into a unified plant safety intelligence briefing.

Agent roster:
  SensorAgent     → IoT sensor stream analysis
  RiskAgent       → Compound risk evaluation
  PermitAgent     → Permit-to-Work intelligence
  ComplianceAgent → Standards compliance audit

The orchestrator routes tasks by intent and can run all agents in parallel
for a full situational awareness briefing.
"""

from __future__ import annotations
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from agents.sensor_agent import SensorAgent
from agents.risk_agent import RiskAgent
from agents.permit_agent import PermitAgent
from agents.compliance_agent import ComplianceAgent
from agents.base_agent import AgentResult


AGENTS = {
    "sensor":     SensorAgent,
    "risk":       RiskAgent,
    "permit":     PermitAgent,
    "compliance": ComplianceAgent,
}

_agent_instances: dict = {}
_lock = threading.Lock()


def _get_agent(name: str):
    with _lock:
        if name not in _agent_instances:
            _agent_instances[name] = AGENTS[name]()
        return _agent_instances[name]


# ── Intent routing ────────────────────────────────────────────────────────────

_INTENT_MAP: list[tuple[list[str], list[str]]] = [
    # (keywords, agent names to invoke)
    (["sensor", "methane", "temperature", "gas", "pressure", "h2s", "oxygen", "vibration", "anomal"], ["sensor"]),
    (["risk", "compound", "explosion", "hazard", "threat", "danger"], ["risk"]),
    (["permit", "ptw", "hot work", "confined", "height", "electrical", "maintenance"], ["permit"]),
    (["compliance", "oisd", "dgms", "factory act", "audit", "standard", "corrective"], ["compliance"]),
    (["full", "all", "briefing", "status", "overview", "situational", "plant"], ["sensor", "risk", "permit", "compliance"]),
]


def _route_task(task: str) -> list[str]:
    task_l = task.lower()
    for keywords, agents in _INTENT_MAP:
        if any(kw in task_l for kw in keywords):
            return agents
    return ["sensor", "risk"]  # default to core safety agents


# ── Public API ────────────────────────────────────────────────────────────────

def dispatch(task: str, context: dict | None = None, agent_names: list[str] | None = None) -> dict:
    """
    Route a task to one or more agents and collect results.
    If agent_names is None, routing is automatic based on task keywords.
    """
    target_agents = agent_names or _route_task(task)
    ctx = context or {}
    results: dict[str, AgentResult] = {}

    if len(target_agents) == 1:
        agent = _get_agent(target_agents[0])
        results[target_agents[0]] = agent.run(task, ctx)
    else:
        with ThreadPoolExecutor(max_workers=len(target_agents)) as pool:
            futures = {
                pool.submit(_get_agent(name).run, task, ctx): name
                for name in target_agents
            }
            for future in as_completed(futures):
                name = futures[future]
                try:
                    results[name] = future.result()
                except Exception as exc:
                    results[name] = AgentResult(
                        agent_name=name, task=task,
                        status="error", output=None, error=str(exc),
                    )

    return _synthesize(task, results, target_agents)


def full_briefing() -> dict:
    """Run all four agents in parallel and return a unified safety briefing."""
    return dispatch("full plant situational awareness briefing", agent_names=["sensor", "risk", "permit", "compliance"])


def list_agents() -> list[dict]:
    """Describe all registered agents and their tools."""
    return [
        {
            "name": cls.name,
            "description": cls.description,
            "tools": cls().list_tools(),
        }
        for cls in AGENTS.values()
    ]


# ── Synthesis ─────────────────────────────────────────────────────────────────

def _synthesize(task: str, results: dict[str, AgentResult], agents_used: list[str]) -> dict:
    """Merge multi-agent outputs into a structured briefing."""
    outputs = {
        name: (res.output if res.status == "success" else {"error": res.error})
        for name, res in results.items()
    }

    # Build summary headline
    sensor_out = outputs.get("sensor", {}) or {}
    risk_out = outputs.get("risk", {}) or {}
    permit_out = outputs.get("permit", {}) or {}
    compliance_out = outputs.get("compliance", {}) or {}

    critical_risks = (
        risk_out.get("fresh_evaluation", {}).get("critical", 0) or
        risk_out.get("critical_found", 0)
    )
    anomaly_count = sensor_out.get("anomaly_count", 0)
    unsafe_overlaps = permit_out.get("critical_overlaps", 0)
    compliance_score = compliance_out.get("compliance_score")

    severity = (
        "CRITICAL" if critical_risks > 0 or unsafe_overlaps > 0 else
        "HIGH"     if anomaly_count > 3 else
        "MODERATE" if anomaly_count > 0 else
        "LOW"
    )

    headline_parts = []
    if critical_risks:
        headline_parts.append(f"{critical_risks} critical compound risk(s) active")
    if anomaly_count:
        headline_parts.append(f"{anomaly_count} sensor anomalie(s)")
    if unsafe_overlaps:
        headline_parts.append(f"{unsafe_overlaps} unsafe permit overlap(s)")
    if compliance_score is not None:
        headline_parts.append(f"compliance score {compliance_score}%")
    headline = ". ".join(headline_parts) if headline_parts else "All systems nominal."

    return {
        "briefing_timestamp": datetime.utcnow().isoformat(),
        "task": task,
        "agents_dispatched": agents_used,
        "severity": severity,
        "headline": headline,
        "agent_results": outputs,
        "performance": {
            name: {"elapsed_ms": res.elapsed_ms, "tools_called": res.tools_called, "status": res.status}
            for name, res in results.items()
        },
    }
