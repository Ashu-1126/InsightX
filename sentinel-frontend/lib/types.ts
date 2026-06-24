// ── Core domain types for SENTINEL AI ────────────────────────────────────────

export interface SensorReading {
  sensor_id: string;
  zone_id: string;
  sensor_type: string;
  value: number;
  unit: string;
  timestamp: string;
  is_warning: boolean;
  is_critical: boolean;
}

export interface ZoneSummary {
  zone_id: string;
  sensors: Record<string, SensorReading>;
  has_warning: boolean;
  has_critical: boolean;
}

export interface SensorHistory {
  value: number;
  unit: string;
  timestamp: string;
  is_warning: boolean;
  is_critical: boolean;
}

export type Severity = "safe" | "low" | "medium" | "high" | "critical";

export interface RiskAssessment {
  id?: number;
  rule_id: string;
  zone_id: string;
  risk_type: string;
  risk_category: string;
  description: string;
  severity: Severity;
  risk_score: number;
  probability: number;
  eta_to_incident: number;
  contributing_factors: string[];
  recommended_actions: string[];
  active_permits: Permit[];
  sensor_snapshot: Record<string, { value: number; unit: string; is_warning: boolean; is_critical: boolean }>;
  detected_at: string;
}

export interface ZoneRiskScore {
  zone_id: string;
  risk_score: number;
  severity: Severity;
  risk_count: number;
  top_risk?: string;
}

export interface Permit {
  id?: number;
  permit_number: string;
  permit_type: string;
  permit_type_label: string;
  zone_id: string;
  worker_name: string;
  issued_by: string;
  description: string;
  hazards: string[];
  precautions: string[];
  start_time: string;
  end_time: string;
  status: "active" | "completed" | "revoked" | "pending";
  created_at: string;
}

export interface PermitOverlap {
  permit_1: Permit;
  permit_2: Permit;
  zone_id: string;
  severity: Severity;
  risk_description: string;
  recommended_action: string;
  detected_at: string;
}

export interface EmergencyEvent {
  id: number;
  zone_id: string;
  zone_name: string;
  event_type: string;
  severity: Severity;
  action_plan: string[];
  evacuation_zones: { zone_id: string; zone_name: string }[];
  responders: string[];
  status: "active" | "resolved" | "false_alarm";
  created_at: string;
}

export interface Incident {
  id: number;
  type: string;
  description: string;
  status: "Open" | "In Progress" | "Closed";
  created_at: string;
  clip_path?: string;
  source: string;
  confidence?: number;
  evidence_image?: string;
  report_path?: string;
  camera_id?: number;
  event_id?: number;
}

export interface RAGResponse {
  query: string;
  answer: string;
  sources: { id: number; title: string; document_type: string; relevance_score: number }[];
  live_context_used: boolean;
  timestamp: string;
}

export interface Pattern {
  pattern: string;
  insight: string;
  confidence: number;
  category: string;
  source?: string;
}

export interface Zone {
  id: string;
  name: string;
  description: string;
  x: number;
  y: number;
  width: number;
  height: number;
  risk_level: "safe" | "warning" | "critical";
  camera_id?: number;
}

export interface User {
  id: number;
  name: string;
  email: string;
  role: "user" | "admin";
  verified: boolean;
}

export type WSMessage =
  | { type: "incident"; data: Incident }
  | { type: "risk_update"; data: RiskAssessment[] }
  | { type: "emergency"; data: EmergencyEvent }
  | { type: "sensor_update"; readings: SensorReading[]; zones: ZoneSummary[] };
