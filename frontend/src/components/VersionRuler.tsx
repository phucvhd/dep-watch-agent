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

/** The versions an issue talks about, in release order, each with its marks. */
function useAxis({ pinned, evidence, fixVersions }: Props) {
  const order = useContext(VersionOrder)
  const marks = new Map<string, Set<Mark>>()
  const add = (version: string, mark?: Mark) => {
    if (!marks.has(version)) marks.set(version, new Set())
    if (mark) marks.get(version)!.add(mark)
  }
  add(pinned)
  for (const e of evidence) add(e.version, e.kind)
  for (const v of fixVersions) add(v, 'fix')
  // Placed by the API's order (GET /versions); versions it doesn't list keep input order after.
  const versions = [...marks.keys()]
    .map((v, i) => ({ v, rank: order.get(v) ?? order.size + i }))
    .sort((a, b) => a.rank - b.rank)
    .map(({ v }) => v)
  return { versions, marks }
}

function describe(versions: string[], marks: Map<string, Set<Mark>>, pinned: string) {
  return versions
    .map((v) => {
      const kinds = [...marks.get(v)!].map((m) => MARK_TEXT[m])
      if (v === pinned) kinds.unshift('your version')
      return `${v}: ${kinds.join(', ') || 'no facts'}`
    })
    .join('; ')
}

function Marks({ kinds, x, y, scale = 1 }: { kinds: Set<Mark>; x: number; y: number; scale?: number }) {
  const s = scale
  return (
    <>
      {kinds.has('fix') && (
        <rect className="mark-fix" x={x - 2 * s} y={y - 7 * s} width={4 * s} height={14 * s} rx={1} />
      )}
      {kinds.has('introduced') && (
        <path
          className="mark-introduced"
          d={`M${x} ${y - 7 * s} l${7 * s} ${7 * s} l${-7 * s} ${7 * s} l${-7 * s} ${-7 * s} Z`}
        />
      )}
      {kinds.has('affects') && !kinds.has('introduced') && (
        <circle className="mark-affects" cx={x} cy={y} r={5.5 * s} />
      )}
      {kinds.has('unaffected') && <circle className="mark-unaffected" cx={x} cy={y} r={5 * s} />}
    </>
  )
}

/**
 * The signature view: every version the issue's facts name, on one axis with the version you
 * run. "Seen only above your version" reads at a glance as why an issue can't be told.
 */
export function VersionRuler(props: Props) {
  const { versions, marks } = useAxis(props)
  const { pinned } = props
  // Sized by version count and never stretched past it, so labels keep their size on a phone.
  const width = Math.min(680, Math.max(280, versions.length * 92 + 64))
  const pad = 32
  const step = versions.length > 1 ? (width - 2 * pad) / (versions.length - 1) : 0
  const x = (i: number) => (versions.length > 1 ? pad + i * step : width / 2)
  const stagger = versions.length > 8
  const axisY = 34
  const pinnedIndex = versions.indexOf(pinned)

  return (
    <svg
      className="ruler"
      viewBox={`0 0 ${width} ${stagger ? 80 : 68}`}
      style={{ maxWidth: width }}
      role="img"
      aria-label={`Versions in this issue. ${describe(versions, marks, pinned)}.`}
    >
      {pinnedIndex >= 0 && (
        <rect
          className="ruler-pin-band"
          x={x(pinnedIndex) - 20}
          y={4}
          width={40}
          height={stagger && pinnedIndex % 2 ? 72 : 60}
          rx={9}
        />
      )}
      <line className="ruler-axis" x1={8} x2={width - 8} y1={axisY} y2={axisY} />
      {pinnedIndex >= 0 && (
        <line
          className="ruler-pin"
          x1={x(pinnedIndex)}
          x2={x(pinnedIndex)}
          y1={12}
          y2={axisY + 8}
        />
      )}
      {versions.map((v, i) => (
        <g key={v}>
          <circle className="ruler-tick" cx={x(i)} cy={axisY} r={2} />
          <Marks kinds={marks.get(v)!} x={x(i)} y={axisY - 14} />
          <text
            className={v === pinned ? 'ruler-label ruler-label-pinned' : 'ruler-label'}
            x={x(i)}
            y={axisY + 22 + (stagger && i % 2 ? 12 : 0)}
            textAnchor="middle"
          >
            {v}
          </text>
        </g>
      ))}
    </svg>
  )
}

/** A thumbnail of the ruler for list rows: same marks, no labels. */
export function MiniRuler(props: Props) {
  const { versions, marks } = useAxis(props)
  const width = 88
  const pad = 8
  const x = (i: number) =>
    versions.length > 1 ? pad + (i * (width - 2 * pad)) / (versions.length - 1) : width / 2
  const axisY = 10
  return (
    <svg className="mini-ruler" viewBox={`0 0 ${width} 20`} aria-hidden="true">
      <line className="ruler-axis" x1={2} x2={width - 2} y1={axisY} y2={axisY} />
      {versions.map((v, i) =>
        v === props.pinned ? (
          <line key={v} className="ruler-pin" x1={x(i)} x2={x(i)} y1={2} y2={18} />
        ) : (
          <Marks key={v} kinds={marks.get(v)!} x={x(i)} y={axisY} scale={0.62} />
        ),
      )}
    </svg>
  )
}

/** The marks, explained once per page rather than on every ruler. */
export function RulerKey() {
  const item = (label: string, mark: Mark | 'pin') => (
    <div>
      <dt>
        <svg viewBox="-8 -8 16 16" aria-hidden="true">
          {mark === 'pin' ? (
            <line className="ruler-pin" x1={0} x2={0} y1={-7} y2={7} />
          ) : (
            <Marks kinds={new Set([mark])} x={0} y={0} scale={0.9} />
          )}
        </svg>
      </dt>
      <dd>{label}</dd>
    </div>
  )
  return (
    <dl className="ruler-key">
      {item('bug starts', 'introduced')}
      {item('seen on', 'affects')}
      {item('absent on', 'unaffected')}
      {item('fixed in', 'fix')}
      {item('your version', 'pin')}
    </dl>
  )
}

/** A sentence from the issue, with the version it is evidence for picked out. */
export function Quote({ text, version }: { text: string; version?: string }) {
  if (!version) return <blockquote className="quote">{text}</blockquote>
  const escaped = version.replace(/^[vV]/, '').replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const parts = text.split(new RegExp(`((?<![\\d.])[vV]?${escaped}(?!\\d|\\.\\d))`))
  return (
    <blockquote className="quote">
      {parts.map((part, i) => (i % 2 ? <mark key={i}>{part}</mark> : part))}
    </blockquote>
  )
}
