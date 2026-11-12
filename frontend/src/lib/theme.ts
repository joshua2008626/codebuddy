import { useCallback, useEffect, useState } from "react";

export type Theme = "dark" | "light";
const KEY = "codebuddy-theme";

/** localStorage can throw (private windows, blocked storage), so every access is guarded. */
function readStored(): Theme {
  try {
    const v = localStorage.getItem(KEY);
    if (v === "light" || v === "dark") return v;
  } catch {
    /* ignore */
  }
  return "dark"; // dark-first product
}

function apply(theme: Theme) {
  document.documentElement.setAttribute("data-theme", theme);
}

export function initTheme() {
  apply(readStored());
}

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => readStored());

  useEffect(() => {
    apply(theme);
    try {
      localStorage.setItem(KEY, theme);
    } catch {
      /* ignore */
    }
  }, [theme]);

  const toggle = useCallback(() => setTheme((t) => (t === "dark" ? "light" : "dark")), []);
  return { theme, toggle };
}
