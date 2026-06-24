"""
Risk Agent — compound risk evaluation across CV + sensors + permits + shift data.

Tools:
  active_risks     — get all currently active compound risk assessments
  zone_risk        — get compound risk score for a specific zone
  risk_timeline    — historical risk evolution (last N hours)
  force_evaluate   — trigger fresh risk evaluation immediately
  risk_rules       — describe all active compound risk rules
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents.base_agent import BaseAgent
from services.risk_engine import (
    get_active_risks,
    get_zone_risk_score,
    get_risk_timeline,
    evaluate_now,
    RISK_RULES,
)


class RiskAgent(BaseAgent):
    name = "RiskAgent"
    description = (
        "Compound risk reasoning engine. Correlates CCTV detections, sensor anomalies, "
        "active permits, and shift change data to identify multi-source hazards. "
        "Each risk assessment includes a score (0-100), ETA to incident, and recommended actions."
    )

    def _register_tools(self):
        self._tools = {
            "active_risks": self._active_risks,
            "zone_risk": self._zone_risk,
            "risk_timeline": self._risk_timeline,
            "force_evaluate": self._force_evaluate,
            "risk_rules": self._risk_rules,
        }

    def _active_risks(self, **_) -> list[dict]:
        """Return all currently active compound risk assessments."""
        return get_active_risks()

    def _zone_risk(self, zone_id: str, **_) -> dict:
        """Compound risk score for a specific zone."""
        return get_zone_risk_score(zone_id)

    def _risk_timeline(self, hours: int = 24, **_) -> list[dict]:
        """Historical risk score evolution."""
        return get_risk_timeline(hours=hours)

    def _force_evaluate(self, zone_id: str | None = None, **_) -> list[dict]:
        """Force immediate risk evaluation (for demo or on-demand)."""
        return evaluate_now(zone_id=zone_id)

    def _risk_rules(self, **_) -> list[dict]:
        """Describe all 10 compound risk rules."""
        return [
            {
                "id": r["id"],
                "base_score": r["base_score"],
                "probability": r["probability"],
                "eta_minutes": r["eta_minutes"],
                "conditions": r["conditions"],
            }
            for r in RISK_RULES
        ]

    def _execute(self, task: str, context: dict, tools_called: list[str]) -> dict:
        task_l = task.lower()

        if "evaluat" in task_l or "force" in task_l:
            tools_called.append("force_evaluate")
            zone_id = context.get("zone_id")
            risks = self.call_tool("force_evaluate", zone_id=zone_id)
            critical = [r for r in risks if r.get("severity") == "critical"]
            return {"evaluated": len(risks), "critical_found": len(critical), "risks": risks}

        if "timeline" in task_l or "histor" in task_l:
            tools_called.append("risk_timeline")
            return {"timeline": self.call_tool("risk_timeline", hours=context.get("hours", 24))}

        if "zone" in task_l and context.get("zone_id"):
            tools_called.append("zone_risk")
            return self.call_tool("zone_risk", zone_id=context["zone_id"])

        if "rules" in task_l:
            tools_called.append("risk_rules")
            return {"rules": self.call_tool("risk_rules")}

        # Default: situational risk snapshot
        tools_called.extend(["active_risks", "force_evaluate"])
        active = self.call_tool("active_risks")
        fresh = self.call_tool("force_evaluate")

        critical = [r for r in fresh if r.get("severity") == "critical"]
        high = [r for r in fresh if r.get("severity") == "high"]

        return {
            "active_stored_risks": len(active),
            "fresh_evaluation": {
                "total": len(fresh),
                "critical": len(critical),
                "high": len(high),
            },
            "highest_risk": max(fresh, key=lambda r: r.get("score", 0), default=None),
            "critical_risks": critical,
        }
