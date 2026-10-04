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

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>New bugs</h1>
          <p className="page-sub">
            Bugs filed or updated upstream, answered for {dependency.name} {version}.
          </p>
        </div>
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
      </header>

      {systems.length === 0 && (
        <ErrorNote>
          No model is configured, so issue text can't be read. Set DEP_WATCH_LLM_MODEL and restart
          the API.
        </ErrorNote>
      )}
      <ErrorNote>{error}</ErrorNote>
      {job && job.status !== 'succeeded' && (
        <JobLine
          job={job}
          describe={(j: Job) =>
            j.status === 'queued'
              ? 'Waiting to start.'
              : `${plural(j.progress, 'issue')} read. New issues take the model 30 to 90 seconds each; known ones come from stored facts.`
          }
        />
      )}

      {result ? (
        <Triage result={result} dependency={dependency} version={version} />
      ) : (
        !job && (
          <div className="empty">
            <h2>No scan of {version} yet</h2>
            <p>
              Scan reads the bugs updated since the date you pick and answers each for{' '}
              {version}. Bugs the fix versions settle are answered at once.
            </p>
          </div>
        )
      )}
    </div>
  )
}

function Triage({
  result,
  dependency,
  version,
}: {
  result: ScanResponse
  dependency: Dependency
  version: string
}) {
  const counts = result.counts
  const [tab, setTab] = useState<Answer>(() =>
    (counts.affected ?? 0) > 0 ? 'affected' : 'insufficient_information',
  )
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

  const affected = counts.affected ?? 0
  const more = result.candidates_total - result.scanned
  return (
    <>
      <section className="summary" aria-live="polite">
        <p className="summary-line">
          {affected === 0
            ? `Nothing new is shown to affect ${dependency.name} ${version}.`
            : `${plural(affected, 'bug')} ${affected === 1 ? 'affects' : 'affect'} ${dependency.name} ${version}.`}
        </p>
        <p className="summary-detail">
          Read {plural(result.scanned, 'bug')}
          {result.since ? ` updated since ${formatDay(result.since)}` : ''} with {result.system}
          {result.cached > 0 ? `, ${result.cached} from stored facts` : ''}.
          {more > 0 && ` ${plural(more, 'more bug')} matched; raise the limit to read them.`}
          {result.errors > 0 && ` ${plural(result.errors, 'issue')} couldn't be read.`}
        </p>
      </section>

      <div className="tabs-bar">
        <div className="tabs" role="tablist" aria-label="Answers">
          {TABS.map((answer) => (
            <button
              key={answer}
              role="tab"
              aria-selected={tab === answer}
              className={`tab tab-${answer}`}
              onClick={() => {
                setTab(answer)
                setSelectedKey(undefined)
              }}
            >
              {ANSWER_TEXT[answer]}
              <span className="tab-count">{counts[answer] ?? 0}</span>
            </button>
          ))}
        </div>
        <input
          className="filter"
          type="search"
          placeholder="Filter by key or title"
          aria-label="Filter issues"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        />
      </div>

      <div className="split" role="tabpanel" aria-label={ANSWER_TEXT[tab]}>
        <div className="list-pane">
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
    </>
  )
}
