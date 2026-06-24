"""
Permit Agent — intelligent Permit-to-Work system analysis.

Tools:
  active_permits   — list all active PTW permits
  overlaps         — detect unsafe permit combinations
  zone_permits     — permits for a specific zone
  summary          — high-level PTW system status
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents.base_agent import BaseAgent
from services.permit_service import (
    list_permits,
    detect_overlaps,
    get_active_permits_summary,
)
import sqlite3
from database import DB_PATH


class PermitAgent(BaseAgent):
    name = "PermitAgent"
    description = (
        "Permit-to-Work intelligence. Tracks active permits, detects unsafe co-location "
        "of permit types (e.g., hot work + gas-release zone), and validates permit conditions. "
        "Issues warnings for dangerous permit overlap combinations."
    )

    def _register_tools(self):
        self._tools = {
            "active_permits": self._active_permits,
            "overlaps": self._overlaps,
            "zone_permits": self._zone_permits,
            "summary": self._summary,
        }

    def _active_permits(self, **_) -> list[dict]:
        """All currently active PTW permits."""
        return list_permits(status="active")

    def _overlaps(self, **_) -> list[dict]:
        """Detect dangerous permit type combinations in the same zone."""
        return detect_overlaps()

    def _zone_permits(self, zone_id: str, **_) -> list[dict]:
        """All active permits for a specific zone."""
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT * FROM permits WHERE zone_id=? AND status='active' ORDER BY created_at DESC",
                (zone_id,),
            )
            cols = [d[0] for d in c.description]
            return [dict(zip(cols, row)) for row in c.fetchall()]

    def _summary(self, **_) -> dict:
        """High-level PTW system status."""
        return get_active_permits_summary()

    def _execute(self, task: str, context: dict, tools_called: list[str]) -> dict:
        task_l = task.lower()

        if "overlap" in task_l or "conflict" in task_l or "unsafe" in task_l:
            tools_called.append("overlaps")
            overlaps = self.call_tool("overlaps")
            critical = [o for o in overlaps if o.get("severity") == "critical"]
            return {
                "total_unsafe_overlaps": len(overlaps),
                "critical_overlaps": len(critical),
                "overlaps": overlaps,
            }

        if "zone" in task_l and context.get("zone_id"):
            tools_called.append("zone_permits")
            permits = self.call_tool("zone_permits", zone_id=context["zone_id"])
            return {"zone_id": context["zone_id"], "active_permits": len(permits), "permits": permits}

        # Default: full PTW snapshot
        tools_called.extend(["summary", "overlaps"])
        summary = self.call_tool("summary")
        overlaps = self.call_tool("overlaps")
        return {
            "summary": summary,
            "unsafe_overlaps": len(overlaps),
            "critical_overlaps": len([o for o in overlaps if o.get("severity") == "critical"]),
            "overlaps": overlaps,
        }
