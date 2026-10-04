import { useMemo, useRef, useState, type FormEvent } from 'react'
import { api, type Answer, type Dependency, type Job, type ScanResponse } from '../api/client'
import { IssueDetail, IssueRow } from '../components/IssueResult'
import { RulerKey } from '../components/VersionRuler'
import { ErrorNote, JobLine } from '../components/common'
import { ANSWER_TEXT, formatDay, plural } from '../format'
import { isActive, message, useJob } from '../hooks'

const TABS: Answer[] = ['affected', 'insufficient_information', 'not_affected']

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

  // The hero is the status: warm when something affects you, cool when nothing does.
  const tone = !result ? 'idle' : affected > 0 ? 'hit' : 'calm'
  const headline = running
    ? `Reading new bugs against ${target}.`
    : !result
      ? `Which new bugs affect ${target}?`
      : affected === 0
        ? `Nothing new is shown to affect ${target}.`
        : `${plural(affected, 'bug')} ${affected === 1 ? 'affects' : 'affect'} ${target}.`

  return (
    <div className="page">
      <section className={`hero hero-${tone}`} aria-live="polite">
        <h1 className="hero-line">{headline}</h1>
      </section>

      <div className="intro">
        {result ? (
          <div className="answer-tabs" role="tablist" aria-label="Answers">
            {TABS.map((answer) => (
              <button
                key={answer}
                role="tab"
                aria-selected={tab === answer}
                className={`answer-tab answer-tab-${answer}`}
                onClick={() => setTab(answer)}
              >
                {ANSWER_TEXT[answer]}
                <sup>{result.counts[answer] ?? 0}</sup>
              </button>
            ))}
          </div>
        ) : (
          <h2 className="intro-title">New bugs</h2>
        )}
        <div className="intro-text">
          {result ? (
            <p>
              Read {plural(result.scanned, 'bug')}
              {result.since ? ` updated since ${formatDay(result.since)}` : ''} with{' '}
              {result.system}
              {result.cached > 0 ? `, ${result.cached} of them from stored facts` : ''}.
              {result.candidates_total > result.scanned &&
                ` ${plural(result.candidates_total - result.scanned, 'more bug')} matched; raise the limit to read them.`}
              {result.errors > 0 && ` ${plural(result.errors, 'issue')} couldn't be read.`}
            </p>
          ) : (
            <p>
              A scan reads the bugs filed or updated upstream since the day you pick and answers
              each for {target}. Bugs the fix versions settle are answered at once; the model reads
              the rest, 30 to 90 seconds each the first time.
            </p>
          )}
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
            <ErrorNote>
              No model is configured, so issue text can't be read. Set DEP_WATCH_LLM_MODEL and
              restart the API.
            </ErrorNote>
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
        </div>
      </div>

      {result && <Triage key={tab} result={result} tab={tab} version={version} />}
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
    <div className="split" role="tabpanel" aria-label={ANSWER_TEXT[tab]}>
      <div className="list-pane">
        <input
          className="filter"
          type="search"
          placeholder="Filter by key or title"
          aria-label="Filter issues"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        />
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
      </div>
      <div className="detail-pane" ref={detailRef}>
        {selected && <IssueDetail key={selected.issue_key} item={selected} pinned={version} />}
        <RulerKey />
      </div>
    </div>
  )
}
