export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="site-footer-inner">
        <span
          className="font-mono text-[0.55rem]"
          style={{ color: "var(--muted)" }}
        >
          Reef v0.1.0 | Pirates of the Coral-bean | WeMakeDevs Coral Hackathon
          2026
        </span>
        <span
          className="font-mono text-[0.5rem]"
          style={{ color: "var(--muted)", opacity: 0.7 }}
        >
          Powered by Coral | cross-source incident intelligence
        </span>
      </div>
    </footer>
  );
}
