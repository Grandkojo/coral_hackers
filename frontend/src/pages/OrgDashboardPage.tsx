import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useInvestigation } from '../hooks/useInvestigation'
import InvestigationForm from '../components/InvestigationForm'
import InvestigationHistory from '../components/InvestigationHistory'
import InvestigationPanel from '../components/InvestigationPanel'
import type { DashboardTriggerRequest } from '../types/index'

export default function OrgDashboardPage() {
  const { orgId } = useParams<{ orgId: string }>()
  const navigate = useNavigate()
  const { isAuthenticated, isLoading, user } = useAuth()

  useEffect(() => {
    if (isLoading) return
    if (!isAuthenticated) {
      navigate('/login', { replace: true })
      return
    }
    if (user && orgId && user.orgId !== orgId) {
      navigate(`/${user.orgId}`, { replace: true })
    }
  }, [isLoading, isAuthenticated, user, orgId, navigate])
  const {
    investigationState,
    selectedInvestigationId,
    isSubmitting,
    error,
    historyRefreshKey,
    handleSubmit: handleSubmitInvestigation,
    handleSelectHistory,
  } = useInvestigation()

  const handleSubmit = async (req: DashboardTriggerRequest) => {
    try {
      const reportId = await handleSubmitInvestigation(req)
      navigate(`/${orgId}/report/${reportId}`)
    } catch (err) {
      // Error is already set in context
    }
  }

  const handleSelectHistoryItem = async (investigationId: string) => {
    try {
      await handleSelectHistory(investigationId)
      navigate(`/${orgId}/report/${investigationId}`)
    } catch (err) {
      // Error is already set in context
    }
  }

  return (
    <div className="org-dashboard">
      {investigationState ? (
        <InvestigationPanel state={investigationState} />
      ) : (
        <div className="landing-layout fade-up">
          {error && (
            <div className="alert-banner" role="alert">
              {error}
            </div>
          )}
          <InvestigationForm
            variant="hero"
            onSubmit={handleSubmit}
            isSubmitting={isSubmitting}
          />

          <InvestigationHistory
            onSelect={(id) => void handleSelectHistoryItem(id)}
            selectedId={selectedInvestigationId}
            refreshKey={historyRefreshKey}
          />
        </div>
      )}
    </div>
  )
}
