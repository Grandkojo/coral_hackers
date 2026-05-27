import { FaGithub, FaSlack } from 'react-icons/fa'
import { SiSentry, SiVercel } from 'react-icons/si'
import type { IconType } from 'react-icons'

const SOURCES: {
  name: string
  role: string
  color: string
  Icon: IconType
}[] = [
  { name: 'GitHub', role: 'PRs, commits, ownership', color: 'var(--ink)', Icon: FaGithub },
  { name: 'Sentry', role: 'Errors and issue history', color: 'var(--red)', Icon: SiSentry },
  { name: 'Slack', role: 'Incident channel context', color: 'var(--blue)', Icon: FaSlack },
  { name: 'Vercel', role: 'Deployments and project links', color: 'var(--ink)', Icon: SiVercel },
]

export default function SourceBadges() {
  return (
    <div className="source-grid">
      {SOURCES.map((source) => (
        <div key={source.name} className="source-card" title={source.role}>
          <div className="source-card-icon" style={{ color: source.color }}>
            <source.Icon size={16} />
          </div>
          <div className="min-w-0">
            <p className="source-card-name">{source.name}</p>
            <p className="source-card-role">{source.role}</p>
          </div>
        </div>
      ))}
    </div>
  )
}
