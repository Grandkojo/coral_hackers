import { FaGithub, FaSlack } from "react-icons/fa";
import { SiSentry, SiVercel } from "react-icons/si";
import type { IconType } from "react-icons";

const SOURCES: { name: string; role: string; color: string; dim: string; Icon: IconType }[] = [
  { name: 'GitHub',  role: 'PRs · commits · ownership', color: 'var(--ink)',  dim: 'rgba(23,20,16,0.06)', Icon: FaGithub  },
  { name: 'Sentry',  role: 'errors · incidents',         color: 'var(--red)',  dim: 'var(--red-dim)',      Icon: SiSentry  },
  { name: 'Slack',   role: 'threads · slash commands',   color: 'var(--blue)', dim: 'var(--blue-dim)',     Icon: FaSlack   },
  { name: 'Vercel',  role: 'deployments',                color: 'var(--ink)',  dim: 'rgba(23,20,16,0.06)', Icon: SiVercel  },
]

// Displays connected Coral data sources with hover lift micro-interaction
export default function SourceBadges() {
  return (
    <div className="flex flex-wrap items-center justify-center gap-2.5">
      {SOURCES.map((s) => (
        <div
          key={s.name}
          className="source-tag"
          style={{ color: s.color, borderColor: s.color, background: s.dim }}
          title={s.role}
        >
          <s.Icon size={11} />
          {s.name}
        </div>
      ))}
    </div>
  )
}
