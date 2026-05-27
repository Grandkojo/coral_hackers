import { useEffect, useState } from 'react'
import type { InvestigationSummary } from '../types/index'
import { fetchInvestigations } from '../api/investigations'

interface InvestigationHistoryProps {
  onSelect: (investigationId: string) => void
  selectedId?: string | null
  refreshKey?: number
  compact?: boolean
}

function formatWhen(iso: string | null): string {
  if (!iso) return '—'
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function truncate(text: string, max = 72): string {
  const trimmed = text.trim()
  if (trimmed.length <= max) return trimmed
  return `${trimmed.slice(0, max - 1)}…`
}

function severityLabel(score: number | null): string {
  if (score === null) return '—'
  return score.toFixed(2)
}

const INITIAL_VISIBLE = 5

export default function InvestigationHistory({
  onSelect,
  selectedId,
  refreshKey = 0,
  compact = false,
}: InvestigationHistoryProps) {
  const [items, setItems] = useState<InvestigationSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showAll, setShowAll] = useState(false)

  useEffect(() => {
    setShowAll(false)
  }, [refreshKey])

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      try {
        const result = await fetchInvestigations()
        if (!cancelled) {
          setItems(result.investigations)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load history')
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [refreshKey])

  const hiddenCount = Math.max(0, items.length - INITIAL_VISIBLE)
  const visibleItems =
    showAll || hiddenCount === 0 ? items : items.slice(0, INITIAL_VISIBLE)

  return (
    <div className={`card history-panel ${compact ? 'history-panel-compact' : ''}`}>
      <div className="card-header">
        <div>
          <span className="label block mb-1">Investigation history</span>
          <span className="font-body text-sm" style={{ color: 'var(--ink-2)' }}>
            Reopen past reports and query evidence
          </span>
        </div>
        {!loading && !error ? (
          <span className="feature-chip">{items.length} saved</span>
        ) : null}
      </div>

      <div className="history-panel-body">
        {loading ? (
          <p className="history-empty">Loading investigations…</p>
        ) : null}

        {error ? (
          <p className="history-empty history-error">{error}</p>
        ) : null}

        {!loading && !error && items.length === 0 ? (
          <p className="history-empty">
            No investigations yet. Launch one to start building history.
          </p>
        ) : null}

        {!loading && !error && items.length > 0 ? (
          <>
            <ul className="history-list">
              {visibleItems.map((item) => {
                const isSelected = selectedId === item.investigation_id
                const preview = item.root_cause || item.user_query

                return (
                  <li key={item.investigation_id}>
                    <button
                      type="button"
                      className={`history-item ${isSelected ? 'history-item-selected' : ''}`}
                      onClick={() => onSelect(item.investigation_id)}
                    >
                      <div className="history-item-top">
                        <span className="history-item-query">{truncate(item.user_query || 'Untitled investigation')}</span>
                        <span className="history-item-severity">{severityLabel(item.severity_score)}</span>
                      </div>

                      <p className="history-item-preview">{truncate(preview, compact ? 56 : 88)}</p>

                      <div className="history-item-meta">
                        <span>{formatWhen(item.completed_at ?? item.created_at)}</span>
                        <span>{item.source}</span>
                        <span>{item.status}</span>
                        {item.remediation_mode === 'human_agent_paired' ? (
                          <span>{item.approved_at ? 'approved' : 'needs approval'}</span>
                        ) : null}
                      </div>
                    </button>
                  </li>
                )
              })}
            </ul>

            {hiddenCount > 0 ? (
              <div className="history-expand-row">
                <button
                  type="button"
                  className="btn btn-ghost history-expand-btn"
                  onClick={() => setShowAll((prev) => !prev)}
                >
                  {showAll ? 'Show less' : `Show ${hiddenCount} more`}
                </button>
              </div>
            ) : null}
          </>
        ) : null}
      </div>
    </div>
  )
}
