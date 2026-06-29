"use client";
import { useState, useEffect } from "react";
import { Bell, Wifi, WifiOff, User, Clock } from "lucide-react";
import { getCurrentUser } from "@/lib/api";
import type { EmergencyEvent } from "@/lib/types";

interface TopBarProps {
  title: string;
  subtitle?: string;
  activeEmergencies?: EmergencyEvent[];
  wsConnected?: boolean;
}

export default function TopBar({ title, subtitle, activeEmergencies = [], wsConnected = true }: TopBarProps) {
  const [time, setTime] = useState<string>("");
  // Read the user only after mount — getCurrentUser() reads localStorage, which is
  // empty during SSR. Reading it during render causes a hydration mismatch.
  const [user, setUser] = useState<ReturnType<typeof getCurrentUser>>(null);

  useEffect(() => {
    setUser(getCurrentUser());
    const tick = () => setTime(new Date().toUTCString().slice(17, 25) + " UTC");
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <header className="fixed top-0 left-60 right-0 h-14 bg-surface/80 backdrop-blur border-b border-border z-40 flex items-center px-6 gap-4">
      <div className="flex-1">
        <h1 className="text-sm font-semibold text-text">{title}</h1>
        {subtitle && <p className="text-xs text-muted">{subtitle}</p>}
      </div>

      {/* Emergency badge */}
      {activeEmergencies.length > 0 && (
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-danger/20 border border-danger/30 animate-pulse">
          <div className="w-1.5 h-1.5 rounded-full bg-danger" />
          <span className="text-xs text-danger font-mono font-semibold">
            {activeEmergencies.length} ACTIVE EMERGENCY
          </span>
        </div>
      )}

      {/* Clock */}
      <div className="flex items-center gap-1.5 text-xs text-muted font-mono">
        <Clock className="w-3.5 h-3.5" />
        {time}
      </div>

      {/* WS status */}
      <div className={`flex items-center gap-1.5 text-xs ${wsConnected ? "text-success" : "text-danger"}`}>
        {wsConnected ? <Wifi className="w-3.5 h-3.5" /> : <WifiOff className="w-3.5 h-3.5" />}
        <span className="font-mono">{wsConnected ? "LIVE" : "OFFLINE"}</span>
      </div>

      {/* User */}
      {user && (
        <div className="flex items-center gap-2 pl-3 border-l border-border">
          <div className="w-7 h-7 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center">
            <User className="w-3.5 h-3.5 text-primary" />
          </div>
          <div>
            <p className="text-xs font-medium text-text leading-none">{user.name}</p>
            <p className="text-[10px] text-muted capitalize">{user.role}</p>
          </div>
        </div>
      )}
    </header>
  );
}
