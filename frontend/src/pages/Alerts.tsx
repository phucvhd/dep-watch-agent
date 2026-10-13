import { useMemo, useRef, useState, type FormEvent } from 'react'
import { useAnswers, type Answers } from '../answers'
import { api, type Answer, type Dependency, type Job, type ScanResponse } from '../api/client'
import { IssueDetail, IssueRow, type AnsweredIssue } from '../components/IssueResult'
import { RulerKey } from '../components/VersionRuler'
import { ErrorNote, ExperimentalNote, JobLine, StepHead } from '../components/common'
import { ANSWER_TEXT, dayStart, plural } from '../format'
import { isActive, message, useJob } from '../hooks'

const TABS: Answer[] = ['affected', 'insufficient_information', 'not_affected']

type ScanItem = ScanResponse['items'][number]

/** A scan item, or its answer from a later check once one succeeds. A check that fails again
 * keeps the item, with the new error. */
function current(item: ScanItem, answers: Answers): AnsweredIssue {
  if (!item.error) return item
  const s = answers.get(item.issue_key)
  if (s.state === 'answered') return { ...item, ...s.result, error: null }
  if (s.state === 'failed') return { ...item, error: s.error }
  return item
}

const pending = (answers: Answers, key: string) =>
  ['queued', 'reading'].includes(answers.get(key).state)

/** The first few keys, then how many more: a model server that was down fails every issue. */
function keyList(keys: string[]): string {
  return keys.length > 3 ? `${keys.slice(0, 3).join(', ')} +${keys.length - 3}` : keys.join(', ')
}

interface Props {
  dependency: Dependency
  version: string
  systems: string[]
  latestScanId?: string
  onScanned: () => void
  since: string // a date input's value: the scan covers issues updated since that day (UTC)
  onSince: (since: string) => void
}

/** The dashboard: is the watched version affected by what changed upstream, as widgets. */
export function Alerts({
  dependency,
  version,
  systems,
  latestScanId,
  onScanned,
  since,
  onSince: setSince,
}: Props) {
  const [startedId, setStartedId] = useState<string>()
  const { job } = useJob(startedId ?? latestScanId, onScanned)
  const [limit, setLimit] = useState(50)
  const [error, setError] = useState<string>()
  const [chosenTab, setTab] = useState<Answer>()

  async function startScan(event: FormEvent) {
    event.preventDefault()
    setError(undefined)
    try {
      const started = await api.startScan({
        version,
        project: dependency.project,
        since: dayStart(since),
        limit,
      })
      setStartedId(started.id)
    } catch (e) {
      setError(message(e))
    }
  }

  const running = isActive(job)
  const result = job?.status === 'succeeded' ? (job.result as unknown as ScanResponse) : undefined
  // Issues the scan couldn't check can be checked again here, one at a time.
  const failedKeys = useMemo(
    () => result?.items.filter((i) => i.error).map((i) => i.issue_key) ?? [],
    [result],
  )
  const answers = useAnswers(failedKeys.length ? version : '', failedKeys)
  const items = result?.items.map((item) => current(item, answers)) ?? []
  const counts = Object.fromEntries(
    TABS.map((answer) => [answer, items.filter((i) => i.answer === answer).length]),
  ) as Record<Answer, number>
  const failed = items.filter((i) => i.error)
  const rechecking = failed.some((i) => pending(answers, i.issue_key))
  const canRead = systems.length > 0
  const recheck = (key: string) => answers.check(key)
  const affected = counts.affected
  const tab: Answer = chosenTab ?? (affected > 0 ? 'affected' : 'insufficient_information')
  const target = `${dependency.name} ${version}`

  return (
    <>
      <StepHead n={3} title="Scan" />
      <section className="widget w-12 scan-widget" aria-labelledby="scan-title">
        <h2 id="scan-title" className="widget-title">
          Scan upstream issues for {target}
        </h2>
        <form className="toolbar" onSubmit={startScan}>
          <label>
            <span>Updated since</span>
            <input type="date" value={since} onChange={(e) => setSince(e.target.value)} />
          </label>
          <label>
            <span>Maximum issues</span>
            <input
              type="number"
              min={1}
              max={10000}
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
            />
          </label>
          <button className="primary" type="submit" disabled={running || systems.length === 0}>
            {running ? 'Scanning…' : 'Scan'}
          </button>
        </form>
        <ExperimentalNote dependency={dependency} />
        {systems.length === 0 && (
          <ErrorNote>No model is configured. Set DEP_WATCH_LLM_MODEL and restart the API.</ErrorNote>
        )}
        <ErrorNote>{error}</ErrorNote>
        {job && job.status !== 'succeeded' && (
          <JobLine
            job={job}
            describe={(j: Job) =>
              j.status === 'queued' ? 'Queued' : `Scanning: ${j.progress.toLocaleString()} checked`
            }
          />
        )}
        {failed.length > 0 && (
          <div className="note note-error failed-note" role="alert">
            <p>
              Check failed for {plural(failed.length, 'issue')} (
              {keyList(failed.map((i) => i.issue_key))}); listed as Inconclusive.
            </p>
            <button
              className="btn-sm"
              disabled={!canRead || rechecking}
              onClick={() => failed.forEach((i) => recheck(i.issue_key))}
            >
              {rechecking ? 'Checking again…' : 'Check again'}
            </button>
          </div>
        )}
      </section>

      <StepHead n={4} title="Results" muted={!result} />
      {result ? (
        <>
          <div className="w-12 count-tiles" role="tablist" aria-label="Answers">
            {TABS.map((answer) => (
              <button
                key={answer}
                role="tab"
                aria-selected={tab === answer}
                className={`widget count-tile count-${answer}`}
                onClick={() => setTab(answer)}
              >
                <span className="count-label">{ANSWER_TEXT[answer]}</span>
                <span className="count-value">{counts[answer]}</span>
              </button>
            ))}
          </div>
          <Triage
            key={tab}
            items={items}
            tab={tab}
            version={version}
            canRead={canRead}
            isPending={(key) => pending(answers, key)}
            onRecheck={recheck}
          />
        </>
      ) : (
        !running && (
          <section className="widget w-12 empty-tile">
            <p>No scan results for {target}.</p>
          </section>
        )
      )}
    </>
  )
}

