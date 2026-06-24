"use client";
import { useState, useEffect, useCallback } from "react";
import Sidebar from "@/components/layout/Sidebar";
import TopBar from "@/components/layout/TopBar";
import { sensors } from "@/lib/api";
import { useWebSocket } from "@/hooks/useWebSocket";
import type { ZoneSummary, SensorReading, SensorHistory } from "@/lib/types";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { Activity, AlertTriangle, Thermometer, Wind, Droplets, Gauge, Zap } from "lucide-react";

const ZONE_LABELS: Record<string, string> = {
  zone_a: "Production Floor", zone_b: "Storage Area", zone_c: "Chemical Processing",
  zone_d: "Loading Bay", zone_e: "Control Room", zone_f: "Confined Space",
};

const SENSOR_META: Record<string, { icon: React.ElementType; label: string; color: string }> = {
  methane:     { icon: Wind,       label: "Methane",     color: "#ef4444" },
  temperature: { icon: Thermometer,label: "Temperature", color: "#f59e0b" },
  humidity:    { icon: Droplets,   label: "Humidity",    color: "#3b82f6" },
  smoke:       { icon: Wind,       label: "Smoke",       color: "#8b5cf6" },
  pressure:    { icon: Gauge,      label: "Pressure",    color: "#10b981" },
  vibration:   { icon: Zap,        label: "Vibration",   color: "#00d4ff" },
};

const THRESHOLDS: Record<string, [number, number]> = {
  methane: [5, 10], temperature: [45, 65], humidity: [75, 90],
  smoke: [100, 200], pressure: [6, 8.5], vibration: [15, 25],
};

