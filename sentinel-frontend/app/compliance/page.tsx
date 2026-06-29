"use client";
import { useState, useEffect, useCallback } from "react";
import Sidebar from "@/components/layout/Sidebar";
import TopBar from "@/components/layout/TopBar";
import { CheckCircle, XCircle, AlertTriangle, RefreshCw, ShieldCheck, BookOpen } from "lucide-react";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("sentinel_token");
}

async function apiFetch<T>(path: string): Promise<T> {
  const token = getToken();
  const res = await fetch(`${BASE}${path}`, {
    headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

interface CheckResult {
  id: string;
  standard: string;
  category: string;
  requirement: string;
  severity: string;
  status: "PASS" | "FAIL";
  value: string;
  detail: string;
  corrective_action?: string;
}

interface AuditReport {
  audit_timestamp: string;
  overall_status: string;
  compliance_score: number;
  total_checks: number;
  passed: number;
  failed: number;
  critical_failures: number;
  results: CheckResult[];
  standards_covered: string[];
  corrective_workflows: { check_id: string; priority: string; action: string }[];
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: "text-danger", high: "text-orange-400", medium: "text-warning", low: "text-success",
};

const STATUS_ICONS = {
  PASS: <CheckCircle className="w-4 h-4 text-success" />,
  FAIL: <XCircle className="w-4 h-4 text-danger" />,
};

function ScoreRing({ score }: { score: number }) {
  const color = score >= 90 ? "#10b981" : score >= 70 ? "#f59e0b" : "#ef4444";
  const r = 52;
  const circ = 2 * Math.PI * r;
  const dash = (score / 100) * circ;
  return (
    <div className="relative inline-flex items-center justify-center w-36 h-36">
      <svg className="w-36 h-36 -rotate-90" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r={r} stroke="#3a1620" strokeWidth="10" fill="none" />
        <circle
          cx="60" cy="60" r={r} stroke={color} strokeWidth="10" fill="none"
          strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
          style={{ transition: "stroke-dasharray 0.8s ease" }}
        />
      </svg>
      <div className="absolute text-center">
        <p className="text-3xl font-bold font-mono" style={{ color }}>{score}</p>
        <p className="text-[10px] text-muted uppercase tracking-wider">Score</p>
      </div>
    </div>
  );
}

export default function CompliancePage() {
  const [report, setReport] = useState<AuditReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [lastRun, setLastRun] = useState<string | null>(null);
  const [filterCategory, setFilterCategory] = useState<string>("");

  const runAudit = useCallback(async () => {
    setLoading(true);
    try {
      const r = await apiFetch<AuditReport>("/compliance/audit");
      setReport(r);
      setLastRun(new Date().toLocaleTimeString());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { runAudit(); }, [runAudit]);

  const categories = report ? [...new Set(report.results.map((r) => r.category))] : [];
  const filtered = report?.results.filter((r) => !filterCategory || r.category === filterCategory) ?? [];

  const overallColor =
    report?.overall_status === "COMPLIANT" ? "text-success" :
    report?.overall_status === "MINOR_VIOLATIONS" ? "text-warning" : "text-danger";

  return (
    <div className="min-h-screen bg-bg">
      <Sidebar />
      <TopBar title="Compliance Audit" subtitle="OISD · DGMS · Factory Act validation" />
      <main className="ml-60 pt-14 p-6 space-y-6">

        {/* Header row */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <ShieldCheck className="w-5 h-5 text-primary" />
            <div>
              <p className="font-semibold text-text">Real-time Compliance Audit</p>
              {lastRun && <p className="text-xs text-muted">Last run: {lastRun}</p>}
            </div>
          </div>
          <button
            onClick={runAudit}
            disabled={loading}
            className="btn-primary flex items-center gap-2"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            {loading ? "Running…" : "Run Audit"}
          </button>
        </div>

        {report && (
          <>
            {/* Score cards */}
            <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
              {/* Score ring */}
              <div className="card flex flex-col items-center justify-center py-4">
                <ScoreRing score={report.compliance_score} />
                <p className={`text-sm font-bold mt-2 ${overallColor}`}>
                  {report.overall_status.replace(/_/g, " ")}
                </p>
                <p className="text-xs text-muted mt-0.5 font-mono">
                  {new Date(report.audit_timestamp).toLocaleString()}
                </p>
              </div>

              {/* Stats */}
              <div className="card flex flex-col justify-center">
                <p className="text-3xl font-bold font-mono text-success">{report.passed}</p>
                <p className="text-xs text-muted mt-1">Checks Passed</p>
                <div className="risk-bar mt-3">
                  <div className="risk-bar-fill bg-success" style={{ width: `${(report.passed / report.total_checks) * 100}%` }} />
                </div>
              </div>

              <div className="card flex flex-col justify-center">
                <p className="text-3xl font-bold font-mono text-danger">{report.failed}</p>
                <p className="text-xs text-muted mt-1">Checks Failed</p>
                <div className="risk-bar mt-3">
                  <div className="risk-bar-fill bg-danger" style={{ width: `${(report.failed / report.total_checks) * 100}%` }} />
                </div>
              </div>

              <div className="card flex flex-col justify-center">
                <p className="text-3xl font-bold font-mono text-danger">{report.critical_failures}</p>
                <p className="text-xs text-muted mt-1">Critical Failures</p>
                <p className="text-xs text-muted mt-1">Standards: {report.standards_covered.length} covered</p>
              </div>
            </div>

            {/* Corrective Workflows */}
            {report.corrective_workflows.length > 0 && (
              <div className="card border-warning/30 bg-warning/5">
                <h2 className="section-title text-warning mb-3">
                  ⚠️ Corrective Action Workflows ({report.corrective_workflows.length})
                </h2>
                <div className="space-y-3">
                  {report.corrective_workflows.map((w, i) => (
                    <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-surface2 border border-border">
                      <AlertTriangle className={`w-4 h-4 mt-0.5 flex-shrink-0 ${SEVERITY_COLORS[w.priority]}`} />
                      <div>
                        <p className="text-xs font-mono text-muted mb-0.5">{w.check_id}</p>
                        <p className="text-sm text-text">{w.action}</p>
                      </div>
                      <span className={`ml-auto text-[10px] font-mono uppercase flex-shrink-0 ${SEVERITY_COLORS[w.priority]}`}>
                        {w.priority}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Check results */}
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="section-title">Compliance Checks ({report.total_checks})</h2>
                <select
                  className="input w-48"
                  value={filterCategory}
                  onChange={(e) => setFilterCategory(e.target.value)}
                >
                  <option value="">All Categories</option>
                  {categories.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>

              <div className="space-y-3">
                {filtered.map((result) => (
                  <div
                    key={result.id}
                    className={`p-4 rounded-xl border transition-all
                      ${result.status === "FAIL"
                        ? "border-danger/30 bg-danger/5"
                        : "border-border bg-surface2"
                      }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="mt-0.5 flex-shrink-0">{STATUS_ICONS[result.status]}</div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="text-sm font-semibold text-text">{result.category}</p>
                          <span className="text-[10px] px-1.5 py-0.5 rounded border border-border font-mono text-muted">
                            {result.standard}
                          </span>
                          <span className={`text-[10px] font-mono uppercase ${SEVERITY_COLORS[result.severity]}`}>
                            {result.severity}
                          </span>
                        </div>
                        <p className="text-xs text-muted mt-0.5">{result.requirement}</p>
                        <p className={`text-xs mt-2 font-mono ${result.status === "PASS" ? "text-success" : "text-danger"}`}>
                          {result.value}
                        </p>
                        {result.status === "FAIL" && (
                          <>
                            <p className="text-xs text-muted mt-1">{result.detail}</p>
                            {result.corrective_action && (
                              <div className="mt-2 p-2 rounded bg-warning/10 border border-warning/20">
                                <p className="text-[10px] text-warning font-semibold mb-0.5">CORRECTIVE ACTION:</p>
                                <p className="text-xs text-text">{result.corrective_action}</p>
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Standards covered */}
            <div className="card">
              <h2 className="section-title mb-3">Standards Covered</h2>
              <div className="flex flex-wrap gap-2">
                {report.standards_covered.map((s) => (
                  <span key={s} className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-xs text-primary">
                    <BookOpen className="w-3 h-3" />
                    {s}
                  </span>
                ))}
              </div>
            </div>
          </>
        )}

        {loading && !report && (
          <div className="card text-center py-16">
            <RefreshCw className="w-8 h-8 text-primary animate-spin mx-auto mb-3" />
            <p className="text-muted text-sm">Running compliance audit…</p>
          </div>
        )}
      </main>
    </div>
  );
}
