import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useInvestigation } from '../hooks/useInvestigation'
import InvestigationForm from '../components/InvestigationForm'
import InvestigationHistory from '../components/InvestigationHistory'
import HeroSection from '../components/HeroSection'
import ExampleQueryCard from '../components/ExampleQueryCard'
import type { DashboardTriggerRequest } from '../types/index'

export default function HomePage() {
  const navigate = useNavigate()
  const { isAuthenticated, isLoading: authLoading, user } = useAuth()
  const {
    error,
    isLoadingReport,
    isSubmitting,
    selectedInvestigationId,
    historyRefreshKey,
    handleSelectHistory,
    handleSubmit,
  } = useInvestigation()

  useEffect(() => {
    if (authLoading) return
    if (isAuthenticated && user) {
      navigate(`/${user.orgId}`, { replace: true })
    }
  }, [authLoading, isAuthenticated, user, navigate])

  const handleFormSubmit = async (req: DashboardTriggerRequest) => {
    if (!isAuthenticated || !user) {
      navigate('/login')
      return
    }
    try {
      const reportId = await handleSubmit(req)
      navigate(`/${user.orgId}/report/${reportId}`)
    } catch {
      // Error is already set in context
    }
  }

  const handleSelectHistoryItem = async (investigationId: string) => {
    await handleSelectHistory(investigationId)
    if (user) {
      navigate(`/${user.orgId}/report/${investigationId}`)
      return
    }
    navigate(`/report/${investigationId}`)
  }

  return (
    <div className="landing-layout fade-up">
      <HeroSection
        alerts={
          <>
            {error && (
              <div className="alert-banner" role="alert">
                {error}
              </div>
            )}
            {isLoadingReport && (
              <div className="alert-banner">Loading investigation report…</div>
            )}
          </>
        }
        form={
          <InvestigationForm
            variant="hero"
            onSubmit={handleFormSubmit}
            isSubmitting={isSubmitting}
          />
        }
      />

      <InvestigationHistory
        onSelect={(id) => void handleSelectHistoryItem(id)}
        selectedId={selectedInvestigationId}
        refreshKey={historyRefreshKey}
      />

      <ExampleQueryCard />
    </div>
  )
}
