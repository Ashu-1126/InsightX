"use client";
import { useState, useEffect, useCallback, useRef } from "react";
import Sidebar from "@/components/layout/Sidebar";
import TopBar from "@/components/layout/TopBar";
import { risk, incidents, sensors } from "@/lib/api";
import type { RiskAssessment, Incident } from "@/lib/types";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { Play, Pause, RotateCcw, Clock, AlertTriangle, Zap, Activity } from "lucide-react";

interface TimelineEvent {
  time: string;
  type: "risk" | "incident" | "sensor_spike";
  label: string;
  severity: string;
  score?: number;
  zone?: string;
}

export default function ReplayPage() {
  const [timeline, setTimeline] = useState<RiskAssessment[]>([]);
  const [incidentTimeline, setIncidentTimeline] = useState<Incident[]>([]);
  const [playing, setPlaying] = useState(false);
  const [currentT, setCurrentT] = useState(0); // 0–100 slider
  const [hours, setHours] = useState(24);
  const animRef = useRef<ReturnType<typeof setInterval>>();

  const load = useCallback(async () => {
    const [r, i] = await Promise.allSettled([risk.timeline(hours), incidents.list()]);
    if (r.status === "fulfilled") setTimeline(r.value);
    if (i.status === "fulfilled") setIncidentTimeline(i.value.slice(0, 50));
  }, [hours]);

  useEffect(() => { load(); }, [load]);

  // Build unified event stream
  const events: TimelineEvent[] = [
    ...timeline.map((r) => ({
      time: r.created_at,
      type: "risk" as const,
      label: r.risk_type,
      severity: r.severity,
      score: r.risk_score,
      zone: r.zone_id,
    })),
    ...incidentTimeline.map((i) => ({
      time: i.created_at,
      type: "incident" as const,
      label: `${i.type} incident`,
      severity: "medium",
      zone: i.camera_id ? `cam-${i.camera_id}` : undefined,
    })),
  ].sort((a, b) => a.time.localeCompare(b.time));

  // Chart data — risk score over time
  const chartData = timeline
    .slice(-60)
    .map((r) => ({
      t: new Date(r.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      score: r.risk_score,
      zone: r.zone_id,
    }));

  // Current replay position mapped to visible events
  const totalEvents = events.length;
  const visibleUpTo = Math.floor((currentT / 100) * totalEvents);
  const visibleEvents = events.slice(0, visibleUpTo);
  const currentRisk = visibleEvents.filter((e) => e.type === "risk").at(-1);

  function togglePlay() {
    if (playing) {
      clearInterval(animRef.current);
      setPlaying(false);
    } else {
      setPlaying(true);
      setCurrentT(0);
      animRef.current = setInterval(() => {
        setCurrentT((t) => {
          if (t >= 100) { clearInterval(animRef.current); setPlaying(false); return 100; }
          return t + 0.5;
        });
      }, 60);
    }
  }

  function reset() {
    clearInterval(animRef.current);
    setPlaying(false);
    setCurrentT(0);
  }

  const colorMap: Record<string, string> = { critical: "#ef4444", high: "#f97316", medium: "#f59e0b", low: "#10b981" };

  return (
    <div className="min-h-screen bg-bg">
      <Sidebar />
      <TopBar title="Incident Replay Engine" subtitle="Risk evolution timeline and replay" />
      <main className="ml-60 pt-14 p-6 space-y-6">

        {/* Controls */}
        <div className="card flex items-center gap-4">
          <button onClick={togglePlay} className="btn-primary flex items-center gap-2 flex-shrink-0">
            {playing ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            {playing ? "Pause" : "Play Replay"}
          </button>
          <button onClick={reset} className="text-muted hover:text-text transition-colors">
            <RotateCcw className="w-4 h-4" />
          </button>
          <input
            type="range" min={0} max={100} value={currentT}
            onChange={(e) => { clearInterval(animRef.current); setPlaying(false); setCurrentT(+e.target.value); }}
            className="flex-1 accent-primary"
          />
          <span className="text-xs font-mono text-muted w-12 text-right">{currentT.toFixed(0)}%</span>
          <select className="input w-28" value={hours} onChange={(e) => setHours(+e.target.value)}>
            <option value={1}>Last 1h</option>
            <option value={6}>Last 6h</option>
            <option value={24}>Last 24h</option>
            <option value={72}>Last 3d</option>
          </select>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Risk timeline chart */}
          <div className="xl:col-span-2 card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="section-title">Risk Score Evolution</h2>
              {currentRisk && (
                <span
                  className="text-xs font-mono font-bold px-2 py-1 rounded border"
                  style={{ color: colorMap[currentRisk.severity], borderColor: `${colorMap[currentRisk.severity]}40`, background: `${colorMap[currentRisk.severity]}10` }}
                >
                  Current: {currentRisk.score ?? 0}/100 — {currentRisk.severity}
                </span>
              )}
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={chartData} margin={{ top: 4, right: 4, bottom: 4, left: -20 }}>
                <defs>
                  <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="t" tick={{ fontSize: 9 }} interval="preserveStartEnd" />
                <YAxis domain={[0, 100]} tick={{ fontSize: 9 }} />
                <Tooltip contentStyle={{ background: "#0d0608", border: "1px solid #3a1620", fontSize: 11 }} />
                <ReferenceLine y={80} stroke="#ef4444" strokeDasharray="3 3" label={{ value: "CRITICAL", fontSize: 9, fill: "#ef4444" }} />
                <ReferenceLine y={60} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: "HIGH", fontSize: 9, fill: "#f59e0b" }} />
                <Area type="monotone" dataKey="score" stroke="#ef4444" fill="url(#riskGrad)" strokeWidth={2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Live event panel */}
          <div className="card">
            <h2 className="section-title mb-4">Event Timeline ({visibleUpTo}/{totalEvents})</h2>
            <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
              {visibleEvents.slice(-15).reverse().map((ev, i) => (
                <div key={i} className="flex items-start gap-2.5 text-xs">
                  <div className={`flex-shrink-0 mt-0.5 ${ev.type === "risk" ? "text-danger" : "text-warning"}`}>
                    {ev.type === "risk" ? <Zap className="w-3 h-3" /> : <AlertTriangle className="w-3 h-3" />}
                  </div>
                  <div className="flex-1">
                    <p className="text-text leading-snug">{ev.label}</p>
                    <p className="text-muted text-[10px]">
                      {ev.zone} • {new Date(ev.time).toLocaleTimeString()}
                    </p>
                  </div>
                  {ev.score && (
                    <span className="font-mono font-bold text-danger flex-shrink-0">{ev.score}</span>
                  )}
                </div>
              ))}
              {visibleEvents.length === 0 && (
                <p className="text-muted text-center py-4 text-xs">Press Play to start replay</p>
              )}
            </div>
          </div>
        </div>

        {/* Full event list */}
        <div className="card">
          <h2 className="section-title mb-4">All Timeline Events ({events.length})</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-muted border-b border-border">
                  {["Time", "Type", "Event", "Zone", "Severity", "Score"].map((h) => (
                    <th key={h} className="text-left pb-2 pr-4 font-medium uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border/30">
                {events.slice(-30).reverse().map((ev, i) => (
                  <tr
                    key={i}
                    className={`transition-colors ${i < events.length - visibleUpTo ? "opacity-30" : "opacity-100"}`}
                  >
                    <td className="py-1.5 pr-4 font-mono text-muted">
                      {new Date(ev.time).toLocaleTimeString()}
                    </td>
                    <td className="py-1.5 pr-4">
                      <span className={`text-[10px] font-mono border px-1.5 py-0.5 rounded
                        ${ev.type === "risk" ? "border-danger/30 bg-danger/10 text-danger" : "border-warning/30 bg-warning/10 text-warning"}`}>
                        {ev.type}
                      </span>
                    </td>
                    <td className="py-1.5 pr-4 text-text">{ev.label}</td>
                    <td className="py-1.5 pr-4 text-muted font-mono">{ev.zone || "—"}</td>
                    <td className="py-1.5 pr-4">
                      <span style={{ color: colorMap[ev.severity] || "#b8a0a6" }} className="font-mono capitalize">
                        {ev.severity}
                      </span>
                    </td>
                    <td className="py-1.5 font-mono font-bold text-danger">{ev.score ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
