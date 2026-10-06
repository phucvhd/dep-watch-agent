import { useMemo, useRef, useState, type FormEvent } from 'react'
import { api, type Answer, type Dependency, type Job, type ScanResponse } from '../api/client'
import { IssueDetail, IssueRow } from '../components/IssueResult'
import { RulerKey } from '../components/VersionRuler'
import { ErrorNote, JobLine, StepHead } from '../components/common'
import { ANSWER_TEXT, dayStart, plural } from '../format'
import { isActive, message, useJob } from '../hooks'

const TABS: Answer[] = ['affected', 'insufficient_information', 'not_affected']

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
  const affected = result?.counts.affected ?? 0
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
        {result && result.errors > 0 && (
          <ErrorNote>Check failed for {plural(result.errors, 'issue')}; listed as Inconclusive.</ErrorNote>
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
                <span className="count-value">{result.counts[answer] ?? 0}</span>
              </button>
            ))}
          </div>
          <Triage key={tab} result={result} tab={tab} version={version} />
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

function Triage({ result, tab, version }: { result: ScanResponse; tab: Answer; version: string }) {
  const [filter, setFilter] = useState('')
  const [selectedKey, setSelectedKey] = useState<string>()
  const detailRef = useRef<HTMLDivElement>(null)

  const items = useMemo(() => {
    const words = filter.trim().toLowerCase()
    return result.items.filter(
      (i) =>
        i.answer === tab &&
        (!words || `${i.issue_key} ${i.summary}`.toLowerCase().includes(words)),
    )
  }, [result.items, tab, filter])
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
          <IssueDetail key={selected.issue_key} item={selected} pinned={version} />
        ) : (
          <p className="list-empty">Select an issue</p>
        )}
        <RulerKey />
      </section>
    </>
  )
}
