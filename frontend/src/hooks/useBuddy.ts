import { useCallback, useRef, useState } from "react";
import { ApiError, askBuddy, type AskParams } from "../lib/api";

export interface BuddyEntry {
  id: number;
  mode: AskParams["mode"];
  label: string;
  pending: boolean;
  answer?: string;
  error?: string;
}

const MAX_ENTRIES = 20;

/** Session-only conversation with Buddy AI. Each question is independent; nothing is stored on the server. */
export function useBuddy() {
  const [entries, setEntries] = useState<BuddyEntry[]>([]);
  const nextId = useRef(1);
  const busy = useRef(false); // a ref so a fast double-click can't send two requests

  const ask = useCallback(async (params: AskParams, label: string) => {
    if (busy.current) return;
    busy.current = true;
    const id = nextId.current++;
    setEntries((es) => [...es, { id, mode: params.mode, label, pending: true }].slice(-MAX_ENTRIES));
    const patch = (p: Partial<BuddyEntry>) => setEntries((es) => es.map((e) => (e.id === id ? { ...e, pending: false, ...p } : e)));
    try {
      const res = await askBuddy(params);
      patch({ answer: res.answer });
    } catch (e) {
      patch({ error: e instanceof ApiError ? e.message : "Something went wrong while asking Buddy AI." });
    } finally {
      busy.current = false;
    }
  }, []);

  const clear = useCallback(() => setEntries([]), []);
  return { entries, asking: entries.some((e) => e.pending), ask, clear };
}
