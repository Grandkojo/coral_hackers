import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { AiOutlineLoading3Quarters } from 'react-icons/ai'
import { useInvestigation } from '../hooks/useInvestigation'
import InvestigationHistory from '../components/InvestigationHistory'
import ReportPanel from '../components/ReportPanel'

export default function ReportPage() {
  const { orgId, reportId } = useParams<{ orgId: string; reportId: string }>()
  const navigate = useNavigate()
  const {
    report,
    selectedInvestigationId,
    historyRefreshKey,
    isLoadingReport,
    handleSelectHistory,
    handleReset,
  } = useInvestigation()

  useEffect(() => {
    if (reportId && !report) {
      handleSelectHistory(reportId).catch(() => {
        navigate(orgId ? `/${orgId}` : '/')
      })
    }
  }, [reportId, report, handleSelectHistory, navigate, orgId])

  const handleSelectHistoryItem = async (investigationId: string) => {
    await handleSelectHistory(investigationId)
    navigate(orgId ? `/${orgId}/report/${investigationId}` : `/report/${investigationId}`)
  }

  const handleBackToDashboard = () => {
    handleReset()
    navigate(orgId ? `/${orgId}` : '/')
  }

  if (isLoadingReport || (!report && reportId)) {
    return (
      <div className="report-loading-screen">
        <AiOutlineLoading3Quarters className="spin report-loading-icon" />
        <p className="report-loading-label">Loading report…</p>
      </div>
    )
  }

  return (
    <div className="report-layout fade-up">
      <aside className="report-sidebar">
        <InvestigationHistory
          compact
          onSelect={(id) => void handleSelectHistoryItem(id)}
          onDeleted={(id) => {
            if (id === reportId || id === selectedInvestigationId) {
              handleReset()
              navigate(orgId ? `/${orgId}` : '/')
            }
          }}
          selectedId={selectedInvestigationId}
          refreshKey={historyRefreshKey}
        />
      </aside>
      <div className="report-main">
        {report && <ReportPanel report={report} onReset={handleBackToDashboard} />}
      </div>
    </div>
  )
}
