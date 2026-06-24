"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getCurrentUser } from "@/lib/api";

export default function Root() {
  const router = useRouter();
  useEffect(() => {
    const user = getCurrentUser();
    router.replace(user ? "/dashboard" : "/login");
  }, [router]);
  return (
    <div className="min-h-screen flex items-center justify-center bg-bg">
      <div className="text-muted font-mono text-sm animate-pulse">Initializing SENTINEL AI…</div>
    </div>
  );
}
