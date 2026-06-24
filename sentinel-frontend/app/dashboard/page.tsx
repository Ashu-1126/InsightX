"use client";
import { useState, useEffect, useCallback, useMemo } from "react";
import Sidebar from "@/components/layout/Sidebar";
import TopBar from "@/components/layout/TopBar";
import { risk, sensors, emergency, incidents, permits } from "@/lib/api";
import { useWebSocket } from "@/hooks/useWebSocket";
import type { RiskAssessment, ZoneRiskScore, EmergencyEvent, Incident, ZoneSummary } from "@/lib/types";
import {
  AlertTriangle, Shield, Activity, Zap, FileCheck2,
  Clock, ChevronRight, TriangleAlert,
} from "lucide-react";
import Link from "next/link";

const ZONE_LABELS: Record<string, string> = {
  zone_a: "Production Floor", zone_b: "Storage Area", zone_c: "Chemical Processing",
  zone_d: "Loading Bay", zone_e: "Control Room", zone_f: "Confined Space",
};

function SeverityBadge({ severity }: { severity: string }) {
  const map: Record<string, string> = {
    critical: "badge-critical", high: "badge-medium",
    medium: "badge-warning", low: "badge-safe", safe: "badge-safe",
  };
  return <span className={map[severity] || "badge-safe"}>{severity.toUpperCase()}</span>;
}

function RiskScoreBar({ score }: { score: number }) {
  const color = score >= 80 ? "bg-danger" : score >= 60 ? "bg-warning" : score >= 40 ? "bg-orange-400" : "bg-success";
  return (
    <div className="risk-bar w-full">
      <div className={`risk-bar-fill ${color}`} style={{ width: `${score}%` }} />
    </div>
  );
}