function SensorCard({ reading, onClick }: { reading: SensorReading; onClick: () => void }) {
  const meta = SENSOR_META[reading.sensor_type];
  const [warn, crit] = THRESHOLDS[reading.sensor_type] || [0, 0];
  const Icon = meta?.icon || Activity;
  const pct = Math.min(100, (reading.value / crit) * 80);

  return (
    <button
      onClick={onClick}
      className={`card text-left hover:border-border/70 transition-all w-full
        ${reading.is_critical ? "border-danger/50 bg-danger/5" : reading.is_warning ? "border-warning/50 bg-warning/5" : ""}`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4" style={{ color: meta?.color }} />
          <span className="text-xs font-medium text-muted">{meta?.label || reading.sensor_type}</span>
        </div>
        {reading.is_critical && <span className="badge-critical">CRIT</span>}
        {reading.is_warning && !reading.is_critical && <span className="badge-warning">WARN</span>}
      </div>
      <p className="text-2xl font-bold font-mono text-text">{reading.value.toFixed(1)}</p>
      <p className="text-xs text-muted mb-2">{reading.unit}</p>
      <div className="risk-bar">
        <div
          className="risk-bar-fill"
          style={{
            width: `${pct}%`,
            backgroundColor: reading.is_critical ? "#ef4444" : reading.is_warning ? "#f59e0b" : meta?.color,
          }}
        />
      </div>
      <div className="flex justify-between text-[10px] text-muted mt-1">
        <span>WARN: {warn}</span><span>CRIT: {crit}</span>
      </div>
    </button>
  );
}

function HistoryChart({ sensorId, stype, color }: { sensorId: string; stype: string; color: string }) {
  const [data, setData] = useState<SensorHistory[]>([]);
  const [warn, crit] = THRESHOLDS[stype] || [0, 0];

  useEffect(() => {
    sensors.history(sensorId, 30).then(setData).catch(() => {});
    const id = setInterval(() => sensors.history(sensorId, 30).then(setData).catch(() => {}), 6000);
    return () => clearInterval(id);
  }, [sensorId]);

  const chartData = data.map((d) => ({
    t: new Date(d.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    v: d.value,
  }));

  return (
    <div className="h-32">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 4, right: 4, bottom: 4, left: -20 }}>
          <XAxis dataKey="t" tick={{ fontSize: 9 }} interval="preserveStartEnd" />
          <YAxis tick={{ fontSize: 9 }} />
          <Tooltip
            contentStyle={{ background: "#111118", border: "1px solid #2a2a3e", fontSize: 11 }}
            labelStyle={{ color: "#94a3b8" }}
          />
          <ReferenceLine y={warn} stroke="#f59e0b" strokeDasharray="3 3" strokeWidth={1} />
          <ReferenceLine y={crit} stroke="#ef4444" strokeDasharray="3 3" strokeWidth={1} />
          <Line type="monotone" dataKey="v" stroke={color} strokeWidth={1.5} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function SensorsPage() {
  const [zones, setZones] = useState<ZoneSummary[]>([]);
  const [selected, setSelected] = useState<{ zoneId: string; sensorType: string } | null>(null);
  const [wsConnected, setWsConnected] = useState(false);

  const load = useCallback(async () => {
    const z = await sensors.zones().catch(() => []);
    setZones(z);
  }, []);

  useEffect(() => { load(); }, [load]);

  useWebSocket("/ws/sensors", (msg: unknown) => {
    const m = msg as { type: string; zones: ZoneSummary[] };
    setWsConnected(true);
    if (m.type === "sensor_update") setZones(m.zones);
  });

  const allCritical = zones.flatMap((z) =>
    Object.values(z.sensors).filter((s) => s.is_critical)
  ).length;

  return (
    <div className="min-h-screen bg-bg">
      <Sidebar />
      <TopBar title="Sensor Intelligence" subtitle="Live IoT monitoring across all zones" wsConnected={wsConnected} />
      <main className="ml-60 pt-14 p-6 space-y-6">

        {/* Header stats */}
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: "Total Sensors", value: zones.reduce((acc, z) => acc + Object.keys(z.sensors).length, 0), color: "primary" },
            { label: "Critical Alerts", value: allCritical, color: "danger" },
            { label: "Zones Monitored", value: zones.length, color: "success" },
          ].map(({ label, value, color }) => (
            <div key={label} className="card text-center">
              <p className={`text-3xl font-bold font-mono text-${color}`}>{value}</p>
              <p className="text-xs text-muted mt-1">{label}</p>
            </div>
          ))}
        </div>

        {/* Zone Grids */}
        {zones.map((zone) => (
          <div key={zone.zone_id} className="card space-y-4">
            <div className="flex items-center gap-3">
              <div className={`w-2 h-8 rounded-full ${zone.has_critical ? "bg-danger" : zone.has_warning ? "bg-warning" : "bg-success"}`} />
              <div>
                <h2 className="font-semibold text-text">{ZONE_LABELS[zone.zone_id]}</h2>
                <p className="text-xs text-muted font-mono">{zone.zone_id}</p>
              </div>
              {zone.has_critical && <span className="badge-critical ml-auto">CRITICAL SENSORS</span>}
              {zone.has_warning && !zone.has_critical && <span className="badge-warning ml-auto">WARNING</span>}
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
              {Object.values(zone.sensors).map((reading) => (
                <SensorCard
                  key={reading.sensor_id}
                  reading={reading}
                  onClick={() => setSelected({ zoneId: zone.zone_id, sensorType: reading.sensor_type })}
                />
              ))}
            </div>

            {/* Inline chart for selected sensor */}
            {selected?.zoneId === zone.zone_id && (
              <div className="bg-surface2 rounded-lg p-4 border border-border">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-text">
                    {SENSOR_META[selected.sensorType]?.label} — 30 min history
                  </h3>
                  <button onClick={() => setSelected(null)} className="text-xs text-muted hover:text-text">✕</button>
                </div>
                <HistoryChart
                  sensorId={`${zone.zone_id}_${selected.sensorType}`}
                  stype={selected.sensorType}
                  color={SENSOR_META[selected.sensorType]?.color || "#00d4ff"}
                />
              </div>
            )}
          </div>
        ))}
      </main>
    </div>
  );
}
