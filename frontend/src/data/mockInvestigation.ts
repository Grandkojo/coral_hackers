import type { ReportResponse } from '../types/index'

// Placeholder report returned while the real backend orchestration loop is not yet wired
export const MOCK_REPORT_BASE: Omit<ReportResponse, 'investigation_id'> = {
  timeline: [
    '14:23 UTC — Deploy dpl_9e2xk triggered on main@a4f2b9c',
    '14:31 UTC — Sentry FATAL: AuthenticationError spike (+340%)',
    '14:33 UTC — Slack #incidents: users reporting login failures',
    '14:45 UTC — Coral query correlated PR #234 as root cause',
  ],
  suspects: [
    'PR #234: auth-middleware token validation refactor',
    'Deploy dpl_9e2xk (main@a4f2b9c) — merged 14:21 UTC',
    'auth-service v2.3.1 — breaking JWT parsing change',
  ],
  citations: [
    'github.pull_requests#234',
    'sentry.issues#SENTRY-4521',
    'vercel.deployments#dpl_9e2xk',
    'slack.messages#incidents-1748293847',
  ],
  unresolved_gaps: ['Missing Datadog APM traces for auth-service during incident window'],
  severity_score: 0.72,
  remediation_mode: 'human_agent_paired',
  root_cause: 'PR #234 auth-middleware refactor correlated with fatal AuthenticationError spike after deploy dpl_9e2xk.',
  github_queries_executed: 1,
  github_queries_max: 2,
  github_rate_limited: false,
}
