"use client";
import { useState, useEffect, useCallback } from "react";
import Sidebar from "@/components/layout/Sidebar";
import TopBar from "@/components/layout/TopBar";
import { permits as permitsApi } from "@/lib/api";
import type { Permit, PermitOverlap } from "@/lib/types";
import { FileCheck2, Plus, AlertTriangle, X, CheckCircle } from "lucide-react";

const ZONE_LABELS: Record<string, string> = {
  zone_a: "Production Floor", zone_b: "Storage Area", zone_c: "Chemical Processing",
  zone_d: "Loading Bay", zone_e: "Control Room", zone_f: "Confined Space",
};

const PERMIT_TYPES = [
  { type: "hot_work", label: "Hot Work" },
  { type: "confined_space", label: "Confined Space Entry" },
  { type: "electrical_isolation", label: "Electrical Isolation" },
  { type: "maintenance", label: "Maintenance Work" },
  { type: "height_work", label: "Working at Height" },
  { type: "chemical", label: "Chemical Handling" },
];

const STATUS_COLORS: Record<string, string> = {
  active: "text-success bg-success/10 border-success/30",
  completed: "text-muted bg-muted/10 border-muted/20",
  revoked: "text-danger bg-danger/10 border-danger/30",
  pending: "text-warning bg-warning/10 border-warning/30",
};

function OverlapCard({ overlap }: { overlap: PermitOverlap }) {
  return (
    <div className={`rounded-xl border p-4 space-y-2
      ${overlap.severity === "critical" ? "border-danger/50 bg-danger/8" : "border-warning/50 bg-warning/8"}`}>
      <div className="flex items-center gap-2">
        <AlertTriangle className={`w-4 h-4 ${overlap.severity === "critical" ? "text-danger" : "text-warning"}`} />
        <span className={`text-xs font-bold uppercase ${overlap.severity === "critical" ? "text-danger" : "text-warning"}`}>
          {overlap.severity} — Unsafe Permit Overlap
        </span>
      </div>
      <p className="text-xs text-text">{overlap.risk_description}</p>
      <div className="flex gap-2 flex-wrap">
        <span className="text-[10px] px-2 py-0.5 rounded border border-primary/30 text-primary font-mono">
          {overlap.permit_1.permit_type} #{overlap.permit_1.permit_number}
        </span>
        <span className="text-[10px] text-muted">+</span>
        <span className="text-[10px] px-2 py-0.5 rounded border border-primary/30 text-primary font-mono">
          {overlap.permit_2.permit_type} #{overlap.permit_2.permit_number}
        </span>
      </div>
      <p className="text-[10px] text-muted">💡 {overlap.recommended_action}</p>
    </div>
  );
}

