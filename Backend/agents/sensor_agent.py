"""
Sensor Agent — monitors live IoT sensor streams and classifies anomalies.

Tools:
  get_readings     — fetch current sensor readings across all zones
  get_anomalies    — identify sensors breaching thresholds
  zone_summary     — aggregate risk level per zone from sensor data
  sensor_history   — time-series for a specific sensor
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents.base_agent import BaseAgent
from services.sensor_service import (
    get_current_readings,
    get_zone_summary,
    get_anomalous_sensors,
    get_sensor_history,
)


class SensorAgent(BaseAgent):
    name = "SensorAgent"
    description = (
        "Monitors IoT sensor streams. Classifies methane, temperature, H2S, "
        "pressure, vibration, and oxygen readings against warning/critical thresholds. "
        "Surfaces anomalies and zone-level risk signals."
    )

    def _register_tools(self):
        self._tools = {
            "get_readings": self._get_readings,
            "get_anomalies": self._get_anomalies,
            "zone_summary": self._zone_summary,
            "sensor_history": self._sensor_history,
        }

    def _get_readings(self, **_) -> list[dict]:
        """Return latest reading for every sensor."""
        return get_current_readings()

    def _get_anomalies(self, minutes: int = 5, **_) -> list[dict]:
        """Return sensors that breached a threshold in the last N minutes."""
        return get_anomalous_sensors(minutes=minutes)

    def _zone_summary(self, **_) -> list[dict]:
        """Aggregate sensor state per zone."""
        return get_zone_summary()

    def _sensor_history(self, sensor_id: str, minutes: int = 30, **_) -> list[dict]:
        """Time-series readings for one sensor."""
        return get_sensor_history(sensor_id, minutes=minutes)

    def _execute(self, task: str, context: dict, tools_called: list[str]) -> dict:
        task_l = task.lower()

        if "anomal" in task_l or "breach" in task_l or "alert" in task_l:
            tools_called.append("get_anomalies")
            anomalies = self.call_tool("get_anomalies", minutes=context.get("minutes", 5))
            tools_called.append("zone_summary")
            zones = self.call_tool("zone_summary")
            return {
                "anomalous_sensors": anomalies,
                "zone_summary": zones,
                "anomaly_count": len(anomalies),
                "critical_count": sum(1 for a in anomalies if a.get("severity") == "critical"),
            }

        if "histor" in task_l and context.get("sensor_id"):
            tools_called.append("sensor_history")
            return self.call_tool(
                "sensor_history",
                sensor_id=context["sensor_id"],
                minutes=context.get("minutes", 30),
            )

        # Default: full situational snapshot
        tools_called.extend(["get_readings", "get_anomalies", "zone_summary"])
        readings = self.call_tool("get_readings")
        anomalies = self.call_tool("get_anomalies")
        zones = self.call_tool("zone_summary")
        critical_zones = [z for z in zones if z.get("risk_level") == "critical"]
        return {
            "total_sensors": len(readings),
            "anomaly_count": len(anomalies),
            "critical_zones": critical_zones,
            "zone_summary": zones,
            "top_anomalies": anomalies[:5],
        }
