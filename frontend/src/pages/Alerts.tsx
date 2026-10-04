import { useMemo, useRef, useState, type FormEvent } from 'react'
import { api, type Answer, type Dependency, type Job, type ScanResponse } from '../api/client'
import { IssueDetail, IssueRow } from '../components/IssueResult'
import { RulerKey } from '../components/VersionRuler'
import { ErrorNote, JobLine } from '../components/common'
import { ANSWER_TEXT, formatDay, plural } from '../format'
import { isActive, message, useJob } from '../hooks'

const TABS: Answer[] = ['affected', 'insufficient_information', 'not_affected']

const TAB_HINT: Record<Answer, string> = {
  affected: 'The issue shows the bug at your version, unfixed',
  insufficient_information: "The text doesn't say where the bug starts",
  not_affected: 'Fixed in your version, or starts after it',
}

function weekAgo(): string {
  return new Date(Date.now() - 7 * 24 * 3600 * 1000).toISOString().slice(0, 10)
}

interface Props {
  dependency: Dependency
  version: string
  systems: string[]
  latestScanId?: string
  onScanned: () => void
}

/** The dashboard: is the watched version affected by what changed upstream, as widgets. */
export function Alerts({ dependency, version, systems, latestScanId, onScanned }: Props) {
  const [startedId, setStartedId] = useState<string>()
  const { job } = useJob(startedId ?? latestScanId, onScanned)
  const [since, setSince] = useState(weekAgo)
  const [limit, setLimit] = useState(50)
  const [error, setError] = useState<string>()
  const [chosenTab, setTab] = useState<Answer>()

  async function startScan(event: FormEvent) {
    event.preventDefault()
    setError(undefined)
    try {
      const started = await api.startScan({
        kafka_version: version,
        project: dependency.project,
        since: since ? new Date(`${since}T00:00:00Z`).toISOString() : null,
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

  // The status tile's color is the answer: warm when something affects you, cool when nothing
  // does, neutral before a scan.
  const tone = !result ? 'idle' : affected > 0 ? 'hit' : 'calm'
  const headline = running
    ? `Reading new bugs against ${target}.`
    : !result
      ? `Which new bugs affect ${target}?`
      : affected === 0
        ? `Nothing new is shown to affect ${target}.`
        : `${plural(affected, 'bug')} ${affected === 1 ? 'affects' : 'affect'} ${target}.`

  return (
    <div className="dash">
      <section className={`widget w-8 status-tile hero-${tone}`} aria-live="polite">
        <h1 className="hero-line">{headline}</h1>
        {result && (
          <p className="status-sub">
            {plural(result.scanned, 'bug')}
            {result.since ? ` updated since ${formatDay(result.since)}` : ''}, read with{' '}
            {result.system}.
          </p>
        )}
      </section>

      <section className="widget w-4" aria-labelledby="scan-title">
        <h2 id="scan-title" className="widget-title">
          Scan upstream
        </h2>
        <p className="widget-text">
          Bugs the fix versions settle are answered at once; the model reads the rest, 30 to 90
          seconds each the first time, then from stored facts.
        </p>
        <form className="toolbar" onSubmit={startScan}>
          <label>
            <span>Updated since</span>
            <input type="date" value={since} onChange={(e) => setSince(e.target.value)} />
          </label>
          <label>
            <span>At most</span>
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
              j.status === 'queued' ? 'Waiting to start.' : `${plural(j.progress, 'issue')} read so far.`
            }
          />
        )}
        {result && (
          <p className="widget-foot">
            {result.cached > 0 && `${result.cached} answered from stored facts. `}
            {result.candidates_total > result.scanned &&
              `${plural(result.candidates_total - result.scanned, 'more bug')} matched; raise the limit. `}
            {result.errors > 0 && `${plural(result.errors, 'issue')} couldn't be read.`}
          </p>
        )}
      </section>

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
                <span className="count-hint">{TAB_HINT[answer]}</span>
              </button>
            ))}
          </div>
          <Triage key={tab} result={result} tab={tab} version={version} />
        </>
      ) : (
        !running && (
          <section className="widget w-12 empty-tile">
            <h2>No scan of {version} yet</h2>
            <p>
              Scan reads the bugs updated since the day you pick and answers each for {target}.
              The answers show up here, split into what affects you, what can't be told, and what
              doesn't.
            </p>
          </section>
        )
      )}
    </div>
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
            {filter ? 'No issue here matches the filter.' : 'No issue has this answer.'}
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
          <p className="list-empty">Pick an issue to see why.</p>
        )}
        <RulerKey />
      </section>
    </>
  )
}