export default function PermitsPage() {
  const [permitList, setPermitList] = useState<Permit[]>([]);
  const [overlaps, setOverlaps] = useState<PermitOverlap[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    permit_type: "hot_work", zone_id: "zone_a", worker_name: "",
    description: "", duration_hours: 8, issued_by: "Safety Officer",
  });
  const [formMsg, setFormMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    const [p, o] = await Promise.allSettled([permitsApi.list(), permitsApi.overlaps()]);
    if (p.status === "fulfilled") setPermitList(p.value);
    if (o.status === "fulfilled") setOverlaps(o.value);
  }, []);

  useEffect(() => { load(); const id = setInterval(load, 15000); return () => clearInterval(id); }, [load]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setFormMsg(null);
    try {
      const result = await permitsApi.create(form as Parameters<typeof permitsApi.create>[0]);
      setFormMsg(
        result.has_unsafe_overlap
          ? `⚠️ Permit ${result.permit.permit_number} created — ${result.overlap_warnings.length} unsafe overlap(s) detected!`
          : `✅ Permit ${result.permit.permit_number} issued successfully.`
      );
      setShowForm(false);
      setForm({ permit_type: "hot_work", zone_id: "zone_a", worker_name: "", description: "", duration_hours: 8, issued_by: "Safety Officer" });
      load();
    } catch (err) {
      setFormMsg("❌ Failed to create permit.");
    } finally {
      setLoading(false);
    }
  }

  async function updateStatus(id: number, status: string) {
    await permitsApi.updateStatus(id, status);
    load();
  }

  const activePermits = permitList.filter((p) => p.status === "active");

  return (
    <div className="min-h-screen bg-bg">
      <Sidebar />
      <TopBar title="Permit Control" subtitle="Permit-to-work management & overlap detection" />
      <main className="ml-60 pt-14 p-6 space-y-6">

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: "Active Permits", value: activePermits.length, color: "primary" },
            { label: "Unsafe Overlaps", value: overlaps.length, color: overlaps.length > 0 ? "danger" : "success" },
            { label: "Total Permits", value: permitList.length, color: "muted" },
          ].map(({ label, value, color }) => (
            <div key={label} className="card text-center">
              <p className={`text-3xl font-bold font-mono text-${color}`}>{value}</p>
              <p className="text-xs text-muted mt-1">{label}</p>
            </div>
          ))}
        </div>

        {/* Form message */}
        {formMsg && (
          <div className={`p-3 rounded-lg text-sm border ${formMsg.startsWith("✅") ? "border-success/30 bg-success/10 text-success" : formMsg.startsWith("⚠️") ? "border-warning/30 bg-warning/10 text-warning" : "border-danger/30 bg-danger/10 text-danger"}`}>
            {formMsg}
          </div>
        )}

        {/* Overlaps */}
        {overlaps.length > 0 && (
          <div className="space-y-3">
            <h2 className="section-title text-danger">⚠️ Unsafe Permit Overlaps ({overlaps.length})</h2>
            {overlaps.map((o, i) => <OverlapCard key={i} overlap={o} />)}
          </div>
        )}

        <div className="flex items-center justify-between">
          <h2 className="section-title">Active Permits</h2>
          <button onClick={() => setShowForm(!showForm)} className="btn-primary flex items-center gap-1.5">
            {showForm ? <X className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
            {showForm ? "Cancel" : "Issue Permit"}
          </button>
        </div>

        {/* Create form */}
        {showForm && (
          <div className="card">
            <h3 className="font-semibold text-sm text-text mb-4">Issue New Permit-to-Work</h3>
            <form onSubmit={handleCreate} className="grid grid-cols-2 gap-4">
              <div>
                <label className="label block mb-1.5">Permit Type</label>
                <select className="input" value={form.permit_type} onChange={(e) => setForm((f) => ({ ...f, permit_type: e.target.value }))}>
                  {PERMIT_TYPES.map(({ type, label }) => <option key={type} value={type}>{label}</option>)}
                </select>
              </div>
              <div>
                <label className="label block mb-1.5">Zone</label>
                <select className="input" value={form.zone_id} onChange={(e) => setForm((f) => ({ ...f, zone_id: e.target.value }))}>
                  {Object.entries(ZONE_LABELS).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
                </select>
              </div>
              <div>
                <label className="label block mb-1.5">Worker Name</label>
                <input required className="input" placeholder="e.g. Arjun Sharma" value={form.worker_name} onChange={(e) => setForm((f) => ({ ...f, worker_name: e.target.value }))} />
              </div>
              <div>
                <label className="label block mb-1.5">Issued By</label>
                <input className="input" value={form.issued_by} onChange={(e) => setForm((f) => ({ ...f, issued_by: e.target.value }))} />
              </div>
              <div>
                <label className="label block mb-1.5">Duration (hours)</label>
                <input type="number" className="input" min={1} max={24} value={form.duration_hours} onChange={(e) => setForm((f) => ({ ...f, duration_hours: +e.target.value }))} />
              </div>
              <div>
                <label className="label block mb-1.5">Description</label>
                <input required className="input" placeholder="Work description…" value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} />
              </div>
              <div className="col-span-2">
                <button type="submit" disabled={loading} className="btn-primary w-full justify-center">
                  {loading ? "Issuing…" : "Issue Permit"}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Permit table */}
        <div className="card overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-muted border-b border-border">
                {["Number", "Type", "Zone", "Worker", "Duration", "Status", "Actions"].map((h) => (
                  <th key={h} className="text-left pb-2 pr-4 font-medium uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border/30">
              {permitList.map((p) => (
                <tr key={p.id} className="hover:bg-surface2 transition-colors">
                  <td className="py-2 pr-4 font-mono text-primary">{p.permit_number}</td>
                  <td className="py-2 pr-4 font-medium text-text capitalize">{p.permit_type.replace(/_/g, " ")}</td>
                  <td className="py-2 pr-4 text-muted">{ZONE_LABELS[p.zone_id]}</td>
                  <td className="py-2 pr-4 text-text">{p.worker_name}</td>
                  <td className="py-2 pr-4 text-muted font-mono">
                    {new Date(p.start_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} →{" "}
                    {new Date(p.end_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </td>
                  <td className="py-2 pr-4">
                    <span className={`text-[10px] font-mono border px-1.5 py-0.5 rounded ${STATUS_COLORS[p.status] || ""}`}>
                      {p.status.toUpperCase()}
                    </span>
                  </td>
                  <td className="py-2">
                    <div className="flex gap-2">
                      {p.status === "active" && (
                        <>
                          <button onClick={() => updateStatus(p.id!, "completed")} className="text-[10px] text-success hover:underline">Complete</button>
                          <button onClick={() => updateStatus(p.id!, "revoked")} className="text-[10px] text-danger hover:underline">Revoke</button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {permitList.length === 0 && (
                <tr><td colSpan={7} className="py-8 text-center text-muted">No permits issued</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
