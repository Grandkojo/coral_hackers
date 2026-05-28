import { useInvestigation } from '../hooks/useInvestigation'
import InvestigationForm from '../components/InvestigationForm'
import InvestigationHistory from '../components/InvestigationHistory'
import HeroSection from '../components/HeroSection'
import ExampleQueryCard from '../components/ExampleQueryCard'

export default function HomePage() {
  const { error, isLoadingReport, selectedInvestigationId, historyRefreshKey, handleSelectHistory } = useInvestigation()

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
            onSubmit={() => Promise.resolve()}
            isSubmitting={false}
          />
        }
      />

      <InvestigationHistory
        onSelect={(id) => void handleSelectHistory(id)}
        selectedId={selectedInvestigationId}
        refreshKey={historyRefreshKey}
      />

      <ExampleQueryCard />
    </div>
  )
}
