import json
import os
from datetime import datetime


REPORTS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../Database/incident_reports")
)
os.makedirs(REPORTS_DIR, exist_ok=True)


def generate_incident_report(incident: dict) -> str:
    incident_id = incident.get("id", "unknown")
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"incident_{incident_id}_{timestamp}.json"
    path = os.path.join(REPORTS_DIR, filename)

    report_payload = {
        "report_generated_at": datetime.utcnow().isoformat() + "Z",
        "incident": incident,
        "summary": {
            "id": incident.get("id"),
            "type": incident.get("type"),
            "status": incident.get("status"),
            "created_at": incident.get("created_at"),
            "source": incident.get("source"),
        },
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(report_payload, f, indent=2)

    return filename
