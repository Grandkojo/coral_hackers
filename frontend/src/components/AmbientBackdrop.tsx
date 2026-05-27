const EDGE_STACK = ['github', 'sentry', 'slack', 'vercel', 'coral'] as const

const TELEMETRY = [
  'read-path: coral sql',
  'mode: cross-source join',
  'agent: reef v0.1',
  'severity gate: active',
] as const

export default function AmbientBackdrop() {
  return (
    <div className="ambient-backdrop" aria-hidden="true">
      <div className="ambient-grid" />
      <div className="ambient-noise" />
      <div className="ambient-orb ambient-orb-left" />
      <div className="ambient-orb ambient-orb-right" />
      <div className="ambient-orb ambient-orb-bottom" />
      <div className="ambient-frame ambient-frame-left" />
      <div className="ambient-frame ambient-frame-right" />
      <div className="ambient-frame-corner ambient-frame-corner-tl" />
      <div className="ambient-frame-corner ambient-frame-corner-tr" />
      <div className="ambient-edge ambient-edge-left">
        <div className="ambient-stack">
          {EDGE_STACK.map((item) => (
            <span key={item} className="ambient-stack-item">
              {item}
            </span>
          ))}
        </div>
        <div className="ambient-telemetry">
          {TELEMETRY.map((line) => (
            <span key={line} className="ambient-telemetry-line">
              {line}
            </span>
          ))}
        </div>
      </div>
      <div className="ambient-edge ambient-edge-right">
        <div className="ambient-stack">
          {['issues', 'deploys', 'pulls', 'channels', 'queries'].map((item) => (
            <span key={item} className="ambient-stack-item ambient-stack-item-dim">
              {item}
            </span>
          ))}
        </div>
        <div className="ambient-telemetry ambient-telemetry-right">
          {TELEMETRY.map((line) => (
            <span key={`r-${line}`} className="ambient-telemetry-line">
              {line}
            </span>
          ))}
        </div>
      </div>
      <div className="ambient-horizon" />
    </div>
  )
}
