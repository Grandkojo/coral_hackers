import ThemeToggle from "../components/ThemeToggle";

// Top navigation bar — theme state is read internally via useTheme inside ThemeToggle
export default function Header() {
  return (
    <header
      className="border-b px-6 py-3.5"
      style={{ borderColor: "var(--border)", background: "var(--surface)" }}
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4">
        <div className="flex items-center gap-5">
          <span
            className="font-pixel"
            style={{ fontSize: "0.55rem", color: "var(--accent)", lineHeight: 1.8 }}
          >
            INVINCIBLE
          </span>
          <span
            className="hidden font-mono text-[0.58rem] sm:block"
            style={{ color: "var(--muted)" }}
          >
            // incident intelligence
          </span>
        </div>

        <ThemeToggle />
      </div>
    </header>
  );
}
