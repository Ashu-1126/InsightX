"use client";
import { useState, useEffect, useCallback } from "react";
import Sidebar from "@/components/layout/Sidebar";
import TopBar from "@/components/layout/TopBar";
import {
  BrainCircuit, Zap, Activity, FileCheck2, ShieldCheck,
  Play, Clock, ChevronDown, ChevronUp,
} from "lucide-react";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("sentinel_token");
}

async function apiFetch<T>(path: string, opts?: RequestInit): Promise<T> {
  const token = getToken();
  const res = await fetch(`${BASE}${path}`, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...((opts?.headers as Record<string, string>) ?? {}),
    },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

interface AgentInfo {
  name: string;
  description: string;
  tools: { name: string; doc: string }[];
}

interface BriefingResult {
  briefing_timestamp: string;
  task: string;
  agents_dispatched: string[];
  severity: string;
  headline: string;
  agent_results: Record<string, unknown>;
  performance: Record<string, { elapsed_ms: number; tools_called: string[]; status: string }>;
}

const AGENT_ICONS: Record<string, React.ElementType> = {
  SensorAgent: Activity,
  RiskAgent: Zap,
  PermitAgent: FileCheck2,
  ComplianceAgent: ShieldCheck,
};

const SEVERITY_STYLES: Record<string, string> = {
  CRITICAL: "text-danger border-danger/30 bg-danger/10",
  HIGH:     "text-orange-400 border-orange-400/30 bg-orange-400/10",
  MODERATE: "text-warning border-warning/30 bg-warning/10",
  LOW:      "text-success border-success/30 bg-success/10",
};

const AGENT_COLORS: Record<string, string> = {
  sensor:     "text-primary",
  risk:       "text-danger",
  permit:     "text-warning",
  compliance: "text-success",
};

const PRESET_TASKS = [
  { label: "Full Plant Briefing",         task: "full plant situational awareness briefing" },
  { label: "Sensor Anomalies",            task: "detect all sensor anomalies and breaches" },
  { label: "Compound Risk Snapshot",      task: "evaluate all compound risks across the plant" },
  { label: "Permit Overlap Check",        task: "detect unsafe permit overlaps and conflicts" },
  { label: "Compliance Score",            task: "check compliance score against all standards" },
];

function AgentCard({ info }: { info: AgentInfo }) {
  const [open, setOpen] = useState(false);
  const Icon = AGENT_ICONS[info.name] || BrainCircuit;
  const colorKey = info.name.replace("Agent", "").toLowerCase();
  return (
    <div className="card">
      <button
        className="flex items-center gap-3 w-full text-left"
        onClick={() => setOpen((o) => !o)}
      >
        <div className={`p-2 rounded-lg bg-surface2 ${AGENT_COLORS[colorKey] ?? "text-primary"}`}>
          <Icon className="w-4 h-4" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-text">{info.name}</p>
          <p className="text-xs text-muted truncate">{info.description.slice(0, 80)}…</p>
        </div>
        <span className="text-xs font-mono text-muted">{info.tools.length} tools</span>
        {open ? <ChevronUp className="w-3.5 h-3.5 text-muted" /> : <ChevronDown className="w-3.5 h-3.5 text-muted" />}
      </button>
      {open && (
        <div className="mt-3 pt-3 border-t border-border space-y-1.5">
          <p className="text-xs text-muted mb-2">{info.description}</p>
          {info.tools.map((t) => (
            <div key={t.name} className="flex items-start gap-2">
              <span className="text-[10px] font-mono px-1.5 py-0.5 bg-surface2 border border-border rounded text-primary">{t.name}</span>
              <span className="text-xs text-muted">{t.doc}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function PerformanceBar({ name, perf }: { name: string; perf: { elapsed_ms: number; tools_called: string[]; status: string } }) {
  const Icon = AGENT_ICONS[name] || BrainCircuit;
  const colorKey = name.replace("Agent", "").toLowerCase();
  const ok = perf.status === "success";
  return (
    <div className="flex items-center gap-3 p-3 rounded-xl bg-surface2 border border-border">
      <div className={`p-1.5 rounded-lg ${AGENT_COLORS[colorKey] ?? "text-primary"}`}>
        <Icon className="w-3.5 h-3.5" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-semibold text-text">{name}</p>
        <p className="text-[10px] text-muted">Tools: {perf.tools_called.join(" · ") || "none"}</p>
      </div>
      <span className={`text-[10px] font-mono ${ok ? "text-success" : "text-danger"}`}>{perf.status}</span>
      <span className="text-xs font-mono text-muted">{perf.elapsed_ms}ms</span>
    </div>
  );
}

export default function MultiAgentPage() {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [briefing, setBriefing] = useState<BriefingResult | null>(null);
  const [customTask, setCustomTask] = useState("");
  const [loading, setLoading] = useState(false);
  const [expandedResult, setExpandedResult] = useState<string | null>(null);

  const loadAgents = useCallback(async () => {
    try {
      const a = await apiFetch<AgentInfo[]>("/agents/");
      setAgents(a);
    } catch (e) { console.error(e); }
  }, []);

  useEffect(() => { loadAgents(); }, [loadAgents]);

  async function runBriefing() {
    setLoading(true);
    try {
      const b = await apiFetch<BriefingResult>("/agents/briefing");
      setBriefing(b);
    } catch (e) { console.error(e); } finally { setLoading(false); }
  }

  async function runTask(task: string) {
    setLoading(true);
    try {
      const b = await apiFetch<BriefingResult>("/agents/dispatch", {
        method: "POST",
        body: JSON.stringify({ task }),
      });
      setBriefing(b);
    } catch (e) { console.error(e); } finally { setLoading(false); }
  }

  const severityStyle = briefing ? SEVERITY_STYLES[briefing.severity] ?? SEVERITY_STYLES.LOW : "";

  return (
    <div className="min-h-screen bg-bg">
      <Sidebar />
      <TopBar title="Multi-Agent Intelligence" subtitle="Parallel specialized reasoning across all plant systems" />
      <main className="ml-60 pt-14 p-6 space-y-6">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <BrainCircuit className="w-5 h-5 text-primary" />
            <div>
              <p className="font-semibold text-text">Agent Orchestration Layer</p>
              <p className="text-xs text-muted">{agents.length} specialized agents registered</p>
            </div>
          </div>
          <button onClick={runBriefing} disabled={loading} className="btn-primary flex items-center gap-2">
            <Play className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            {loading ? "Running Agents…" : "Full Briefing"}
          </button>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Left: Agents + Preset tasks */}
          <div className="xl:col-span-1 space-y-4">
            <div className="card">
              <h2 className="section-title mb-3">Dispatch Task</h2>
              <div className="space-y-1.5 mb-3">
                {PRESET_TASKS.map((p) => (
                  <button
                    key={p.task}
                    onClick={() => runTask(p.task)}
                    disabled={loading}
                    className="w-full text-left text-xs px-3 py-2 rounded-lg bg-surface2 border border-border text-muted hover:text-text hover:border-primary/30 transition-all"
                  >
                    {p.label}
                  </button>
                ))}
              </div>
              <div className="flex gap-2">
                <input
                  className="input flex-1 text-xs"
                  placeholder="Custom task…"
                  value={customTask}
                  onChange={(e) => setCustomTask(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && customTask && runTask(customTask)}
                />
                <button
                  onClick={() => customTask && runTask(customTask)}
                  disabled={loading || !customTask}
                  className="btn-primary text-xs px-3"
                >
                  Run
                </button>
              </div>
            </div>

            {/* Agent roster */}
            <h2 className="section-title">Agent Roster</h2>
            {agents.map((a) => <AgentCard key={a.name} info={a} />)}
          </div>

          {/* Right: Briefing results */}
          <div className="xl:col-span-2 space-y-4">
            {briefing && (
              <>
                {/* Severity headline */}
                <div className={`card border ${severityStyle}`}>
                  <div className="flex items-center gap-3 mb-1">
                    <BrainCircuit className="w-4 h-4" />
                    <span className="text-xs font-mono uppercase font-bold">{briefing.severity}</span>
                    <span className="text-[10px] text-muted font-mono ml-auto">
                      {briefing.agents_dispatched.length} agents · {new Date(briefing.briefing_timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-sm font-semibold text-text">{briefing.headline}</p>
                  <p className="text-[10px] text-muted mt-1 font-mono">Task: {briefing.task}</p>
                </div>

                {/* Agent performance */}
                <div className="card">
                  <h3 className="section-title mb-3">Agent Performance</h3>
                  <div className="space-y-2">
                    {Object.entries(briefing.performance).map(([name, perf]) => (
                      <PerformanceBar key={name} name={name} perf={perf} />
                    ))}
                  </div>
                </div>

                {/* Per-agent outputs */}
                <div className="card">
                  <h3 className="section-title mb-3">Agent Outputs</h3>
                  <div className="space-y-3">
                    {Object.entries(briefing.agent_results).map(([name, result]) => {
                      const isOpen = expandedResult === name;
                      const Icon = AGENT_ICONS[name] || BrainCircuit;
                      const colorKey = name.replace("Agent", "").toLowerCase();
                      return (
                        <div key={name} className="border border-border rounded-xl overflow-hidden">
                          <button
                            className="flex items-center gap-3 w-full px-4 py-3 bg-surface2 text-left"
                            onClick={() => setExpandedResult(isOpen ? null : name)}
                          >
                            <Icon className={`w-4 h-4 ${AGENT_COLORS[colorKey] ?? "text-primary"}`} />
                            <span className="text-sm font-semibold text-text capitalize">{name}</span>
                            <span className="ml-auto text-[10px] text-muted font-mono">
                              {briefing.performance[name]?.elapsed_ms}ms
                            </span>
                            {isOpen ? <ChevronUp className="w-3 h-3 text-muted" /> : <ChevronDown className="w-3 h-3 text-muted" />}
                          </button>
                          {isOpen && (
                            <pre className="px-4 py-3 text-[11px] text-muted font-mono overflow-auto max-h-72 bg-bg leading-relaxed">
                              {JSON.stringify(result, null, 2)}
                            </pre>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </>
            )}

            {!briefing && !loading && (
              <div className="card text-center py-16 border-dashed">
                <BrainCircuit className="w-8 h-8 text-muted mx-auto mb-3" />
                <p className="text-sm text-muted">Run Full Briefing or dispatch a task to activate agents</p>
              </div>
            )}

            {loading && (
              <div className="card text-center py-16">
                <BrainCircuit className="w-8 h-8 text-primary animate-pulse mx-auto mb-3" />
                <p className="text-sm text-muted">Agents reasoning in parallel…</p>
                <div className="flex justify-center gap-2 mt-3">
                  {["SensorAgent", "RiskAgent", "PermitAgent", "ComplianceAgent"].map((a) => (
                    <span key={a} className="text-[10px] font-mono text-muted px-2 py-0.5 rounded bg-surface2 border border-border animate-pulse">
                      {a}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
