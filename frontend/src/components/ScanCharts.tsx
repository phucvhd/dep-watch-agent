import { useContext } from 'react'
import type { ScanResponse } from '../api/client'
import { ANSWER_TEXT } from '../format'
import { ColumnChart, type Series } from './charts'
import { VersionOrder } from './versionOrder'

// Stacked bottom to top in this order: orange and amber are never adjacent (the validated
// adjacency), and the bug that affects you sits on the baseline where it is easiest to read.
const STACK = [
  ['affected', 'var(--hit)'],
  ['not_affected', 'var(--clear)'],
  ['insufficient_information', 'var(--unknown)'],
] as const

const day = (iso: string) => iso.slice(0, 10)
const dayLabel = (d: string) =>
  new Date(`${d}T00:00:00Z`).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    timeZone: 'UTC',
  })

/** Scanned bugs per day of their last update, split by answer. */
export function BugsByDay({ result }: { result: ScanResponse }) {
  const days = result.items.map((i) => day(i.updated_at)).sort()
  const first = result.since ? day(result.since) : days[0]
  const last = days[days.length - 1] ?? first
  const categories: string[] = []
  for (let d = new Date(`${first}T00:00:00Z`); day(d.toISOString()) <= last; d.setUTCDate(d.getUTCDate() + 1)) {
    categories.push(day(d.toISOString()))
  }
  const series: Series[] = STACK.map(([answer, color]) => ({
    key: answer,
    label: ANSWER_TEXT[answer],
    color,
    values: categories.map(
      (c) => result.items.filter((i) => i.answer === answer && day(i.updated_at) === c).length,
    ),
  }))
  return (
    <ColumnChart
      title="Scanned bugs by day"
      categories={categories.map(dayLabel)}
      categoryLabel="Day"
      series={series}
    />
  )
}

/** The release line of a version: 3.9.1 -> 3.9; before 1.0 the scheme has four parts. */
function lineOf(version: string): string {
  const parts = version.replace(/^v/i, '').split('-')[0].split('.')
  return parts.slice(0, parts[0] === '0' ? 3 : 2).join('.')
}

/** How many scanned issues put the bug on each release line, the line you run picked out. */
export function EvidenceByLine({ result, version }: { result: ScanResponse; version: string }) {
  const order = useContext(VersionOrder)
  const counts = new Map<string, number>()
  for (const item of result.items) {
    const lines = new Set(
      item.evidence
        .filter((e) => e.kind === 'introduced' || e.kind === 'affects')
        .map((e) => lineOf(e.version)),
    )
    for (const line of lines) counts.set(line, (counts.get(line) ?? 0) + 1)
  }
  const yours = lineOf(version)
  if (!counts.has(yours)) counts.set(yours, 0)

  // Release order from the API's version list (GET /versions): a line ranks where its
  // earliest listed release does. The UI never compares versions itself.
  const rank = (line: string) => {
    let best = Infinity
    for (const [name, i] of order) if (lineOf(name) === line && i < best) best = i
    return best
  }
  const lines = [...counts.keys()].sort((a, b) => rank(a) - rank(b))
  const yourIndex = lines.indexOf(yours)

  return (
    <ColumnChart
      title="Where the bugs were seen"
      categories={lines}
      categoryLabel="Release line"
      series={[
        { key: 'issues', label: 'Issues', color: 'var(--ink-3)', values: lines.map((l) => counts.get(l)!) },
      ]}
      colorOf={(i) => (i === yourIndex ? 'var(--ink)' : 'var(--ink-3)')}
      marker={{ index: yourIndex, label: 'yours' }}
      labelSpacing={30}
    />
  )
}
