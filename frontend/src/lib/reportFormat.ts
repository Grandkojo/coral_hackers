export interface ParsedTimelineStep {
  iteration: number | null
  title: string
  body: string
  isRootCause: boolean
}

const ITERATION_RE = /^Iteration\s+(\d+):\s*(.*)$/is
const ROOT_CAUSE_RE = /^Root cause identified:\s*(.*)$/is

export function parseTimelineEntry(entry: string): ParsedTimelineStep {
  const rootMatch = entry.match(ROOT_CAUSE_RE)
  if (rootMatch) {
    return {
      iteration: null,
      title: 'Root cause',
      body: rootMatch[1].trim(),
      isRootCause: true,
    }
  }

  const iterMatch = entry.match(ITERATION_RE)
  if (iterMatch) {
    const body = iterMatch[2].trim()
    return {
      iteration: Number(iterMatch[1]),
      title: `Iteration ${iterMatch[1]}`,
      body,
      isRootCause: false,
    }
  }

  return {
    iteration: null,
    title: 'Event',
    body: entry.trim(),
    isRootCause: false,
  }
}

export function summarizeText(text: string, max = 160): string {
  const normalized = text.replace(/\s+/g, ' ').trim()
  if (normalized.length <= max) return normalized
  return `${normalized.slice(0, max - 1)}…`
}

export function dedupeStrings(items: string[]): string[] {
  const seen = new Set<string>()
  const result: string[] = []
  for (const item of items) {
    const key = item.trim()
    if (!key || seen.has(key)) continue
    seen.add(key)
    result.push(key)
  }
  return result
}

export function parseCitationRunId(citation: string): number | null {
  const match = citation.match(/query-run\/(\d+)/)
  return match ? Number(match[1]) : null
}
