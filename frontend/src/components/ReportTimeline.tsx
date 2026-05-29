import { useState } from 'react'
import { parseTimelineEntry, summarizeText } from '../lib/reportFormat'

interface ReportTimelineProps {
  entries: string[]
}

export default function ReportTimeline({ entries }: ReportTimelineProps) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})

  if (entries.length === 0) {
    return (
      <p className="report-empty">No investigation steps recorded.</p>
    )
  }

  return (
    <ol className="report-timeline">
      {entries.map((entry, index) => {
        const step = parseTimelineEntry(entry)
        const key = `${index}-${step.title}`
        const isOpen = expanded[key] ?? step.isRootCause
        const preview = summarizeText(step.body, 200)

        return (
          <li
            key={key}
            className={`report-timeline-step ${step.isRootCause ? 'report-timeline-step-root' : ''}`}
          >
            <button
              type="button"
              className="report-timeline-step-header"
              onClick={() =>
                setExpanded((prev) => ({ ...prev, [key]: !isOpen }))
              }
              aria-expanded={isOpen}
            >
              <span className="report-timeline-marker" aria-hidden>
                {step.isRootCause ? '✓' : step.iteration ?? '·'}
              </span>
              <span className="report-timeline-step-text">
                <span className="report-timeline-step-title">{step.title}</span>
                {!isOpen ? (
                  <span className="report-timeline-step-preview">{preview}</span>
                ) : null}
              </span>
              <span className="report-timeline-chevron">{isOpen ? '−' : '+'}</span>
            </button>
            {isOpen ? (
              <div className="report-timeline-step-body">{step.body}</div>
            ) : null}
          </li>
        )
      })}
    </ol>
  )
}
