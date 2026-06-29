"use client";
import { useState, useEffect, useCallback } from "react";
import Sidebar from "@/components/layout/Sidebar";
import TopBar from "@/components/layout/TopBar";
import { incidents as incidentsApi } from "@/lib/api";
import { useWebSocket } from "@/hooks/useWebSocket";
import type { Incident } from "@/lib/types";
import { AlertTriangle, Filter, FileVideo, Image, FileJson } from "lucide-react";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const TYPE_COLORS: Record<string, string> = {
  ppe: "text-primary bg-primary/10 border-primary/30",
  "fire-smoke": "text-danger bg-danger/10 border-danger/30",
  fall: "text-warning bg-warning/10 border-warning/30",
  pose: "text-secondary bg-secondary/10 border-secondary/30",
  manual: "text-muted bg-muted/10 border-muted/20",
};

export default function IncidentsPage() {
  const [incidentList, setIncidentList] = useState<Incident[]>([]);
  const [filter, setFilter] = useState<{ status?: string; type?: string }>({});
  const [wsConnected, setWsConnected] = useState(false);

  const load = useCallback(async () => {
    const data = await incidentsApi.list(filter).catch(() => []);
    setIncidentList(data);
  }, [filter]);

  useEffect(() => { load(); }, [load]);

  useWebSocket("/ws/incidents", (msg: unknown) => {
    const m = msg as { type: string };
    setWsConnected(true);
    if (m.type === "incident") load();
  });

  function getFileUrl(path: string, type: "clips" | "incident-images" | "reports") {
    const token = typeof window !== "undefined" ? localStorage.getItem("sentinel_token") : null;
    return `${BASE}/${type}/${path}${token ? `?token=${token}` : ""}`;
  }

  const openCount  = incidentList.filter((i) => i.status === "Open").length;
  const closedCount = incidentList.filter((i) => i.status === "Closed").length;

  return (
    <div className="min-h-screen bg-bg">
      <Sidebar />
      <TopBar title="Incident Registry" subtitle="Complete incident history and evidence management" wsConnected={wsConnected} />
      <main className="ml-60 pt-14 p-6 space-y-6">

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4">
          {[
            { label: "Total", value: incidentList.length, color: "text-text" },
            { label: "Open", value: openCount, color: "text-warning" },
            { label: "In Progress", value: incidentList.filter((i) => i.status === "In Progress").length, color: "text-primary" },
            { label: "Closed", value: closedCount, color: "text-success" },
          ].map(({ label, value, color }) => (
            <div key={label} className="card text-center">
              <p className={`text-3xl font-bold font-mono ${color}`}>{value}</p>
              <p className="text-xs text-muted mt-1">{label}</p>
            </div>
          ))}
        </div>

        {/* Filters */}
        <div className="card flex items-center gap-4">
          <Filter className="w-4 h-4 text-muted flex-shrink-0" />
          <select
            className="input w-40"
            value={filter.status || ""}
            onChange={(e) => setFilter((f) => ({ ...f, status: e.target.value || undefined }))}
          >
            <option value="">All Status</option>
            <option value="Open">Open</option>
            <option value="In Progress">In Progress</option>
            <option value="Closed">Closed</option>
          </select>
          <select
            className="input w-40"
            value={filter.type || ""}
            onChange={(e) => setFilter((f) => ({ ...f, type: e.target.value || undefined }))}
          >
            <option value="">All Types</option>
            <option value="ppe">PPE</option>
            <option value="fire-smoke">Fire/Smoke</option>
            <option value="fall">Fall</option>
            <option value="pose">Pose</option>
            <option value="manual">Manual</option>
          </select>
          {(filter.status || filter.type) && (
            <button onClick={() => setFilter({})} className="text-xs text-muted hover:text-text">
              Clear filters
            </button>
          )}
        </div>

        {/* Table */}
        <div className="card overflow-x-auto">
          <table className="w-full text-xs min-w-[900px]">
            <thead>
              <tr className="text-muted border-b border-border">
                {["ID", "Type", "Description", "Source", "Confidence", "Camera", "Status", "Evidence", "Time"].map((h) => (
                  <th key={h} className="text-left pb-2 pr-3 font-medium uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border/30">
              {incidentList.map((inc) => (
                <tr key={inc.id} className="hover:bg-surface2 transition-colors group">
                  <td className="py-2.5 pr-3 font-mono text-muted">#{inc.id}</td>
                  <td className="py-2.5 pr-3">
                    <span className={`text-[10px] font-mono border px-1.5 py-0.5 rounded ${TYPE_COLORS[inc.type] || ""}`}>
                      {inc.type}
                    </span>
                  </td>
                  <td className="py-2.5 pr-3 text-text max-w-[240px] truncate">{inc.description}</td>
                  <td className="py-2.5 pr-3 text-muted capitalize">{inc.source?.replace("-", " ")}</td>
                  <td className="py-2.5 pr-3 font-mono text-text">
                    {inc.confidence != null ? `${(inc.confidence * 100).toFixed(0)}%` : "—"}
                  </td>
                  <td className="py-2.5 pr-3 text-muted">{inc.camera_id ? `#${inc.camera_id}` : "—"}</td>
                  <td className="py-2.5 pr-3">
                    <select
                      className="bg-transparent border-0 text-xs font-medium cursor-pointer focus:outline-none"
                      value={inc.status}
                      onChange={async (e) => {
                        await incidentsApi.updateStatus(inc.id, e.target.value);
                        load();
                      }}
                      style={{
                        color: inc.status === "Open" ? "#f59e0b" : inc.status === "Closed" ? "#10b981" : "#a8324a",
                      }}
                    >
                      <option value="Open">Open</option>
                      <option value="In Progress">In Progress</option>
                      <option value="Closed">Closed</option>
                    </select>
                  </td>
                  <td className="py-2.5 pr-3">
                    <div className="flex items-center gap-2">
                      {inc.clip_path && (
                        <a href={getFileUrl(inc.clip_path, "clips")} target="_blank" rel="noreferrer" title="View clip">
                          <FileVideo className="w-3.5 h-3.5 text-primary hover:text-primary/80" />
                        </a>
                      )}
                      {inc.evidence_image && (
                        <a href={getFileUrl(inc.evidence_image, "incident-images")} target="_blank" rel="noreferrer" title="View image">
                          <Image className="w-3.5 h-3.5 text-secondary hover:text-secondary/80" />
                        </a>
                      )}
                      {inc.report_path && (
                        <a href={getFileUrl(inc.report_path, "reports")} target="_blank" rel="noreferrer" title="JSON report">
                          <FileJson className="w-3.5 h-3.5 text-warning hover:text-warning/80" />
                        </a>
                      )}
                    </div>
                  </td>
                  <td className="py-2.5 font-mono text-muted whitespace-nowrap">
                    {new Date(inc.created_at).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                  </td>
                </tr>
              ))}
              {incidentList.length === 0 && (
                <tr><td colSpan={9} className="py-10 text-center text-muted">No incidents found</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
