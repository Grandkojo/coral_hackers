import { useLocation, useNavigate } from 'react-router-dom'
import { FiGlobe } from 'react-icons/fi'
import ThemeToggle from '../components/ThemeToggle'
import { useAuth } from '../hooks/useAuth'

export default function Header() {
  const location = useLocation()
  const navigate = useNavigate()
  const { isAuthenticated, user, logout } = useAuth()

  const handleIntegrate = () => {
    if (isAuthenticated && user) {
      navigate(`/${user.orgId}/settings`)
      return
    }
    navigate('/signup')
  }

  const handleHome = () => {
    if (isAuthenticated && user) {
      if (location.pathname !== `/${user.orgId}`) {
        navigate(`/${user.orgId}`)
      }
      return
    }
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
          {isAuthenticated && user ? (
            <span className="header-org-label">{user.orgName}</span>
          ) : null}
          <button
            type="button"
            className="btn btn-ghost header-nav-btn"
            onClick={handleIntegrate}
            title="Organization integrations"
          >
            <FiGlobe />
            <span>{isAuthenticated ? 'Integrations' : 'Integrate'}</span>
          </button>
          {isAuthenticated ? (
            <button
              type="button"
              className="btn btn-ghost header-nav-btn"
              onClick={() => {
                logout()
                navigate('/login')
              }}
            >
              Sign out
            </button>
          ) : (
            <button
              type="button"
              className="btn btn-ghost header-nav-btn"
              onClick={() => navigate('/login')}
            >
              Sign in
            </button>
          )}
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
