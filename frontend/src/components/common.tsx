import type { ReactNode } from 'react'
import type { Dependency, Job } from '../api/client'
import { formatAgo, formatDate } from '../format'

export function ErrorNote({ children }: { children: ReactNode }) {
  if (!children) return null
  return (
    <p className="note note-error" role="alert">
      {children}
    </p>
  )
}

/** A running background job, described in words the page chooses. */
/** For a dependency answered before it has a ground truth: its answers aren't measured. */
export function ExperimentalNote({ dependency }: { dependency: Dependency }) {
  if (!dependency.experimental) return null
  return (
    <p className="note">
      {dependency.name} is experimental: its answers aren't measured against a ground truth yet.
      Read the cited facts before relying on one.
    </p>
  )
}

export function JobLine({ job, describe }: { job: Job; describe: (job: Job) => string }) {
  if (job.status === 'failed') {
    return (
      <p className="note note-error" role="alert">
        Stopped with an error: {job.error}
      </p>
    )
  }
  const running = job.status === 'queued' || job.status === 'running'
  return (
    <p className="job-line" aria-live="polite">
      {running && <span className="spinner" aria-hidden="true" />}
      {describe(job)}
    </p>
  )
}

export type Tone = 'idle' | 'hit' | 'calm'

/** The top of every page: the title on a gradient band. The gradient is a status where a page
 * has one (Scan: warm when a bug affects you, cool when none does); neutral otherwise. */
export function PageIntro({
  title,
  tone = 'idle',
  children,
}: {
  title: string
  tone?: Tone
  children?: ReactNode
}) {
  return (
    <header className={`intro page-hero hero-${tone}`}>
      <h1>{title}</h1>
      {children && <div className="intro-text">{children}</div>}
    </header>
  )
}

/** A numbered step of the scan flow: the steps are a real sequence. */
export function StepHead({ n, title, muted = false }: { n: number; title: string; muted?: boolean }) {
  return (
    <h2 className={muted ? 'step-head is-muted' : 'step-head'}>
      <span className="step-n">{String(n).padStart(2, '0')}</span>
      {title}
    </h2>
  )
}

/** Labeled values in a row, for statuses and summaries: "Last sync" over its date, not a
 * sentence around it. Empty values are left out. */
export function Fields({
  items,
  className,
}: {
  items: [string, ReactNode][]
  className?: string
}) {
  const shown = items.filter(([, value]) => value !== null && value !== undefined && value !== '')
  return (
    <dl className={className ? `fields ${className}` : 'fields'}>
      {shown.map(([label, value]) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  )
}

/** A date and time with how long ago it was, for "last sync" style values. */
export function Timestamp({ value }: { value: string }) {
  return (
    <>
      <time dateTime={value}>{formatDate(value)}</time>
      <span className="timestamp-ago">{formatAgo(value)}</span>
    </>
  )
}
