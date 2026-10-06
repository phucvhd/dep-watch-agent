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

const WATCH_KEY = 'dep-watch.watch.v2'

/** One dependency the team runs, at the version they run it. */
export interface WatchItem {
  dependency: string // a dependency id from GET /dependencies
  version: string
  files?: string[] // the build files it was found in, if it came from a repository scan
}

export interface WatchState {
  repo: string | null // the repository folder the items were read from
  items: WatchItem[]
  active: number // the item every page answers for
}

const EMPTY: WatchState = { repo: null, items: [], active: 0 }

function readWatch(): WatchState {
  // A shared link (?dependency=<id>&version=<version>) wins over what this browser remembers.
  // Without a dependency it means the first watchable one (resolved where the list is known).
  const link = new URLSearchParams(window.location.search)
  const version = link.get('version')
  if (version) {
    return { repo: null, items: [{ dependency: link.get('dependency') ?? '', version }], active: 0 }
  }
  try {
    const stored = JSON.parse(localStorage.getItem(WATCH_KEY) ?? 'null')
    if (stored && Array.isArray(stored.items)) return { ...EMPTY, ...stored }
  } catch {
    // unreadable or blocked storage: start fresh
  }
  return EMPTY
}

/** What this team watches: the dependencies of their repository they chose, with versions. */
export function useWatch() {
  const [state, setState] = useState(readWatch)
  const save = useCallback((next: WatchState) => {
    setState(next)
    try {
      localStorage.setItem(WATCH_KEY, JSON.stringify(next))
    } catch {
      // private mode: the choice lasts for this visit only
    }
  }, [])
  const active = state.items[Math.min(state.active, state.items.length - 1)]
  return {
    repo: state.repo,
    items: state.items,
    active,
    activeIndex: active ? state.items.indexOf(active) : -1,
    select: useCallback((index: number) => save({ ...state, active: index }), [save, state]),
    replace: useCallback(
      (repo: string | null, items: WatchItem[]) => save({ repo, items, active: 0 }),
      [save],
    ),
  }
}

export function message(error: unknown): string {
  if (error instanceof ApiError || error instanceof Error) return error.message
  return String(error)
}

/** The JIRA sync jobs: which project is syncing, starting one, and a count that goes up each
 * time running syncs finish (a key to reload what they change). Follows running syncs by
 * polling; ``onFinished`` runs when they end. */
export function useSyncJobs(onFinished?: () => void) {
  const jobs = useLoad(() => api.jobs('sync-jira'), [])
  const [error, setError] = useState<string>()
  const [finished, setFinished] = useState(0)
  const anyRunning = jobs.data?.some(isActive) ?? false
  const reload = jobs.reload

  useEffect(() => {
    if (!anyRunning) return
    const timer = window.setInterval(reload, 3000)
    return () => window.clearInterval(timer)
  }, [anyRunning, reload])

  const wasRunning = useRef(false)
  const onFinishedRef = useRef(onFinished)
  useEffect(() => {
    onFinishedRef.current = onFinished
  })
  useEffect(() => {
    if (wasRunning.current && !anyRunning) {
      onFinishedRef.current?.()
      setFinished((n) => n + 1)
    }
    wasRunning.current = anyRunning
  }, [anyRunning])

  const start = useCallback(
    async (project: string, full = false) => {
      setError(undefined)
      try {
        await api.startSync(project, full)
        reload()
      } catch (e) {
        setError(message(e))
      }
    },
    [reload],
  )

  return {
    /** The project's running sync, if any. */
    running: (project: string) =>
      jobs.data?.find((j) => j.params.project === project && isActive(j)),
    /** The project's latest sync, finished or not. */
    latest: (project: string) => jobs.data?.find((j) => j.params.project === project),
    anyRunning,
    finished,
    start,
    error,
  }
}
