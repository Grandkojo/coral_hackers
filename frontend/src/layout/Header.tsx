import { useLocation, useNavigate } from 'react-router-dom'
import { FiGlobe } from 'react-icons/fi'
import ThemeToggle from '../components/ThemeToggle'

export default function Header() {
  const location = useLocation()
  const navigate = useNavigate()

  const handleIntegrate = () => {
    navigate('/signup')
  }

  const handleHome = () => {
    if (location.pathname !== '/') {
      navigate('/')
    }
  }

  const isNotHome = location.pathname !== '/'

  return (
    <header className="site-header">
      <div className="site-header-inner">
        <div className="brand-lockup">
          {isNotHome ? (
            <button type="button" className="brand-button" onClick={handleHome}>
              <div className="brand-mark" aria-hidden="true">
                <span className="brand-mark-core" />
              </div>
              <div>
                <span className="brand-name">Reef</span>
                <span className="brand-tagline">Incident intelligence</span>
              </div>
            </button>
          ) : (
            <>
              <div className="brand-mark" aria-hidden="true">
                <span className="brand-mark-core" />
              </div>
              <div>
                <span className="brand-name">Reef</span>
                <span className="brand-tagline">Incident intelligence</span>
              </div>
            </>
          )}
        </div>

        <div className="site-header-actions">
          <button
            type="button"
            className="btn btn-ghost header-nav-btn"
            onClick={handleIntegrate}
            title="Integrate into your organization"
          >
            <FiGlobe />
            <span>Integrate</span>
          </button>
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
