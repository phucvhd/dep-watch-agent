// Small SVG charts for the dashboard widgets, built to the dataviz mark specs: bars at most
// 24px with a 4px rounded data-end and a square baseline, a 2px surface gap between stacked
// segments, 2px lines with ringed end-dots, hairline solid grid, a legend for two or more
// series, a tooltip on hover and keyboard focus (values first), and a table view for every
// chart. Colors are CSS variables validated as a set (see styles.css).
import { useEffect, useRef, useState, type ReactNode } from 'react'

export interface Series {
  key: string
  label: string
  color: string // a CSS color, usually var(--...)
  values: number[]
}

function useWidth<T extends HTMLElement>() {
  const ref = useRef<T>(null)
  const [width, setWidth] = useState(0)
  useEffect(() => {
    if (!ref.current) return
    const observer = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width))
    observer.observe(ref.current)
    return () => observer.disconnect()
  }, [])
  return [ref, width] as const
}

/** Round ticks (0, 5, 10 ...) covering ``max`` in about ``count`` steps. */
function niceTicks(max: number, count = 4): number[] {
  if (max <= 0) return [0, 1]
  const raw = max / count
  const magnitude = 10 ** Math.floor(Math.log10(raw))
  const step = ([1, 2, 5, 10].find((m) => m * magnitude >= raw) ?? 10) * magnitude
  const ticks = []
  for (let v = 0; v <= max + step * 0.999; v += step) ticks.push(Math.round(v * 1e6) / 1e6)
  return ticks
}

const fmt = (n: number) => n.toLocaleString()

/** A bar with a rounded data-end (top) and a square baseline. */
function barPath(x: number, y: number, w: number, h: number, r: number) {
  const rr = Math.min(r, h, w / 2)
  return `M${x},${y + h}V${y + rr}Q${x},${y} ${x + rr},${y}H${x + w - rr}Q${x + w},${y} ${x + w},${y + rr}V${y + h}Z`
}

interface FrameProps {
  title: string
  note?: ReactNode
  series: Series[]
  categories: string[]
  categoryLabel: string
  children: ReactNode
}