function Triage({
  items: all,
  tab,
  version,
  canRead,
  isPending,
  onRecheck,
}: {
  items: AnsweredIssue[]
  tab: Answer
  version: string
  canRead: boolean
  isPending: (key: string) => boolean
  onRecheck: (key: string) => void
}) {
  const [filter, setFilter] = useState('')
  const [selectedKey, setSelectedKey] = useState<string>()
  const detailRef = useRef<HTMLDivElement>(null)

  const words = filter.trim().toLowerCase()
  const items = all
    .filter(
      (i) =>
        i.answer === tab &&
        (!words || `${i.issue_key} ${i.summary}`.toLowerCase().includes(words)),
    )
    // The ones that failed first, to check again; newest first otherwise (the scan's order).
    .sort((a, b) => Number(!!b.error) - Number(!!a.error))
  const selected = items.find((i) => i.issue_key === selectedKey) ?? items[0]

  return (
    <>
      <section
        className="widget w-5 list-widget"
        role="tabpanel"
        aria-label={ANSWER_TEXT[tab]}
      >
        <div className="widget-head">
          <h2 className="widget-title">
            {ANSWER_TEXT[tab]}
            <sup>{items.length}</sup>
          </h2>
          <input
            className="filter"
            type="search"
            placeholder="Filter"
            aria-label="Filter issues"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
        </div>
        {items.length === 0 ? (
          <p className="list-empty">
            {filter ? 'No matching issues' : 'No issues'}
          </p>
        ) : (
          <ul className="rows">
            {items.map((item) => (
              <IssueRow
                key={item.issue_key}
                item={item}
                pinned={version}
                selected={item.issue_key === selected?.issue_key}
                onSelect={() => {
                  setSelectedKey(item.issue_key)
                  if (window.matchMedia('(max-width: 960px)').matches) {
                    detailRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
                  }
                }}
              />
            ))}
          </ul>
        )}
      </section>
      <section className="widget w-7 detail-widget" ref={detailRef}>
        {selected ? (
          <>
            <IssueDetail key={selected.issue_key} item={selected} pinned={version} />
            {selected.error && (
              <div className="button-row detail-actions">
                <button
                  className="primary"
                  disabled={!canRead || isPending(selected.issue_key)}
                  onClick={() => onRecheck(selected.issue_key)}
                >
                  {isPending(selected.issue_key) ? 'Checking again…' : 'Check again'}
                </button>
              </div>
            )}
          </>
        ) : (
          <p className="list-empty">Select an issue</p>
        )}
        <RulerKey />
      </section>
    </>
  )
}
