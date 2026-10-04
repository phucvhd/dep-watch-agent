import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, api, type Job } from './api/client'

/** Load when `deps` change (they must be JSON-serializable); `reload` refetches. The last data
 * stays visible while a new load runs. */
export function useLoad<T>(load: () => Promise<T>, deps: unknown[] = []) {
  const [state, setState] = useState<{ data?: T; error?: string; key?: string }>({})
  const [nonce, setNonce] = useState(0)
  const loadRef = useRef(load)
  useEffect(() => {
    loadRef.current = load
  })
  const key = JSON.stringify([deps, nonce])

  useEffect(() => {
    let stale = false
    loadRef.current().then(
      (data) => !stale && setState({ data, key }),
      (e: unknown) => !stale && setState((s) => ({ data: s.data, error: message(e), key })),
    )
    return () => {
      stale = true
    }
  }, [key])

  const reload = useCallback(() => setNonce((n) => n + 1), [])
  return { data: state.data, error: state.error, loading: state.key !== key, reload }
}

export const isActive = (job?: Job) => job?.status === 'queued' || job?.status === 'running'

/** Follow a background job until it finishes. */
export function useJob(id: string | undefined, onDone?: (job: Job) => void) {
  const [job, setJob] = useState<Job>()
  const [error, setError] = useState<string>()
  const doneRef = useRef(onDone)
  useEffect(() => {
    doneRef.current = onDone
  })

  useEffect(() => {
    if (!id) return
    let stopped = false
    let timer: number | undefined
    const poll = () => {
      api
        .job(id)
        .then((next) => {
          if (stopped) return
          setJob(next)
          setError(undefined)
          if (isActive(next)) timer = window.setTimeout(poll, 2000)
          else doneRef.current?.(next)
        })
        .catch((e: unknown) => {
          if (stopped) return
          setError(message(e))
          timer = window.setTimeout(poll, 5000)
        })
    }
    poll()
    return () => {
      stopped = true
      window.clearTimeout(timer)
    }
  }, [id])

  // A job from a previous id is never shown for the current one.
  return { job: job?.id === id ? job : undefined, error }
}

const VERSION_KEY = 'dep-watch.kafka-version'

/** The Kafka version this team runs. Kept in the browser; every page reads it. A link with
 * `?kafka=3.9.1` opens on that version, so a page can be shared with a teammate. */
export function usePinnedVersion(): [string, (version: string) => void] {
  const [version, setVersion] = useState(() => {
    const fromLink = new URLSearchParams(window.location.search).get('kafka')
    if (fromLink) return fromLink
    try {
      return localStorage.getItem(VERSION_KEY) ?? ''
    } catch {
      return ''
    }
  })
  const update = useCallback((next: string) => {
    setVersion(next)
    try {
      localStorage.setItem(VERSION_KEY, next)
    } catch {
      // private mode: the choice lasts for this visit only
    }
  }, [])
  return [version, update]
}

export function message(error: unknown): string {
  if (error instanceof ApiError || error instanceof Error) return error.message
  return String(error)
}
