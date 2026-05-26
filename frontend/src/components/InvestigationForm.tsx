import { useState } from 'react'
import type { TriggerRequest } from '../types/index'

interface InvestigationFormProps {
  onSubmit: (req: TriggerRequest) => void
  isSubmitting: boolean
}

const SOURCES = ['dashboard', 'slack', 'webhook'] as const

// Form for triggering a new investigation; maps 1:1 to the TriggerRequest backend schema
export default function InvestigationForm({ onSubmit, isSubmitting }: InvestigationFormProps) {
  const [query,      setQuery]      = useState('')
  const [incidentId, setIncidentId] = useState('')
  const [source,     setSource]     = useState('dashboard')

  const isValid = query.trim().length > 0

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!isValid || isSubmitting) return
    onSubmit({
      source,
      query: query.trim(),
      incident_id: incidentId.trim() !== '' ? incidentId.trim() : undefined,
      context: {},
    })
  }

  return (
    <form onSubmit={handleSubmit} className="card">
      <div className="card-header">
        <span className="label">Launch Investigation</span>
        <span className="font-mono text-[0.56rem]" style={{ color: 'var(--muted)' }}>
          POST /api/v1/triggers/dashboard
        </span>
      </div>

      <div className="p-6 space-y-5">
        <div className="grid gap-5 sm:grid-cols-2">
          <div className="space-y-2">
            <label className="label block">
              Incident ID
              <span className="ml-1.5" style={{ color: 'var(--muted)', fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>
                (optional)
              </span>
            </label>
            <input
              type="text"
              className="field-input"
              placeholder="SENTRY-4521 · INC-001"
              value={incidentId}
              onChange={(e) => setIncidentId(e.target.value)}
              disabled={isSubmitting}
            />
          </div>

          <div className="space-y-2">
            <label className="label block">Source</label>
            <select
              className="field-select"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              disabled={isSubmitting}
            >
              {SOURCES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="space-y-2">
          <label className="label block">
            Query
            <span className="ml-1" style={{ color: 'var(--accent)' }}>*</span>
          </label>
          <textarea
            className="field-input resize-none"
            rows={3}
            placeholder="Why did checkout fail after the last deploy?"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isSubmitting}
          />
          <p className="font-mono text-[0.58rem]" style={{ color: 'var(--muted)' }}>
            Natural-language prompt — the planner will translate this into Coral SQL queries.
          </p>
        </div>

        <div className="flex items-center justify-between pt-1">
          <span className="font-mono text-[0.58rem]" style={{ color: 'var(--muted)' }}>
            {isValid ? 'Ready to launch' : 'Query required'}
          </span>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={!isValid || isSubmitting}
          >
            {isSubmitting ? 'Launching...' : 'Launch investigation'}
          </button>
        </div>
      </div>
    </form>
  )
}
