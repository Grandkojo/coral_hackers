import { useState } from 'react'
import type { TriggerRequest } from '../types/index'

interface InvestigationFormProps {
  onSubmit: (req: TriggerRequest) => void
  isSubmitting: boolean
}

const SOURCES = ['dashboard', 'slack', 'webhook'] as const

export default function InvestigationForm({ onSubmit, isSubmitting }: InvestigationFormProps) {
  const [query, setQuery] = useState('')
  const [incidentId, setIncidentId] = useState('')
  const [source, setSource] = useState('dashboard')

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
    <form onSubmit={handleSubmit} className="pixel-card">
      <div className="border-b-2 border-[var(--color-edge)] px-5 py-3">
        <span className="section-label">TRIGGER INVESTIGATION</span>
      </div>

      <div className="p-5 space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <label className="section-label block">
              INCIDENT ID{' '}
              <span className="text-[var(--color-muted)]">(OPTIONAL)</span>
            </label>
            <input
              type="text"
              className="pixel-input"
              placeholder="SENTRY-4521 · INC-001"
              value={incidentId}
              onChange={(e) => setIncidentId(e.target.value)}
              disabled={isSubmitting}
            />
          </div>

          <div className="space-y-1.5">
            <label className="section-label block">SOURCE</label>
            <select
              className="pixel-select"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              disabled={isSubmitting}
            >
              {SOURCES.map((s) => (
                <option key={s} value={s}>
                  {s.toUpperCase()}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="space-y-1.5">
          <label className="section-label block">
            QUERY <span className="text-[var(--color-danger)]">*</span>
          </label>
          <textarea
            className="pixel-input resize-none"
            rows={3}
            placeholder="Why did checkout fail after the last deploy?"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isSubmitting}
          />
        </div>

        <div className="flex justify-end pt-1">
          <button
            type="submit"
            className="pixel-btn"
            disabled={!isValid || isSubmitting}
          >
            {isSubmitting ? 'LAUNCHING...' : '> LAUNCH INVESTIGATION'}
          </button>
        </div>
      </div>
    </form>
  )
}
