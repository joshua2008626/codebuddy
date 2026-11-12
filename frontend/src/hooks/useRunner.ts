import { useCallback, useRef, useState } from "react";
import { ApiError, executeCode, type ExecuteResult } from "../lib/api";
import type { WsFile } from "./useWorkspace";

export type RunState =
  | { phase: "idle" }
  | { phase: "running"; fileName: string }
  | { phase: "done"; fileName: string; result: ExecuteResult }
  | { phase: "error"; fileName: string; message: string; code: string };

/** Runs the active file through the backend. Only one run at a time. */
export function useRunner() {
  const [state, setState] = useState<RunState>({ phase: "idle" });
  const [runCount, setRunCount] = useState(0); // bumped on every run so the UI can jump to the Output tab
  const busy = useRef(false); // a ref, not state, so a fast double-click can't start two runs

  const run = useCallback(async (file: WsFile, stdin: string) => {
    if (busy.current) return;
    busy.current = true;
    setRunCount((c) => c + 1);
    setState({ phase: "running", fileName: file.name });
    try {
      const result = await executeCode({ language: file.language, sourceCode: file.content, stdin });
      setState({ phase: "done", fileName: file.name, result });
    } catch (e) {
      const err = e instanceof ApiError ? e : null;
      setState({
        phase: "error",
        fileName: file.name,
        message: err?.message ?? "Something went wrong while running your code.",
        code: err?.code ?? "unknown",
      });
    } finally {
      busy.current = false;
    }
  }, []);

  return { state, runCount, running: state.phase === "running", run };
}
