import { useEffect, useState } from 'react'
import type { QueryRunResponse } from '../types/index'
import { fetchQueryRuns } from '../api/investigations'
import PixelCard from './PixelCard'

interface QueryEvidencePanelProps {
  investigationId: string
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function QueryRunCard({ run }: { run: QueryRunResponse }) {
  const [open, setOpen] = useState(run.iteration === 0)
  const columns = run.rows.length > 0 ? Object.keys(run.rows[0]) : []

  return (
    <div
      className="border"
      style={{ borderColor: 'var(--border)', background: 'var(--surface-2)' }}
    >
      <button
        type="button"
        className="w-full flex items-center justify-between gap-3 p-4 text-left"
        onClick={() => setOpen((prev) => !prev)}
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className="label shrink-0" style={{ color: 'var(--blue)' }}>
            Iter {run.iteration + 1}
          </span>
          <span className="font-mono text-[0.64rem] truncate" style={{ color: 'var(--ink-2)' }}>
            {run.rationale ?? 'Coral query'}
          </span>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <span className="font-mono text-[0.58rem]" style={{ color: 'var(--muted)' }}>
            {run.row_count} rows
          </span>
          <span className="font-mono text-[0.58rem]" style={{ color: 'var(--accent)' }}>
            {open ? '−' : '+'}
          </span>
        </div>
      </button>

      {open ? (
        <div className="px-4 pb-4 space-y-4">
          <div>
            <span className="label block mb-2">SQL</span>
            <pre
              className="font-mono text-[0.62rem] leading-relaxed overflow-x-auto p-3"
              style={{
                background: 'var(--surface)',
                border: '1px solid var(--border)',
                color: 'var(--ink-2)',
              }}
            >
              {run.sql}
            </pre>
          </div>

          <div>
            <span className="label block mb-2">Citation</span>
            <span className="font-mono text-[0.62rem]" style={{ color: 'var(--accent)' }}>
              {run.citation}
            </span>
          </div>

          {run.rows.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse font-mono text-[0.58rem]">
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-strong)' }}>
                    {columns.map((col) => (
                      <th
                        key={col}
                        className="px-2 py-2 text-left font-normal"
                        style={{ color: 'var(--muted)' }}
                      >
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {run.rows.map((row, rowIndex) => (
                    <tr
                      key={rowIndex}
                      style={{ borderBottom: '1px solid var(--border)' }}
                    >
                      {columns.map((col) => (
                        <td
                          key={col}
                          className="px-2 py-2 align-top"
                          style={{ color: 'var(--ink-2)' }}
                        >
                          {formatCell(row[col])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="font-mono text-[0.62rem]" style={{ color: 'var(--muted)' }}>
              No rows returned for this query.
            </p>
          )}
        </div>
      ) : null}
    </div>
  )
}

export default function QueryEvidencePanel({ investigationId }: QueryEvidencePanelProps) {
  const [queryRuns, setQueryRuns] = useState<QueryRunResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      try {
        const result = await fetchQueryRuns(investigationId)
        if (!cancelled) {
          setQueryRuns(result.query_runs)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load query evidence')
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
  }, [investigationId])

  return (
    <PixelCard title="Queries & evidence">
      {loading ? (
        <p className="font-mono text-[0.64rem]" style={{ color: 'var(--muted)' }}>
          Loading Coral query runs…
        </p>
      ) : null}

      {error ? (
        <p className="font-mono text-[0.64rem]" style={{ color: 'var(--red)' }}>
          {error}
        </p>
      ) : null}

      {!loading && !error && queryRuns.length === 0 ? (
        <p className="font-mono text-[0.64rem]" style={{ color: 'var(--muted)' }}>
          No query runs recorded for this investigation.
        </p>
      ) : null}

      {!loading && !error && queryRuns.length > 0 ? (
        <div className="space-y-3">
          {queryRuns.map((run) => (
            <QueryRunCard key={run.id} run={run} />
          ))}
        </div>
      ) : null}
    </PixelCard>
  )
}
