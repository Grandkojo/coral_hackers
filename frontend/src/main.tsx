import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import './index.css'
import { AuthProvider } from './contexts/AuthProvider.tsx'
import { ThemeProvider } from './contexts/ThemeProvider.tsx'
import { InvestigationProvider } from './contexts/InvestigationProvider.tsx'
import { routes } from './routes.tsx'

const router = createBrowserRouter(routes)

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider>
      <AuthProvider>
        <InvestigationProvider>
          <RouterProvider router={router} />
        </InvestigationProvider>
      </AuthProvider>
    </ThemeProvider>
  </StrictMode>,
)