import ThemeToggle from "../components/ThemeToggle";

interface HeaderProps {
  onHome?: () => void;
  showHistoryNav?: boolean;
}

export default function Header({
  onHome,
  showHistoryNav = false,
}: HeaderProps) {
  return (
    <header className="site-header">
      <div className="site-header-inner">
        <div className="brand-lockup">
          {onHome ? (
            <button type="button" className="brand-button" onClick={onHome}>
              <div className="brand-mark" aria-hidden="true">
                <span className="brand-mark-core" />
              </div>
              <div>
                <span className="brand-name">Reef</span>
                <span className="brand-tagline">
                  Incident intelligence
                </span>
              </div>
            </button>
          ) : (
            <>
              <div className="brand-mark" aria-hidden="true">
                <span className="brand-mark-core" />
              </div>
              <div>
                <span className="brand-name">Reef</span>
                <span className="brand-tagline">
                  Incident intelligence
                </span>
              </div>
            </>
          )}
        </div>

        <div className="site-header-actions">
          {showHistoryNav && onHome ? (
            <button
              type="button"
              className="btn btn-ghost header-nav-btn"
              onClick={onHome}
            >
              New investigation
            </button>
          ) : null}
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
