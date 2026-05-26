import { LuSun, LuMoon } from "react-icons/lu";
import { useTheme } from "../hooks/useTheme";

// Self-contained toggle — reads and mutates theme via context, no props needed
export default function ThemeToggle() {
  const { resolvedTheme, toggle } = useTheme();
  const isDark = resolvedTheme === "dark";

  return (
    <button
      className="theme-toggle"
      onClick={toggle}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      title={isDark ? "Light mode" : "Dark mode"}
    >
      {isDark ? <LuSun size={15} /> : <LuMoon size={14} />}
    </button>
  );
}
