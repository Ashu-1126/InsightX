"use client";
import dynamic from "next/dynamic";
import { useState, useEffect, useCallback } from "react";
import Sidebar from "@/components/layout/Sidebar";
import TopBar from "@/components/layout/TopBar";
import { risk, sensors } from "@/lib/api";
import type { ZoneRiskScore, ZoneSummary } from "@/lib/types";
import { Box, Activity, AlertTriangle, Shield } from "lucide-react";

// Load Three.js canvas client-side only
const PlantCanvas = dynamic(() => import("@/components/digital-twin/PlantCanvas"), { ssr: false });

const ZONE_LABELS: Record<string, string> = {
  zone_a: "Production Floor", zone_b: "Storage Area", zone_c: "Chemical Processing",
  zone_d: "Loading Bay", zone_e: "Control Room", zone_f: "Confined Space",
};

function SeverityDot({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    critical: "bg-danger", high: "bg-orange-500", medium: "bg-warning",
    low: "bg-success", safe: "bg-success",
  };
  return <span className={`inline-block w-2 h-2 rounded-full ${colors[severity] || "bg-success"}`} />;
}

export default function DigitalTwinPage() {
  const [zoneScores, setZoneScores] = useState<ZoneRiskScore[]>([]);
  const [zoneSummaries, setZoneSummaries] = useState<ZoneSummary[]>([]);
  const [selectedZone, setSelectedZone] = useState<string | null>(null);

  const load = useCallback(async () => {
    const [z, s] = await Promise.allSettled([risk.zones(), sensors.zones()]);
    if (z.status === "fulfilled") setZoneScores(z.value);
    if (s.status === "fulfilled") setZoneSummaries(s.value);
  }, []);

  useEffect(() => { load(); const id = setInterval(load, 10000); return () => clearInterval(id); }, [load]);

  const selectedScore = zoneScores.find((z) => z.zone_id === selectedZone);
  const selectedSensors = zoneSummaries.find((z) => z.zone_id === selectedZone);

  return (
    <div className="min-h-screen bg-bg">
      <Sidebar />
      <TopBar title="3D Digital Twin" subtitle="Live plant visualization with real-time risk overlay" />
      <main className="ml-60 pt-14 h-screen flex flex-col">
        <div className="flex flex-1 overflow-hidden">
          {/* 3D Canvas — main area */}
          <div className="flex-1 relative">
            <PlantCanvas zoneScores={zoneScores} />

            {/* Legend overlay */}
            <div className="absolute bottom-6 left-6 card bg-surface/80 backdrop-blur space-y-2 text-xs">
              <p className="label">Risk Level</p>
              {[
                { color: "bg-danger", label: "Critical (80–100)" },
                { color: "bg-orange-500", label: "High (60–80)" },
                { color: "bg-warning", label: "Medium (40–60)" },
                { color: "bg-success", label: "Safe (0–40)" },
              ].map(({ color, label }) => (
                <div key={label} className="flex items-center gap-2">
                  <span className={`w-3 h-3 rounded ${color}`} />
                  <span className="text-muted">{label}</span>
                </div>
              ))}
            </div>

            {/* Camera label */}
            <div className="absolute top-4 left-4 flex items-center gap-2 text-xs text-muted font-mono bg-surface/70 px-3 py-1.5 rounded-full border border-border">
              <Box className="w-3 h-3 text-primary" />
              AUTO-ORBIT • 3D PLANT VIEW
            </div>
          </div>

          {/* Right panel */}
          <div className="w-72 bg-surface border-l border-border flex flex-col overflow-y-auto">
            <div className="p-4 border-b border-border">
              <h2 className="font-semibold text-sm text-text">Zone Status</h2>
              <p className="text-xs text-muted mt-0.5">Click a zone for details</p>
            </div>

            <div className="p-3 space-y-2 flex-1">
              {zoneScores.map((z) => (
                <button
                  key={z.zone_id}
                  onClick={() => setSelectedZone(selectedZone === z.zone_id ? null : z.zone_id)}
                  className={`w-full text-left p-3 rounded-lg border transition-all
                    ${selectedZone === z.zone_id ? "border-primary/50 bg-primary/5" : "border-border bg-surface2 hover:border-border/60"}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <SeverityDot severity={z.severity} />
                      <span className="text-xs font-medium text-text">{ZONE_LABELS[z.zone_id]}</span>
                    </div>
                    <span className="text-xs font-mono font-bold text-text">{z.risk_score}</span>
                  </div>
                  <div className="mt-1.5 risk-bar">
                    <div
                      className="risk-bar-fill"
                      style={{
                        width: `${z.risk_score}%`,
                        backgroundColor: z.severity === "critical" ? "#ef4444" : z.severity === "high" ? "#f97316" : z.severity === "medium" ? "#f59e0b" : "#10b981",
                      }}
                    />
                  </div>
                </button>
              ))}
            </div>

            {/* Zone detail panel */}
            {selectedZone && selectedScore && (
              <div className="p-4 border-t border-border bg-surface2">
                <h3 className="text-sm font-semibold text-text mb-3">{ZONE_LABELS[selectedZone]}</h3>
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-muted">Risk Score</span>
                    <span className="font-mono font-bold text-danger">{selectedScore.risk_score}/100</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-muted">Severity</span>
                    <span className="font-mono capitalize text-text">{selectedScore.severity}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-muted">Active Risks</span>
                    <span className="font-mono text-text">{selectedScore.risk_count}</span>
                  </div>
                  {selectedScore.top_risk && (
                    <div className="mt-2 p-2 rounded bg-danger/10 border border-danger/20">
                      <p className="text-[10px] text-danger font-mono">{selectedScore.top_risk}</p>
                    </div>
                  )}

                  {/* Sensors */}
                  {selectedSensors && (
                    <div className="mt-3 space-y-1.5">
                      <p className="label">Sensor Readings</p>
                      {Object.entries(selectedSensors.sensors).map(([type, s]) => (
                        <div key={type} className="flex items-center justify-between text-xs">
                          <span className="text-muted capitalize">{type}</span>
                          <span className={`font-mono ${s.is_critical ? "text-danger" : s.is_warning ? "text-warning" : "text-text"}`}>
                            {s.value.toFixed(1)} {s.unit}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
