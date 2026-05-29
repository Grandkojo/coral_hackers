import type { RouteObject } from 'react-router-dom'
import App from './App'
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import OrgDashboardPage from './pages/OrgDashboardPage'
import ReportPage from './pages/ReportPage'

export const routes: RouteObject[] = [
  {
    path: '/',
    element: <App />,
    children: [
      {
        index: true,
        element: <HomePage />,
      },
      {
        path: 'login',
        element: <LoginPage />,
      },
      {
        path: 'signup',
        element: <SignupPage />,
      },
      {
        path: 'report/:reportId',
        element: <ReportPage />,
      },
      {
        path: ':orgId',
        element: <OrgDashboardPage />,
      },
      {
        path: ':orgId/report/:reportId',
        element: <ReportPage />,
      },
    ],
  },
]