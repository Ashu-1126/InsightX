"use client";
import { useState, useEffect, useCallback } from "react";
import Sidebar from "@/components/layout/Sidebar";
import TopBar from "@/components/layout/TopBar";
import { risk, emergency } from "@/lib/api";
import type { RiskAssessment, ZoneRiskScore, EmergencyEvent } from "@/lib/types";
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip } from "recharts";
import { Zap, Clock, Shield, AlertTriangle, ChevronDown, ChevronUp } from "lucide-react";

const ZONE_LABELS: Record<string, string> = {
  zone_a: "Production Floor", zone_b: "Storage Area", zone_c: "Chemical Processing",
  zone_d: "Loading Bay", zone_e: "Control Room", zone_f: "Confined Space",
};

function SeverityColor(severity: string): string {
  return { critical: "#ef4444", high: "#f97316", medium: "#f59e0b", low: "#10b981", safe: "#10b981" }[severity] || "#10b981";
}

function RiskCard({ r, expanded, onToggle }: { r: RiskAssessment; expanded: boolean; onToggle: () => void }) {
  const color = SeverityColor(r.severity);
  return (
    <div
      className="rounded-xl border overflow-hidden transition-all"
      style={{ borderColor: `${color}40`, background: `${color}08` }}
    >
      <button className="w-full p-4 text-left flex items-start gap-3" onClick={onToggle}>
        <div className="flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-bold text-text">{r.risk_type}</span>
            <span
              className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border"
              style={{ color, borderColor: `${color}50`, background: `${color}15` }}
            >
              {r.severity.toUpperCase()}
            </span>
            <span className="text-[10px] text-muted">/ {r.risk_category}</span>
          </div>
          <p className="text-xs text-muted mt-1">{ZONE_LABELS[r.zone_id]} • {r.zone_id}</p>
        </div>

        <div className="flex items-center gap-4 flex-shrink-0">
          <div className="text-right">
            <p className="text-2xl font-bold font-mono" style={{ color }}>{r.risk_score}</p>
            <p className="text-[10px] text-muted">RISK SCORE</p>
          </div>
          <div className="text-right">
            <p className="text-sm font-bold text-warning font-mono">{r.eta_to_incident}m</p>
            <p className="text-[10px] text-muted">ETA</p>
          </div>
          <div className="text-right">
            <p className="text-sm font-bold text-text font-mono">{Math.round(r.probability * 100)}%</p>
            <p className="text-[10px] text-muted">PROB.</p>
          </div>
          {expanded ? <ChevronUp className="w-4 h-4 text-muted" /> : <ChevronDown className="w-4 h-4 text-muted" />}
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 border-t border-border/30 pt-3 space-y-4">
          <p className="text-xs text-muted">{r.description}</p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Contributing Factors */}
            <div>
              <p className="label mb-2">Contributing Factors</p>
              <ul className="space-y-1">
                {r.contributing_factors.slice(0, 6).map((f, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-muted">
                    <span className="text-danger mt-0.5">•</span>{f}
                  </li>
                ))}
              </ul>
            </div>

            {/* Recommended Actions */}
            <div>
              <p className="label mb-2">Recommended Actions</p>
              <ul className="space-y-1">
                {r.recommended_actions.map((a, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs">
                    <span className="font-bold text-primary font-mono">{i + 1}.</span>
                    <span className="text-text">{a}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Sensor Snapshot */}
          {r.sensor_snapshot && (
            <div>
              <p className="label mb-2">Sensor Snapshot</p>
              <div className="flex flex-wrap gap-2">
                {Object.entries(r.sensor_snapshot).map(([type, s]) => (
                  <span
                    key={type}
                    className={`text-xs font-mono px-2 py-1 rounded border
                      ${s.is_critical ? "border-danger/40 bg-danger/10 text-danger"
                        : s.is_warning ? "border-warning/40 bg-warning/10 text-warning"
                        : "border-border bg-surface2 text-muted"}`}
                  >
                    {type}: {s.value} {s.unit}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Active Permits */}
          {r.active_permits?.length > 0 && (
            <div>
              <p className="label mb-2">Active Permits in Zone</p>
              <div className="flex flex-wrap gap-2">
                {r.active_permits.map((p, i) => (
                  <span key={i} className="text-xs px-2 py-1 rounded border border-primary/30 bg-primary/10 text-primary">
                    {p.permit_type} #{p.permit_number}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Emergency trigger */}
          <button
            onClick={async () => {
              await emergency.trigger({
                zone_id: r.zone_id, risk_type: r.risk_type,
                risk_category: r.risk_category, severity: r.severity,
                risk_score: r.risk_score, description: r.description,
                recommended_actions: r.recommended_actions,
              });
              alert("Emergency response triggered!");
            }}
            className="btn-danger text-xs"
          >
            🚨 Trigger Emergency Response
          </button>
        </div>
      )}
    </div>
  );
}

export default function RiskPage() {
  const [activeRisks, setActiveRisks] = useState<RiskAssessment[]>([]);
  const [zoneScores, setZoneScores] = useState<ZoneRiskScore[]>([]);
  const [activeEmergencies, setActiveEmergencies] = useState<EmergencyEvent[]>([]);
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});

  const load = useCallback(async () => {
    const [r, z, e] = await Promise.allSettled([risk.active(), risk.zones(), emergency.active()]);
    if (r.status === "fulfilled") setActiveRisks(r.value);
    if (z.status === "fulfilled") setZoneScores(z.value);
    if (e.status === "fulfilled") setActiveEmergencies(e.value);
  }, []);

  useEffect(() => { load(); const id = setInterval(load, 15000); return () => clearInterval(id); }, [load]);

  const radarData = zoneScores.map((z) => ({
    zone: ZONE_LABELS[z.zone_id]?.split(" ")[0] || z.zone_id,
    score: z.risk_score,
  }));

  return (
    <div className="min-h-screen bg-bg">
      <Sidebar />
      <TopBar title="Compound Risk Engine" subtitle="Multi-source risk correlation & assessment" activeEmergencies={activeEmergencies} />
      <main className="ml-60 pt-14 p-6 space-y-6">

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Active risks list */}
          <div className="xl:col-span-2 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="section-title">Active Compound Risks</h2>
              <div className="flex gap-2">
                <span className="badge-critical">{activeRisks.filter(r => r.severity === "critical").length} Critical</span>
                <span className="badge-warning">{activeRisks.filter(r => r.severity === "high").length} High</span>
              </div>
            </div>

            {activeRisks.length === 0 ? (
              <div className="card text-center py-16">
                <Shield className="w-12 h-12 text-success/30 mx-auto mb-3" />
                <p className="font-semibold text-text">All clear — no compound risks detected</p>
                <p className="text-sm text-muted mt-1">The system is actively monitoring all zones</p>
              </div>
            ) : (
              activeRisks.map((r, i) => (
                <RiskCard
                  key={i}
                  r={r}
                  expanded={!!expanded[i]}
                  onToggle={() => setExpanded((prev) => ({ ...prev, [i]: !prev[i] }))}
                />
              ))
            )}
          </div>

          {/* Radar + Zone scores */}
          <div className="space-y-4">
            <div className="card">
              <h2 className="section-title mb-4">Zone Risk Radar</h2>
              <ResponsiveContainer width="100%" height={220}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#3a1620" />
                  <PolarAngleAxis dataKey="zone" tick={{ fontSize: 10, fill: "#b8a0a6" }} />
                  <Radar name="Risk" dataKey="score" stroke="#ef4444" fill="#ef4444" fillOpacity={0.15} />
                  <Tooltip contentStyle={{ background: "#0d0608", border: "1px solid #3a1620", fontSize: 11 }} />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            <div className="card space-y-3">
              <h2 className="section-title">Zone Scores</h2>
              {zoneScores.map((z) => (
                <div key={z.zone_id} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted">{ZONE_LABELS[z.zone_id]}</span>
                    <span className="font-mono font-bold" style={{ color: SeverityColor(z.severity) }}>
                      {z.risk_score}
                    </span>
                  </div>
                  <div className="risk-bar">
                    <div
                      className="risk-bar-fill"
                      style={{ width: `${z.risk_score}%`, backgroundColor: SeverityColor(z.severity) }}
                    />
                  </div>
                </div>
              ))}
            </div>

            {/* Force evaluate button */}
            <button
              onClick={() => risk.evaluate().then(load)}
              className="btn-primary w-full"
            >
              <Zap className="w-3.5 h-3.5 inline mr-1.5" />
              Force Risk Evaluation
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
