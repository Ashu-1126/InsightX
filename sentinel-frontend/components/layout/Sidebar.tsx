"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Activity, Zap, Box, FileCheck2,
  AlertTriangle, MessageSquareText, Clock, ShieldAlert,
  LogOut, ChevronRight, ShieldCheck, BrainCircuit,
} from "lucide-react";
import { logout } from "@/lib/api";
import { useRouter } from "next/navigation";

const NAV = [
  { href: "/dashboard",     label: "Command Center",    icon: LayoutDashboard },
  { href: "/sensors",       label: "Sensor Intelligence", icon: Activity },
  { href: "/risk",          label: "Risk Engine",       icon: Zap },
  { href: "/digital-twin",  label: "Digital Twin",      icon: Box },
  { href: "/permits",       label: "Permit Control",    icon: FileCheck2 },
  { href: "/incidents",     label: "Incident Registry", icon: AlertTriangle },
  { href: "/copilot",       label: "AI Copilot",        icon: MessageSquareText },
  { href: "/replay",        label: "Incident Replay",   icon: Clock },
  { href: "/compliance",    label: "Compliance Audit",  icon: ShieldCheck },
  { href: "/multi-agent",   label: "Multi-Agent",       icon: BrainCircuit },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  function handleLogout() {
    logout();
    router.push("/login");
  }

  return (
    <aside className="fixed left-0 top-0 h-screen w-60 bg-surface border-r border-border flex flex-col z-50 select-none">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-border">
        <div className="flex items-center gap-2.5">
          <div className="relative">
            <ShieldAlert className="w-7 h-7 text-primary" />
            <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-success rounded-full animate-pulse" />
          </div>
          <div>
            <p className="font-bold text-sm text-text tracking-wide">SENTINEL AI</p>
            <p className="text-[10px] text-muted font-mono uppercase tracking-widest">Safety Intelligence OS</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-3 px-2">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg mb-0.5 text-sm transition-all group
                ${active
                  ? "bg-primary/10 text-primary border border-primary/20"
                  : "text-muted hover:text-text hover:bg-surface2"
                }`}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span className="flex-1 font-medium">{label}</span>
              {active && <ChevronRight className="w-3 h-3" />}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-2 pb-4 border-t border-border pt-3">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg w-full text-sm text-muted hover:text-danger hover:bg-danger/10 transition-all"
        >
          <LogOut className="w-4 h-4" />
          <span className="font-medium">Sign Out</span>
        </button>
        <p className="text-[10px] text-muted/40 font-mono text-center mt-3">v2.0 © SENTINEL AI</p>
      </div>
    </aside>
  );
}
