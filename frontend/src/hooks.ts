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

const WATCH_KEY = 'dep-watch.watch'

export interface Watch {
  dependency: string // a dependency id from GET /dependencies
  versions: Record<string, string> // the version run, per dependency
}

function readWatch(): Watch {
  const fallback: Watch = { dependency: 'kafka', versions: {} }
  let stored = fallback
  try {
    stored = { ...fallback, ...JSON.parse(localStorage.getItem(WATCH_KEY) ?? '{}') }
  } catch {
    // unreadable or blocked storage: start fresh
  }
  // A shared link (?dependency=kafka&version=3.9.1) wins over what this browser remembers.
  const link = new URLSearchParams(window.location.search)
  const dependency = link.get('dependency') ?? stored.dependency
  const version = link.get('version')
  return {
    dependency,
    versions: version ? { ...stored.versions, [dependency]: version } : stored.versions,
  }
}

/** What this team watches: a dependency and the version of it they run. Kept in the browser. */
export function useWatch() {
  const [watch, setWatch] = useState(readWatch)
  const save = useCallback((next: Watch) => {
    setWatch(next)
    try {
      localStorage.setItem(WATCH_KEY, JSON.stringify(next))
    } catch {
      // private mode: the choice lasts for this visit only
    }
  }, [])
  const setDependency = useCallback(
    (dependency: string) => save({ ...watch, dependency }),
    [save, watch],
  )
  const setVersion = useCallback(
    (version: string) =>
      save({ ...watch, versions: { ...watch.versions, [watch.dependency]: version } }),
    [save, watch],
  )
  return {
    dependency: watch.dependency,
    version: watch.versions[watch.dependency] ?? '',
    setDependency,
    setVersion,
  }
}

export function message(error: unknown): string {
  if (error instanceof ApiError || error instanceof Error) return error.message
  return String(error)
}
