export default function Footer() {
  return (
    <footer
      className="border-t px-6 py-5 text-center"
      style={{ borderColor: "var(--border)", background: "var(--surface)" }}
    >
      <div className="mx-auto max-w-5xl flex flex-col items-center gap-1.5">
        <span className="font-mono text-[0.55rem]" style={{ color: "var(--muted)" }}>
          INVINCIBLE v0.1.0-alpha · Pirates of the Coral-bean · WeMakeDevs Coral Hackathon 2026
        </span>
        <span className="font-mono text-[0.5rem]" style={{ color: "var(--muted)", opacity: 0.6 }}>
          powered by Coral · cross-source incident intelligence
        </span>
      </div>
    </footer>
  );
}
