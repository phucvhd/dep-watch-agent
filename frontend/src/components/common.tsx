import type { ReactNode } from 'react'
import type { Job } from '../api/client'

export function ErrorNote({ children }: { children: ReactNode }) {
  if (!children) return null
  return (
    <p className="note note-error" role="alert">
      {children}
    </p>
  )
}

/** A running background job, described in words the page chooses. */
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
      <span className="step-n">{n}</span>
      {title}
    </h2>
  )
}
