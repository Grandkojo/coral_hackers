import { useEffect, useEffectEvent, useState, type ReactNode } from "react";
import type { Theme, ResolvedTheme } from "../types/theme";
import { ThemeContext } from "./ThemeContext";

const STORAGE_KEY = "invincible-theme";

// "system" is kept in the type for forward-compatibility but always resolves to dark here
function resolve(theme: Theme): ResolvedTheme {
  return theme === "system" ? "dark" : theme;
}

function applyToDOM(resolved: ResolvedTheme) {
  document.documentElement.classList.toggle("dark", resolved === "dark");
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "light" || stored === "dark") return stored;
    if (stored !== null) localStorage.removeItem(STORAGE_KEY);
    return "dark"; // default
  });

  const [resolvedTheme, setResolvedTheme] = useState<ResolvedTheme>(() =>
    resolve(theme),
  );

  const setTheme = (next: Theme) => {
    setThemeState(next);
    localStorage.setItem(STORAGE_KEY, next);
  };

  // Toggles between dark and light
  const toggle = () => {
    setTheme(resolvedTheme === "dark" ? "light" : "dark");
  };

  const onThemeChange = useEffectEvent((resolved: ResolvedTheme) => {
    setResolvedTheme(resolved);
    applyToDOM(resolved);
  });

  // Apply to DOM whenever the stored preference changes
  useEffect(() => {
    onThemeChange(resolve(theme));
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme, toggle }}>
      {children}
    </ThemeContext.Provider>
  );
}
