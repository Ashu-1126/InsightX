"""
Compliance Agent — validates plant operations against OISD, DGMS, Factory Act standards.

Tools:
  run_audit        — full compliance audit across all standards
  score            — quick compliance score
  corrective_workflows — list only failing checks with corrective actions
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents.base_agent import BaseAgent
from services.compliance_service import run_compliance_audit, get_compliance_score


class ComplianceAgent(BaseAgent):
    name = "ComplianceAgent"
    description = (
        "Quality and Compliance auditor. Validates live plant state against OISD-116, "
        "OISD-105, DGMS, and Factory Act requirements. Generates corrective action workflows "
        "for failing checks and tracks compliance score over time."
    )

    def _register_tools(self):
        self._tools = {
            "run_audit": self._run_audit,
            "score": self._score,
            "corrective_workflows": self._corrective_workflows,
        }

    def _run_audit(self, **_) -> dict:
        """Full compliance audit across all 8 checks."""
        return run_compliance_audit()

    def _score(self, **_) -> dict:
        """Quick compliance score without full audit."""
        return get_compliance_score()

    def _corrective_workflows(self, **_) -> list[dict]:
        """Only failing checks with their corrective actions."""
        audit = run_compliance_audit()
        return audit["corrective_workflows"]

    def _execute(self, task: str, context: dict, tools_called: list[str]) -> dict:
        task_l = task.lower()

        if "corrective" in task_l or "action" in task_l or "fix" in task_l:
            tools_called.append("corrective_workflows")
            workflows = self.call_tool("corrective_workflows")
            return {"corrective_actions_required": len(workflows), "workflows": workflows}

        if "score" in task_l and "full" not in task_l:
            tools_called.append("score")
            return self.call_tool("score")

        # Default: full audit
        tools_called.append("run_audit")
        audit = self.call_tool("run_audit")
        return {
            "compliance_score": audit["compliance_score"],
            "overall_status": audit["overall_status"],
            "passed": audit["passed"],
            "failed": audit["failed"],
            "critical_failures": audit["critical_failures"],
            "corrective_actions": len(audit["corrective_workflows"]),
            "summary": audit["corrective_workflows"],
        }