/** Title, legend (for two or more series), and a Chart/Table switch. */
function ChartFrame({ title, note, series, categories, categoryLabel, children }: FrameProps) {
  const [table, setTable] = useState(false)
  return (
    <figure className="chart">
      <figcaption className="chart-head">
        <span className="widget-title">{title}</span>
        <button
          type="button"
          className="chart-toggle"
          aria-pressed={table}
          onClick={() => setTable((t) => !t)}
        >
          {table ? 'Chart' : 'Table'}
        </button>
      </figcaption>
      {note && <p className="chart-note">{note}</p>}
      {series.length >= 2 && !table && (
        <ul className="chart-legend">
          {series.map((s) => (
            <li key={s.key}>
              <span className="legend-swatch" style={{ background: s.color }} aria-hidden="true" />
              {s.label}
            </li>
          ))}
        </ul>
      )}
      {table ? (
        <div className="table-wrap chart-table">
          <table>
            <thead>
              <tr>
                <th scope="col">{categoryLabel}</th>
                {series.map((s) => (
                  <th key={s.key} scope="col" className="num">
                    {s.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {categories.map((c, i) => (
                <tr key={c}>
                  <th scope="row">{c}</th>
                  {series.map((s) => (
                    <td key={s.key} className="num">
                      {fmt(s.values[i] ?? 0)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        children
      )}
    </figure>
  )
}

interface Tip {
  index: number
  x: number
  y: number
}

function Tooltip({
  tip,
  title,
  series,
  width,
}: {
  tip: Tip
  title: string
  series: Series[]
  width: number
}) {
  const left = Math.min(Math.max(tip.x + 12, 0), Math.max(0, width - 180))
  return (
    <div className="chart-tip" style={{ left, top: Math.max(0, tip.y - 8) }} role="status">
      <p className="chart-tip-title">{title}</p>
      {series.map((s) => (
        <p key={s.key} className="chart-tip-row">
          <span className="tip-key" style={{ background: s.color }} aria-hidden="true" />
          <strong>{fmt(s.values[tip.index] ?? 0)}</strong>
          <span>{s.label}</span>
        </p>
      ))}
    </div>
  )
}

const PAD = { top: 12, right: 8, bottom: 26, left: 36 }

interface ColumnProps {
  title: string
  note?: ReactNode
  categories: string[] // x labels
  categoryLabel: string
  series: Series[] // stacked bottom to top, in this order
  height?: number
  /** Per-column color for a single series (emphasis: one column dark, the rest gray). */
  colorOf?: (index: number) => string
  /** A label under the axis for one column, e.g. "yours". */
  marker?: { index: number; label: string }
  /** Least room per x label, in px; short labels (3.9) can sit closer than dates. */
  labelSpacing?: number
}

/** Columns, stacked when there are several series. */
export function ColumnChart({
  title,
  note,
  categories,
  categoryLabel,
  series,
  height = 190,
  colorOf,
  marker,
  labelSpacing = 56,
}: ColumnProps) {
  const [ref, width] = useWidth<HTMLDivElement>()
  const [tip, setTip] = useState<Tip>()
  const totals = categories.map((_, i) => series.reduce((sum, s) => sum + (s.values[i] ?? 0), 0))
  const ticks = niceTicks(Math.max(...totals, 0))
  const top = ticks[ticks.length - 1]
  const plotW = Math.max(0, width - PAD.left - PAD.right)
  const plotH = height - PAD.top - PAD.bottom
  const band = categories.length ? plotW / categories.length : 0
  const barW = Math.max(2, Math.min(24, band * 0.62))
  const y = (v: number) => PAD.top + plotH - (v / top) * plotH
  const labelEvery = Math.max(
    1,
    Math.ceil(categories.length / Math.max(1, Math.floor(plotW / labelSpacing))),
  )

  return (
    <ChartFrame
      title={title}
      note={note}
      series={series}
      categories={categories}
      categoryLabel={categoryLabel}
    >
      <div className="chart-body" ref={ref} onPointerLeave={() => setTip(undefined)}>
        {width > 0 && (
          <svg width={width} height={height} role="img" aria-label={`${title}. Table view available.`}>
            {ticks.map((t) => (
              <g key={t}>
                <line className="chart-grid" x1={PAD.left} x2={width - PAD.right} y1={y(t)} y2={y(t)} />
                <text className="chart-axis" x={PAD.left - 8} y={y(t) + 4} textAnchor="end">
                  {fmt(t)}
                </text>
              </g>
            ))}
            {categories.map((c, i) => {
              const cx = PAD.left + band * i + band / 2
              let base = 0
              const segments = series
                .map((s) => ({ s, v: s.values[i] ?? 0 }))
                .filter(({ v }) => v > 0)
              const active = tip?.index === i
              return (
                <g
                  key={c}
                  className={active ? 'chart-col is-active' : 'chart-col'}
                  tabIndex={0}
                  aria-label={`${c}: ${series.map((s) => `${s.label} ${fmt(s.values[i] ?? 0)}`).join(', ')}`}
                  onPointerMove={() => setTip({ index: i, x: cx, y: y(totals[i]) })}
                  onFocus={() => setTip({ index: i, x: cx, y: y(totals[i]) })}
                  onBlur={() => setTip(undefined)}
                >
                  {/* The hit target is the whole band, not the painted bar. */}
                  <rect x={PAD.left + band * i} y={PAD.top} width={band} height={plotH} fill="transparent" />
                  {segments.map(({ s, v }, k) => {
                    const y1 = y(base + v)
                    const y0 = y(base)
                    base += v
                    const isTop = k === segments.length - 1
                    const gap = isTop ? 0 : 2 // the surface gap between stacked segments
                    const h = Math.max(0, y0 - y1 - gap)
                    const color = colorOf ? colorOf(i) : s.color
                    return isTop ? (
                      <path key={s.key} d={barPath(cx - barW / 2, y1, barW, y0 - y1, 4)} style={{ fill: color }} />
                    ) : (
                      <rect key={s.key} x={cx - barW / 2} y={y1 + gap} width={barW} height={h} style={{ fill: color }} />
                    )
                  })}
                  {(i % labelEvery === 0 || marker?.index === i) && (
                    <text
                      className={marker?.index === i ? 'chart-axis chart-axis-strong' : 'chart-axis'}
                      x={cx}
                      y={height - 8}
                      textAnchor="middle"
                    >
                      {c}
                    </text>
                  )}
                </g>
              )
            })}
            <line
              className="chart-baseline"
              x1={PAD.left}
              x2={width - PAD.right}
              y1={y(0)}
              y2={y(0)}
            />
            {marker && (
              <text
                className="chart-marker"
                x={PAD.left + band * marker.index + band / 2}
                y={y(totals[marker.index]) - 6}
                textAnchor="middle"
              >
                {marker.label}
              </text>
            )}
          </svg>
        )}
        {tip && width > 0 && (
          <Tooltip tip={tip} title={categories[tip.index]} series={series} width={width} />
        )}
      </div>
    </ChartFrame>
  )
}

interface LineProps {
  title: string
  note?: ReactNode
  categories: string[]
  categoryLabel: string
  series: Series[]
  height?: number
  formatCategory?: (c: string) => string
}

/** Lines over an ordered x, one y-axis, with a crosshair that snaps to the nearest x. */
export function LineChart({
  title,
  note,
  categories,
  categoryLabel,
  series,
  height = 220,
  formatCategory = (c) => c,
}: LineProps) {
  const [ref, width] = useWidth<HTMLDivElement>()
  const [index, setIndex] = useState<number>()
  const max = Math.max(0, ...series.flatMap((s) => s.values))
  const ticks = niceTicks(max)
  const top = ticks[ticks.length - 1]
  const pad = { ...PAD, right: 92 } // room for direct end labels
  const plotW = Math.max(0, width - pad.left - pad.right)
  const plotH = height - pad.top - pad.bottom
  const step = categories.length > 1 ? plotW / (categories.length - 1) : 0
  const x = (i: number) => pad.left + step * i
  const y = (v: number) => pad.top + plotH - (v / top) * plotH
  const labelEvery = Math.max(1, Math.ceil(categories.length / Math.max(1, Math.floor(plotW / 64))))
  const last = categories.length - 1

  // Direct end labels only when the line ends are far enough apart not to collide.
  const ends = series.map((s) => y(s.values[last] ?? 0))
  const endsApart = ends.every((a, i) => ends.every((b, j) => i === j || Math.abs(a - b) >= 16))

  function nearest(clientX: number, rect: DOMRect) {
    const i = Math.round((clientX - rect.left - pad.left) / (step || 1))
    return Math.min(last, Math.max(0, i))
  }

  return (
    <ChartFrame
      title={title}
      note={note}
      series={series}
      categories={categories.map(formatCategory)}
      categoryLabel={categoryLabel}
    >
      <div className="chart-body" ref={ref}>
        {width > 0 && (
          <svg
            width={width}
            height={height}
            role="img"
            tabIndex={0}
            aria-label={`${title}. Use the arrow keys to read each ${categoryLabel.toLowerCase()}; table view available.`}
            onPointerMove={(e) => setIndex(nearest(e.clientX, e.currentTarget.getBoundingClientRect()))}
            onPointerLeave={() => setIndex(undefined)}
            onFocus={() => setIndex((i) => i ?? last)}
            onBlur={() => setIndex(undefined)}
            onKeyDown={(e) => {
              if (e.key === 'ArrowLeft') setIndex((i) => Math.max(0, (i ?? last) - 1))
              if (e.key === 'ArrowRight') setIndex((i) => Math.min(last, (i ?? 0) + 1))
            }}
          >
            {ticks.map((t) => (
              <g key={t}>
                <line className="chart-grid" x1={pad.left} x2={pad.left + plotW} y1={y(t)} y2={y(t)} />
                <text className="chart-axis" x={pad.left - 8} y={y(t) + 4} textAnchor="end">
                  {fmt(t)}
                </text>
              </g>
            ))}
            {categories.map((c, i) =>
              i % labelEvery === 0 || i === last ? (
                <text key={c} className="chart-axis" x={x(i)} y={height - 8} textAnchor="middle">
                  {formatCategory(c)}
                </text>
              ) : null,
            )}
            {index !== undefined && (
              <line className="chart-crosshair" x1={x(index)} x2={x(index)} y1={pad.top} y2={pad.top + plotH} />
            )}
            {series.map((s) => (
              <g key={s.key}>
                <polyline
                  className="chart-line"
                  points={s.values.map((v, i) => `${x(i)},${y(v)}`).join(' ')}
                  style={{ stroke: s.color }}
                />
                <circle className="chart-dot" cx={x(last)} cy={y(s.values[last] ?? 0)} r={4} style={{ fill: s.color }} />
                {index !== undefined && (
                  <circle className="chart-dot" cx={x(index)} cy={y(s.values[index] ?? 0)} r={4} style={{ fill: s.color }} />
                )}
                {endsApart && (
                  <text className="chart-end" x={x(last) + 10} y={y(s.values[last] ?? 0) + 4}>
                    {s.label} {fmt(s.values[last] ?? 0)}
                  </text>
                )}
              </g>
            ))}
          </svg>
        )}
        {index !== undefined && width > 0 && (
          <Tooltip
            tip={{ index, x: x(index), y: pad.top }}
            title={formatCategory(categories[index])}
            series={series}
            width={width}
          />
        )}
      </div>
    </ChartFrame>
  )
}
