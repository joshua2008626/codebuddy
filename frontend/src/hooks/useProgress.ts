import { useCallback, useState } from "react";
import { loadProgress, recordSubmission, saveProgress, type ProgressMap, type Verdict } from "../lib/progress";

export function useProgress() {
  const [map, setMap] = useState<ProgressMap>(loadProgress);
  const [storageOk, setStorageOk] = useState(true);

  const record = useCallback((id: string, verdict: Verdict, passed: number, total: number) => {
    // Read the latest saved value so two open tabs do not overwrite each other's progress.
    const next = recordSubmission(loadProgress(), id, verdict, passed, total);
    setStorageOk(saveProgress(next));
    setMap(next);
  }, []);

  return { map, record, storageOk };
}
