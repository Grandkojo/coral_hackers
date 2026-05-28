import { Outlet } from 'react-router-dom'
import Header from './layout/Header'
import Footer from './layout/Footer'
import AmbientBackdrop from './components/AmbientBackdrop'

export default function App() {
  return (
    <div className="app-shell">
      <AmbientBackdrop />
      <Header />

      <main className="app-main">
        <div className="app-container">
          <Outlet />
        </div>
      </main>

      <Footer />
    </div>
  )
}
