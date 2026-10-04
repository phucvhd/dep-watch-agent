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
