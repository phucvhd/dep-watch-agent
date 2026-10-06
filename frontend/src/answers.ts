import { useCallback, useEffect, useRef, useState } from 'react'
import { api, type CheckResponse } from './api/client'
import { message } from './hooks'

/** Where one issue's answer for a version stands. ``result`` is kept while a re-check runs or
 * after one fails, so the last answer stays on screen. */
export type AnswerState =
  | { state: 'loading' }
  | { state: 'unchecked' }
  | { state: 'queued'; result?: CheckResponse }
  | { state: 'reading'; result?: CheckResponse }
  | { state: 'answered'; result: CheckResponse }
  | { state: 'failed'; error: string; result?: CheckResponse }

export interface Answers {
  get: (key: string) => AnswerState
  /** Read the issue with the model, or with ``refresh`` read it again. One at a time: the
   * model server reads one issue at a time anyway, so the rest wait in order. */
  check: (key: string, refresh?: boolean) => void
}

interface Job {
  key: string
  version: string
  refresh: boolean
}

const at = (version: string, key: string) => `${version}|${key}`
const resultOf = (s: AnswerState | undefined) => (s && 'result' in s ? s.result : undefined)

/** Answers for ``version`` to the issues in ``keys``: the stored ones at once (no model call),
 * the others when checked. An empty ``version`` loads nothing. */
export function useAnswers(version: string, keys: string[]): Answers {
  const [entries, setEntries] = useState<Record<string, AnswerState>>({})
  const queue = useRef<Job[]>([])
  const busy = useRef(new Set<string>()) // queued or being read
  const draining = useRef(false)
  const alive = useRef(true)
  const keysId = keys.join(',')

  useEffect(() => {
    alive.current = true
    return () => {
      alive.current = false
      queue.current = []
    }
  }, [])

  useEffect(() => {
    if (!version || !keysId) return
    let current = true
    const asked = keysId.split(',')
    const update = (fill: (key: string, known: AnswerState | undefined) => AnswerState | null) =>
      setEntries((prev) => {
        const next = { ...prev }
        for (const key of asked) {
          const value = fill(key, prev[at(version, key)])
          if (value) next[at(version, key)] = value
        }
        return next
      })
    api
      .answers(version, asked)
      .then((body) => {
        if (!current) return
        const found = new Map(body.items.map((i) => [i.issue_key, i.result]))
        // A check started meanwhile knows better than the stored answer.
        update((key, known) =>
          known && known.state !== 'unchecked'
            ? null
            : found.get(key)
              ? { state: 'answered', result: found.get(key)! }
              : { state: 'unchecked' },
        )
      })
      .catch((e) => {
        if (current) update((_, known) => (known ? null : { state: 'failed', error: message(e) }))
      })
    return () => {
      current = false
    }
  }, [version, keysId])

  const drain = useCallback(async () => {
    if (draining.current) return
    draining.current = true
    while (queue.current.length > 0 && alive.current) {
      const job = queue.current.shift()!
      const id = at(job.version, job.key)
      setEntries((prev) => ({ ...prev, [id]: { state: 'reading', result: resultOf(prev[id]) } }))
      try {
        const result = await api.check({
          issue_key: job.key,
          version: job.version,
          refresh: job.refresh,
        })
        if (alive.current) setEntries((prev) => ({ ...prev, [id]: { state: 'answered', result } }))
      } catch (e) {
        if (alive.current) {
          setEntries((prev) => ({
            ...prev,
            [id]: { state: 'failed', error: message(e), result: resultOf(prev[id]) },
          }))
        }
      } finally {
        busy.current.delete(id)
      }
    }
    draining.current = false
  }, [])

  const check = useCallback(
    (key: string, refresh = false) => {
      const id = at(version, key)
      if (!version || busy.current.has(id)) return
      busy.current.add(id)
      setEntries((prev) => ({ ...prev, [id]: { state: 'queued', result: resultOf(prev[id]) } }))
      queue.current.push({ key, version, refresh })
      void drain()
    },
    [version, drain],
  )

  return {
    get: (key) => entries[at(version, key)] ?? { state: 'loading' },
    check,
  }
}
