import { useContext } from 'react'
import type { Evidence } from '../api/client'
import { VersionOrder } from './versionOrder'

type Mark = 'introduced' | 'affects' | 'unaffected' | 'fix'

const MARK_TEXT: Record<Mark, string> = {
  introduced: 'bug starts',
  affects: 'bug seen',
  unaffected: 'bug absent',
  fix: 'fixed',
}

interface Props {
  pinned: string
  evidence: Evidence[]
  fixVersions: string[]
}

/**
 * The versions an issue's facts talk about, on one axis with the version you run. It shows
 * why an answer came out as it did: e.g. every "seen" mark sitting above your version is why
 * an issue can't be told apart from a bug that started later.
 */
export function VersionRuler({ pinned, evidence, fixVersions }: Props) {
  const order = useContext(VersionOrder)
  const marks = new Map<string, Set<Mark>>()
  const add = (version: string, mark?: Mark) => {
    if (!marks.has(version)) marks.set(version, new Set())
    if (mark) marks.get(version)!.add(mark)
  }
  add(pinned)
  for (const e of evidence) add(e.version, e.kind)
  for (const v of fixVersions) add(v, 'fix')

  // Versions JIRA doesn't list keep their place in the input, after the listed ones.
  const versions = [...marks.keys()]
    .map((v, i) => ({ v, rank: order.get(v) ?? order.size + i }))
    .sort((a, b) => a.rank - b.rank)
    .map(({ v }) => v)

  // Sized by how many versions there are, and never stretched past that, so labels keep
  // their size: a two-version ruler fits a phone without shrinking.
  const width = Math.min(640, Math.max(260, versions.length * 88 + 72))
  const pad = 36
  const step = versions.length > 1 ? (width - 2 * pad) / (versions.length - 1) : 0
  const x = (i: number) => (versions.length > 1 ? pad + i * step : width / 2)
  const axisY = 40
  // Many versions: alternate the labels between two rows so they don't run into each other.
  const stagger = versions.length > 8

  const description = versions
    .map((v) => {
      const kinds = [...marks.get(v)!].map((m) => MARK_TEXT[m])
      if (v === pinned) kinds.unshift('your version')
      return `${v}: ${kinds.join(', ') || 'no facts'}`
    })
    .join('; ')

  return (
    <svg
      className="ruler"
      viewBox={`0 0 ${width} ${stagger ? 78 : 66}`}
      style={{ maxWidth: width }}
      role="img"
      aria-label={`Versions in this issue. ${description}.`}
    >
      <line className="ruler-axis" x1={pad - 16} x2={width - pad + 16} y1={axisY} y2={axisY} />
      {versions.map((v, i) => {
        const cx = x(i)
        const kinds = marks.get(v)!
        const isPinned = v === pinned
        return (
          <g key={v}>
            {isPinned && (
              <>
                <line className="ruler-pin" x1={cx} x2={cx} y1={8} y2={axisY + 4} />
                <path className="ruler-pin-head" d={`M${cx - 5} 4 L${cx + 5} 4 L${cx} 11 Z`} />
              </>
            )}
            <line className="ruler-tick" x1={cx} x2={cx} y1={axisY - 3} y2={axisY + 3} />
            {kinds.has('fix') && (
              <rect className="mark-fix" x={cx - 2} y={axisY - 15} width={4} height={15} />
            )}
            {kinds.has('introduced') && (
              <path
                className="mark-introduced"
                d={`M${cx} ${axisY - 30} l7 7 l-7 7 l-7 -7 Z`}
              />
            )}
            {kinds.has('affects') && !kinds.has('introduced') && (
              <circle className="mark-affects" cx={cx} cy={axisY - 22} r={5.5} />
            )}
            {kinds.has('unaffected') && (
              <circle className="mark-unaffected" cx={cx} cy={axisY - 22} r={5} />
            )}
            <text
              className={isPinned ? 'ruler-label ruler-label-pinned' : 'ruler-label'}
              x={cx}
              y={axisY + 20 + (stagger && i % 2 ? 13 : 0)}
              textAnchor="middle"
            >
              {v}
            </text>
          </g>
        )
      })}
    </svg>
  )
}

/** The marks, explained once per page rather than on every ruler. */
export function RulerKey() {
  return (
    <dl className="ruler-key">
      <div>
        <dt>
          <svg viewBox="0 0 16 16" aria-hidden="true">
            <path className="mark-introduced" d="M8 1 l7 7 l-7 7 l-7 -7 Z" />
          </svg>
        </dt>
        <dd>bug starts here</dd>
      </div>
      <div>
        <dt>
          <svg viewBox="0 0 16 16" aria-hidden="true">
            <circle className="mark-affects" cx="8" cy="8" r="5.5" />
          </svg>
        </dt>
        <dd>bug seen on</dd>
      </div>
      <div>
        <dt>
          <svg viewBox="0 0 16 16" aria-hidden="true">
            <circle className="mark-unaffected" cx="8" cy="8" r="5" />
          </svg>
        </dt>
        <dd>bug absent on</dd>
      </div>
      <div>
        <dt>
          <svg viewBox="0 0 16 16" aria-hidden="true">
            <rect className="mark-fix" x="6" y="1" width="4" height="14" />
          </svg>
        </dt>
        <dd>fix released in</dd>
      </div>
      <div>
        <dt>
          <svg viewBox="0 0 16 16" aria-hidden="true">
            <line className="ruler-pin" x1="8" x2="8" y1="1" y2="15" />
          </svg>
        </dt>
        <dd>the version you run</dd>
      </div>
    </dl>
  )
}
