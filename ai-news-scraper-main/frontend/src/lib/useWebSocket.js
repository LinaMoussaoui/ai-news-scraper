'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { WS_BASE } from './api';

/**
 * WebSocket hook with auto-reconnect, ping/pong, and event dispatching.
 *
 * @param {string}   channel   – one of 'events' | 'bronze' | 'silver' | 'gold'
 * @param {function} onMessage – callback receiving parsed JSON data
 * @param {object}   opts      – { enabled, reconnectInterval, maxRetries }
 */
export default function useWebSocket(channel = 'events', onMessage, opts = {}) {
  const {
    enabled = true,
    reconnectInterval = 3000,
    maxRetries = 10,
  } = opts;

  const [status, setStatus] = useState('disconnected'); // 'connecting' | 'connected' | 'disconnected' | 'error'
  const [retryCount, setRetryCount] = useState(0);
  const wsRef = useRef(null);
  const retriesRef = useRef(0);
  const pingRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const onMessageRef = useRef(onMessage);

  // Keep callback ref current without re-connecting
  useEffect(() => { onMessageRef.current = onMessage; }, [onMessage]);

  const connect = useCallback(() => {
    if (!enabled) return;

    const url = `${WS_BASE}/realtime/ws/${channel}`;
    setStatus('connecting');

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus('connected');
      retriesRef.current = 0;
      setRetryCount(0);

      // Start ping every 25s to keep alive
      pingRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ cmd: 'ping' }));
        }
      }, 25000);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'pong') return; // ignore pong
        onMessageRef.current?.(data);
      } catch {
        // ignore non-JSON
      }
    };

    ws.onerror = () => setStatus('error');

    ws.onclose = () => {
      setStatus('disconnected');
      clearInterval(pingRef.current);

      // Auto-reconnect
      if (retriesRef.current < maxRetries && enabled) {
        retriesRef.current += 1;
        setRetryCount(retriesRef.current);
        reconnectTimerRef.current = setTimeout(connect, reconnectInterval);
      }
    };
  }, [channel, enabled, reconnectInterval, maxRetries]);

  useEffect(() => {
    connect();
    return () => {
      clearInterval(pingRef.current);
      clearTimeout(reconnectTimerRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const disconnect = useCallback(() => {
    clearInterval(pingRef.current);
    clearTimeout(reconnectTimerRef.current);
    retriesRef.current = maxRetries; // prevent reconnect
    wsRef.current?.close();
  }, [maxRetries]);

  return { status, retryCount, disconnect, reconnect: connect };
}