export default function DashboardPage() {
  const [activeRisks, setActiveRisks] = useState<RiskAssessment[]>([]);
  const [zoneScores, setZoneScores] = useState<ZoneRiskScore[]>([]);
  const [activeEmergencies, setActiveEmergencies] = useState<EmergencyEvent[]>([]);
  const [recentIncidents, setRecentIncidents] = useState<Incident[]>([]);
  const [zoneSummaries, setZoneSummaries] = useState<ZoneSummary[]>([]);
  const [activePermitCount, setActivePermitCount] = useState(0);
  const [wsConnected, setWsConnected] = useState(false);

  const load = useCallback(async () => {
    const [r, z, e, i, s, p] = await Promise.allSettled([
      risk.active(), risk.zones(), emergency.active(),
      incidents.list(), sensors.zones(), permits.summary(),
    ]);
    if (r.status === "fulfilled") setActiveRisks(r.value);
    if (z.status === "fulfilled") setZoneScores(z.value);
    if (e.status === "fulfilled") setActiveEmergencies(e.value);
    if (i.status === "fulfilled") setRecentIncidents(i.value.slice(0, 8));
    if (s.status === "fulfilled") setZoneSummaries(s.value);
    if (p.status === "fulfilled") setActivePermitCount((p.value as { total_active: number }).total_active);
  }, []);

  useEffect(() => { load(); const id = setInterval(load, 15000); return () => clearInterval(id); }, [load]);

  useWebSocket("/ws/incidents", (msg: unknown) => {
    const m = msg as { type: string };
    setWsConnected(true);
    if (m.type === "incident") load();
    if (m.type === "risk_update") load();
    if (m.type === "emergency") load();
  });

  const criticalRisks = useMemo(() => activeRisks.filter((r) => r.severity === "critical"), [activeRisks]);
  const highRisks = useMemo(() => activeRisks.filter((r) => r.severity === "high"), [activeRisks]);
  const warningSensors = useMemo(() => zoneSummaries.filter((z) => z.has_warning || z.has_critical).length, [zoneSummaries]);
  const todayIncidents = useMemo(() => {
    const today = new Date().toDateString();
    return recentIncidents.filter((i) => new Date(i.created_at).toDateString() === today).length;
  }, [recentIncidents]);

  return (
    <div className="min-h-screen bg-bg">
      <Sidebar />
      <TopBar
        title="Command Center"
        subtitle="Real-time safety intelligence overview"
        activeEmergencies={activeEmergencies}
        wsConnected={wsConnected}
      />
      <main className="ml-60 pt-14 p-6 space-y-6">

        {/* Emergency Banner */}
        {activeEmergencies.length > 0 && (
          <div className="rounded-xl border border-danger bg-danger/10 p-4 flex items-start gap-4 animate-pulse">
            <TriangleAlert className="w-6 h-6 text-danger mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <p className="font-bold text-danger text-sm">
                {activeEmergencies.length} ACTIVE EMERGENCY EVENT{activeEmergencies.length > 1 ? "S" : ""}
              </p>
              {activeEmergencies.slice(0, 2).map((ev) => (
                <p key={ev.id} className="text-xs text-danger/80 mt-0.5">
                  {ev.event_type} — {ev.zone_name}
                </p>
              ))}
            </div>
            <Link href="/risk" className="text-xs text-danger border border-danger/40 px-3 py-1.5 rounded-lg hover:bg-danger/20">
              View →
            </Link>
          </div>
        )}

        {/* Stat Cards */}
        <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
          {[
            {
              label: "Critical Risks", value: criticalRisks.length,
              icon: Zap, color: "danger", href: "/risk",
              sub: `${highRisks.length} high severity`,
            },
            {
              label: "Sensor Alerts", value: warningSensors,
              icon: Activity, color: "warning", href: "/sensors",
              sub: "zones with anomalies",
            },
            {
              label: "Active Permits", value: activePermitCount,
              icon: FileCheck2, color: "primary", href: "/permits",
              sub: "permit-to-work active",
            },
            {
              label: "Today's Incidents", value: todayIncidents,
              icon: AlertTriangle, color: "secondary", href: "/incidents",
              sub: `${recentIncidents.length} total`,
            },
          ].map(({ label, value, icon: Icon, color, href, sub }) => (
            <Link key={label} href={href} className="card-glow group hover:border-border/60 transition-all">
              <div className="flex items-start justify-between mb-3">
                <div className={`p-2 rounded-lg bg-${color}/10 border border-${color}/20`}>
                  <Icon className={`w-4 h-4 text-${color}`} />
                </div>
                <ChevronRight className="w-3.5 h-3.5 text-muted group-hover:text-text transition-colors" />
              </div>
              <p className={`text-3xl font-bold text-${color} font-mono`}>{value}</p>
              <p className="text-xs font-semibold text-text mt-1">{label}</p>
              <p className="text-xs text-muted">{sub}</p>
            </Link>
          ))}
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Zone Risk Matrix */}
          <div className="xl:col-span-2 card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="section-title">Zone Risk Matrix</h2>
              <Link href="/risk" className="text-xs text-primary hover:underline">Full analysis →</Link>
            </div>
            <div className="space-y-3">
              {(zoneScores.length > 0 ? zoneScores : Object.keys(ZONE_LABELS).map((id) => ({
                zone_id: id, risk_score: 0, severity: "safe" as const, risk_count: 0,
              }))).map((z) => (
                <div key={z.zone_id} className="flex items-center gap-3 group">
                  <div className="w-32 flex-shrink-0">
                    <p className="text-xs font-medium text-text truncate">{ZONE_LABELS[z.zone_id] || z.zone_id}</p>
                    <p className="text-[10px] text-muted font-mono">{z.zone_id}</p>
                  </div>
                  <div className="flex-1">
                    <RiskScoreBar score={z.risk_score} />
                  </div>
                  <div className="w-12 text-right font-mono text-sm font-bold text-text">{z.risk_score}</div>
                  <div className="w-20 flex-shrink-0">
                    <SeverityBadge severity={z.severity} />
                  </div>
                  <div className="w-14 text-xs text-muted text-right">
                    {z.risk_count > 0 ? `${z.risk_count} risk${z.risk_count > 1 ? "s" : ""}` : "—"}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Active Risk Cards */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="section-title">Active Risks</h2>
              <span className="text-xs text-muted">{activeRisks.length} total</span>
            </div>
            <div className="space-y-2.5 max-h-72 overflow-y-auto">
              {activeRisks.length === 0 ? (
                <div className="text-center py-8">
                  <Shield className="w-8 h-8 text-success/40 mx-auto mb-2" />
                  <p className="text-sm text-muted">No active risks detected</p>
                </div>
              ) : (
                activeRisks.slice(0, 6).map((r, i) => (
                  <div key={i} className="p-3 rounded-lg bg-surface2 border border-border/50 space-y-1.5">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-xs font-semibold text-text leading-tight">{r.risk_type}</p>
                      <SeverityBadge severity={r.severity} />
                    </div>
                    <p className="text-[10px] text-muted">{ZONE_LABELS[r.zone_id] || r.zone_id}</p>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1 text-[10px] text-muted">
                        <Clock className="w-3 h-3" />
                        ETA: {r.eta_to_incident}m
                      </div>
                      <p className="text-xs font-mono font-bold text-danger">{r.risk_score}/100</p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Recent Incidents */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title">Recent Incidents</h2>
            <Link href="/incidents" className="text-xs text-primary hover:underline">View all →</Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-muted border-b border-border">
                  {["ID", "Type", "Description", "Camera", "Status", "Time"].map((h) => (
                    <th key={h} className="text-left pb-2 pr-4 font-medium uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border/30">
                {recentIncidents.map((inc) => (
                  <tr key={inc.id} className="hover:bg-surface2 transition-colors">
                    <td className="py-2 pr-4 font-mono text-muted">#{inc.id}</td>
                    <td className="py-2 pr-4">
                      <span className="px-2 py-0.5 rounded bg-surface2 border border-border font-mono">{inc.type}</span>
                    </td>
                    <td className="py-2 pr-4 text-text max-w-xs truncate">{inc.description}</td>
                    <td className="py-2 pr-4 text-muted">{inc.camera_id ? `Cam ${inc.camera_id}` : "—"}</td>
                    <td className="py-2 pr-4">
                      <span className={`font-mono ${inc.status === "Open" ? "text-warning" : inc.status === "Closed" ? "text-success" : "text-primary"}`}>
                        {inc.status}
                      </span>
                    </td>
                    <td className="py-2 text-muted font-mono">
                      {new Date(inc.created_at).toLocaleTimeString()}
                    </td>
                  </tr>
                ))}
                {recentIncidents.length === 0 && (
                  <tr><td colSpan={6} className="py-8 text-center text-muted">No incidents recorded</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
