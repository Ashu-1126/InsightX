// API client for SENTINEL AI backend
import type {
  SensorReading, ZoneSummary, SensorHistory,
  RiskAssessment, ZoneRiskScore,
  Permit, PermitOverlap,
  EmergencyEvent, Incident, RAGResponse, Pattern, Zone,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("sentinel_token");
}

async function apiFetch<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const token = getToken();
  const res = await fetch(`${BASE}${path}`, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(opts.headers || {}),
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// ── Auth ──────────────────────────────────────────────────────────────────────
export async function login(email: string, password: string) {
  const form = new URLSearchParams({ username: email, password });
  const res = await fetch(`${BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form.toString(),
  });
  if (!res.ok) throw new Error("Invalid credentials");
  const data = await res.json();
  localStorage.setItem("sentinel_token", data.access_token);
  localStorage.setItem("sentinel_user", JSON.stringify(data.user));
  return data;
}

export function logout() {
  localStorage.removeItem("sentinel_token");
  localStorage.removeItem("sentinel_user");
}

export function getCurrentUser() {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("sentinel_user");
  return raw ? JSON.parse(raw) : null;
}

// ── Sensors ───────────────────────────────────────────────────────────────────
export const sensors = {
  current: ()                                   => apiFetch<SensorReading[]>("/sensors/current"),
  zones: ()                                     => apiFetch<ZoneSummary[]>("/sensors/zones"),
  anomalies: (minutes = 5)                      => apiFetch<SensorReading[]>(`/sensors/anomalies?minutes=${minutes}`),
  history: (sensorId: string, minutes = 30)     => apiFetch<SensorHistory[]>(`/sensors/history/${sensorId}?minutes=${minutes}`),
  zoneHistory: (zoneId: string, type: string, minutes = 60) =>
    apiFetch<SensorHistory[]>(`/sensors/history/${zoneId}/${type}?minutes=${minutes}`),
  thresholds: ()                                => apiFetch<unknown[]>("/sensors/thresholds"),
};

// ── Risk Engine ───────────────────────────────────────────────────────────────
export const risk = {
  active: ()                    => apiFetch<RiskAssessment[]>("/risk/active"),
  zones: ()                     => apiFetch<ZoneRiskScore[]>("/risk/zones"),
  zone: (zoneId: string)        => apiFetch<ZoneRiskScore>(`/risk/zone/${zoneId}`),
  timeline: (hours = 24)        => apiFetch<RiskAssessment[]>(`/risk/timeline?hours=${hours}`),
  evaluate: (zoneId?: string)   => apiFetch<RiskAssessment[]>("/risk/evaluate", {
    method: "POST",
    body: JSON.stringify(zoneId ? { zone_id: zoneId } : {}),
  }),
  rules: ()                     => apiFetch<unknown[]>("/risk/rules"),
};

// ── Permits ───────────────────────────────────────────────────────────────────
export const permits = {
  list: (status?: string, zoneId?: string) => {
    const params = new URLSearchParams();
    if (status) params.set("status", status);
    if (zoneId) params.set("zone_id", zoneId);
    return apiFetch<Permit[]>(`/permits/?${params}`);
  },
  create: (body: {
    permit_type: string; zone_id: string; worker_name: string;
    description: string; duration_hours?: number; issued_by?: string;
    hazards?: string[]; precautions?: string[];
  }) => apiFetch<{ permit: Permit; overlap_warnings: PermitOverlap[] }>("/permits/", {
    method: "POST",
    body: JSON.stringify(body),
  }),
  get: (id: number)            => apiFetch<Permit>(`/permits/${id}`),
  updateStatus: (id: number, status: string) => apiFetch<Permit>(`/permits/${id}/status?status=${status}`, { method: "PATCH" }),
  overlaps: (zoneId?: string)  => apiFetch<PermitOverlap[]>(`/permits/overlaps${zoneId ? `?zone_id=${zoneId}` : ""}`),
  summary: ()                  => apiFetch<{ total_active: number; permits: Permit[]; unsafe_overlaps: PermitOverlap[]; overlap_count: number; has_critical_overlap: boolean }>("/permits/summary"),
  types: ()                    => apiFetch<{ type: string; label: string }[]>("/permits/types"),
};

// ── Emergency ─────────────────────────────────────────────────────────────────
export const emergency = {
  active: ()                    => apiFetch<EmergencyEvent[]>("/emergency/active"),
  trigger: (body: unknown)      => apiFetch<EmergencyEvent>("/emergency/trigger", { method: "POST", body: JSON.stringify(body) }),
  resolve: (id: number)         => apiFetch<unknown>(`/emergency/${id}/resolve`, { method: "PATCH" }),
  plan: (zoneId: string)        => apiFetch<unknown>(`/emergency/plan/${zoneId}`),
};

// ── Intelligence (RAG) ────────────────────────────────────────────────────────
export const intelligence = {
  query: (query: string, includeLiveContext = true) =>
    apiFetch<RAGResponse>("/intelligence/query", {
      method: "POST",
      body: JSON.stringify({ query, include_live_context: includeLiveContext }),
    }),
  patterns: ()                  => apiFetch<Pattern[]>("/intelligence/patterns"),
  search: (q: string, topK = 5) => apiFetch<unknown[]>(`/intelligence/search?q=${encodeURIComponent(q)}&top_k=${topK}`),
  context: ()                   => apiFetch<unknown>("/intelligence/context"),
};

// ── Incidents ─────────────────────────────────────────────────────────────────
export const incidents = {
  list: (params: { status?: string; type?: string } = {}) => {
    const p = new URLSearchParams();
    if (params.status) p.set("status", params.status);
    if (params.type) p.set("type", params.type);
    return apiFetch<Incident[]>(`/incidents/?${p}`);
  },
  events: ()                    => apiFetch<unknown[]>("/incidents/events"),
  updateStatus: (id: number, status: string) =>
    apiFetch<unknown>(`/incidents/${id}/status?status=${status}`, { method: "PATCH" }),
  feedback: (id: number, comment: string) =>
    apiFetch<unknown>(`/incidents/${id}/feedback`, { method: "POST", body: JSON.stringify(comment) }),
};

// ── Compliance — MODULE 7 ─────────────────────────────────────────────────────
export const compliance = {
  audit:     ()  => apiFetch<unknown>("/compliance/audit"),
  score:     ()  => apiFetch<{ compliance_score: number; overall_status: string; passed: number; failed: number; critical_failures: number }>("/compliance/score"),
  standards: ()  => apiFetch<unknown>("/compliance/standards"),
  checks:    ()  => apiFetch<unknown>("/compliance/checks"),
};

// ── Multi-Agent — FEATURE A ──────────────────────────────────────────────────
export const agents = {
  list:      ()                                    => apiFetch<unknown>("/agents/"),
  briefing:  ()                                    => apiFetch<unknown>("/agents/briefing"),
  dispatch:  (task: string, ctx?: unknown, agentNames?: string[]) =>
    apiFetch<unknown>("/agents/dispatch", {
      method: "POST",
      body: JSON.stringify({ task, context: ctx, agents: agentNames }),
    }),
};

// ── Settings ──────────────────────────────────────────────────────────────────
export const settings = {
  getSensitivity: ()            => apiFetch<{ sensitivity: number }>("/settings/sensitivity"),
  setSensitivity: (v: number)   => apiFetch<unknown>("/settings/sensitivity", { method: "POST", body: JSON.stringify({ sensitivity: v }) }),
};

// ── WebSocket helper ──────────────────────────────────────────────────────────
export function createWS(path: string, onMessage: (data: unknown) => void): WebSocket {
  const wsBase = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
  const token = getToken();
  const url = `${wsBase}${path}${token ? `?token=${token}` : ""}`;
  const ws = new WebSocket(url);
  ws.onmessage = (e) => {
    try { onMessage(JSON.parse(e.data)); } catch { /* noop */ }
  };
  return ws;
}
