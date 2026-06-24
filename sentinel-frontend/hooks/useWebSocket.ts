"use client";
import { useEffect, useRef, useCallback } from "react";
import { createWS } from "@/lib/api";

export function useWebSocket(path: string, onMessage: (data: unknown) => void, enabled = true) {
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();
  const reconnectCount = useRef(0);
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  const connect = useCallback(() => {
    if (!enabled) return;

    // Always close stale connection before opening a new one
    if (ws.current && ws.current.readyState !== WebSocket.CLOSED) {
      ws.current.onclose = null;  // prevent triggering reconnect from this close
      ws.current.close();
    }

    ws.current = createWS(path, (data) => onMessageRef.current(data));

    ws.current.onopen = () => {
      reconnectCount.current = 0;  // reset backoff on successful connect
    };

    ws.current.onclose = () => {
      if (!enabled) return;
      // Exponential backoff: 3s → 6s → 12s → 24s → 48s (cap 60s)
      const delay = Math.min(3000 * Math.pow(2, reconnectCount.current), 60000);
      reconnectCount.current += 1;
      reconnectTimer.current = setTimeout(connect, delay);
    };

    ws.current.onerror = () => {
      ws.current?.close();
    };
  }, [path, enabled]);  // stable — only changes if path or enabled changes

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      if (ws.current) {
        ws.current.onclose = null;  // prevent reconnect on unmount close
        ws.current.close();
        ws.current = null;
      }
    };
  }, [connect]);
}
