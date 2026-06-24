"""
Base Agent — SENTINEL AI Multi-Agent Architecture

Defines the contract all specialized agents must follow:
- Each agent has a name, description, and a set of callable tools
- Tools are plain functions registered in the agent's tool registry
- Agents expose .run(task) → AgentResult for orchestrated execution
- The master orchestrator wires agents together for compound reasoning
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class AgentResult:
    agent_name: str
    task: str
    status: str           # "success" | "partial" | "error"
    output: Any
    tools_called: list[str] = field(default_factory=list)
    elapsed_ms: float = 0.0
    error: str | None = None


class BaseAgent:
    """Abstract base for all SENTINEL AI agents."""

    name: str = "BaseAgent"
    description: str = ""

    def __init__(self):
        self._tools: dict[str, Callable] = {}
        self._register_tools()

    def _register_tools(self):
        """Subclasses populate self._tools here."""

    def call_tool(self, tool_name: str, **kwargs) -> Any:
        tool = self._tools.get(tool_name)
        if not tool:
            raise ValueError(f"Unknown tool '{tool_name}' in agent '{self.name}'")
        return tool(**kwargs)

    def list_tools(self) -> list[dict]:
        return [
            {"name": k, "doc": (v.__doc__ or "").strip().split("\n")[0]}
            for k, v in self._tools.items()
        ]

    def run(self, task: str, context: dict | None = None) -> AgentResult:
        """Execute a task. Subclasses override _execute."""
        t0 = time.monotonic()
        tools_called: list[str] = []
        try:
            output = self._execute(task, context or {}, tools_called)
            status = "success"
            error = None
        except Exception as exc:
            output = None
            status = "error"
            error = str(exc)

        elapsed = (time.monotonic() - t0) * 1000
        return AgentResult(
            agent_name=self.name,
            task=task,
            status=status,
            output=output,
            tools_called=tools_called,
            elapsed_ms=round(elapsed, 1),
            error=error,
        )

    def _execute(self, task: str, context: dict, tools_called: list[str]) -> Any:
        raise NotImplementedError
