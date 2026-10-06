import { useMemo, useState, type FormEvent } from 'react'
import {
  api,
  type Change,
  type Dependency,
  type Job,
  type UpgradeItem,
  type UpgradeResponse,
} from '../api/client'
import { AnswerBody } from '../components/IssueResult'
import { RulerKey } from '../components/VersionRuler'
import { ErrorNote, Fields, JobLine, PageIntro, type Tone } from '../components/common'
import { ANSWER_TEXT, plural } from '../format'
import { isActive, message, useJob, useLoad, type WatchItem } from '../hooks'

const CHANGES: Change[] = ['new_risk', 'exposed', 'remains', 'inconclusive', 'fixed']

/** What each change means, in the direction of the move. */
function changeText(change: Change, direction: UpgradeResponse['direction']): string {
  switch (change) {
    case 'new_risk':
      return 'New risks'
    case 'exposed':
      return direction === 'downgrade' ? 'Fixes given up' : 'No longer ruled out'
    case 'remains':
      return 'Affected at target'
    case 'inconclusive':
      return 'Inconclusive'
    case 'fixed':
      return direction === 'downgrade' ? 'Fixed by downgrading' : 'Fixed by upgrading'
  }
}

interface Props {
  dependencies: Dependency[]
  items: WatchItem[] // what the repository runs: the default "from"
  systems: string[]
}

/** The upgrade question: moving from the version you run to another, what is fixed and what
 * newly affects you. Every answer is the API's; the page only groups them. */
export function Upgrade({ dependencies, items, systems }: Props) {
  const watchable = dependencies.filter((d) => d.watchable)
  const last = useLoad(() => api.jobs('upgrade'), [])
  const [startedId, setStartedId] = useState<string>()
  const jobId = startedId ?? last.data?.[0]?.id
  const { job } = useJob(jobId)
  const result = job?.status === 'succeeded' ? (job.result as unknown as UpgradeResponse) : undefined

  // Warm when anything would affect you at the target, or can no longer be ruled out there.
  const atRisk = (['new_risk', 'exposed', 'remains'] as Change[]).some(
    (c) => (result?.counts[c] ?? 0) > 0,
  )
  const tone: Tone = !result ? 'idle' : atRisk ? 'hit' : 'calm'

  return (
    <div className="dash">
      <PageIntro title="Upgrade" tone={tone} />
      {watchable.length === 0 ? (
        <section className="widget w-12 empty-tile">
          <p>No dependency is supported for checks yet.</p>
        </section>
      ) : (
        <UpgradeForm
          key={`form/${job?.id ?? 'new'}`} // starts from the last diagnosis once it loads
          dependencies={watchable}
          items={items}
          systems={systems}
          lastParams={job?.params}
          running={isActive(job)}
          onStarted={setStartedId}
        />
      )}
      {job && job.status !== 'succeeded' && (
        <div className="w-12">
          <JobLine
            job={job}
            describe={(j: Job) =>
              j.status === 'queued'
                ? 'Queued'
                : `Diagnosing: ${j.progress.toLocaleString()} read by the model`
            }
          />
        </div>
      )}
      {result && <Report key={`report/${job!.id}`} result={result} />}
    </div>
  )
}

function UpgradeForm({
  dependencies,
  items,
  systems,
  lastParams,
  running,
  onStarted,
}: {
  dependencies: Dependency[]
  items: WatchItem[]
  systems: string[]
  lastParams?: Record<string, unknown>
  running: boolean
  onStarted: (id: string) => void
}) {
  const watched = items.find((i) => dependencies.some((d) => d.id === i.dependency))
  // Start from the last diagnosis, else the watched version.
  const str = (key: string) =>
    typeof lastParams?.[key] === 'string' ? (lastParams[key] as string) : undefined
  const [dependencyId, setDependencyId] = useState(
    dependencies.find((d) => d.project === str('project'))?.id ??
      watched?.dependency ??
      dependencies[0].id,
  )
  const dependency = dependencies.find((d) => d.id === dependencyId) ?? dependencies[0]
  const versions = useLoad(() => api.versions(dependency.project), [dependency.project])
  // Release names only (the API orders them, oldest first); the UI never compares versions.
  const releases = useMemo(
    () =>
      (versions.data ?? [])
        .filter((v) => v.released && /^\d+(\.\d+)+$/.test(v.name))
        .map((v) => v.name),
    [versions.data],
  )
  const [from, setFrom] = useState(str('from_version') ?? watched?.version ?? '')
  const [to, setTo] = useState(str('to_version') ?? '')
  const [read, setRead] = useState(
    typeof lastParams?.read === 'number' ? (lastParams.read as number) : 0,
  )
  const [error, setError] = useState<string>()
  const toVersion = to || releases.at(-1) || ''
  const fromVersion = from || releases.at(-2) || ''

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError(undefined)
    try {
      const job = await api.startUpgrade({
        project: dependency.project,
        from_version: fromVersion,
        to_version: toVersion,
        read,
      })
      onStarted(job.id)
    } catch (e) {
      setError(message(e))
    }
  }

  const options = (selected: string) => {
    const names = releases.includes(selected) || !selected ? releases : [...releases, selected]
    return [...names].reverse().map((n) => (
      <option key={n} value={n}>
        {n}
      </option>
    ))
  }

  return (
    <section className="widget w-12" aria-labelledby="upgrade-title">
      <h2 id="upgrade-title" className="widget-title">
        Compare two versions
      </h2>
      <form className="toolbar upgrade-form" onSubmit={submit}>
        {dependencies.length > 1 && (
          <label>
            <span>Dependency</span>
            <select value={dependency.id} onChange={(e) => setDependencyId(e.target.value)}>
              {dependencies.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </label>
        )}
        <label>
          <span>From</span>
          <select value={fromVersion} onChange={(e) => setFrom(e.target.value)}>
            {options(fromVersion)}
          </select>
        </label>
        <label>
          <span>To</span>
          <select value={toVersion} onChange={(e) => setTo(e.target.value)}>
            {options(toVersion)}
          </select>
        </label>
        <label title="Issues without stored evidence to read first; each takes a model call">
          <span>Model reads</span>
          <input
            type="number"
            min={0}
            max={500}
            value={read}
            onChange={(e) => setRead(Number(e.target.value))}
          />
        </label>
        <button
          className="primary"
          type="submit"
          disabled={
            running ||
            !fromVersion ||
            !toVersion ||
            fromVersion === toVersion ||
            (read > 0 && systems.length === 0)
          }
        >
          {running ? 'Diagnosing…' : 'Diagnose'}
        </button>
      </form>
      <ErrorNote>{error ?? versions.error}</ErrorNote>
    </section>
  )
}

function Report({ result }: { result: UpgradeResponse }) {
  const counts = result.counts
  const first = CHANGES.find((c) => (counts[c] ?? 0) > 0) ?? 'new_risk'
  const [tab, setTab] = useState<Change>(first)
  const [filter, setFilter] = useState('')
  const [selectedKey, setSelectedKey] = useState<string>()
  const direction = result.direction === 'upgrade' ? 'Upgrade' : 'Downgrade'

  const shown = useMemo(() => {
    const words = filter.trim().toLowerCase()
    return result.items.filter(
      (i) =>
        i.change === tab &&
        (!words || `${i.issue_key} ${i.summary}`.toLowerCase().includes(words)),
    )
  }, [result.items, tab, filter])
  const selected = shown.find((i) => i.issue_key === selectedKey) ?? shown[0]

  return (
    <>
      <section className="widget w-12" aria-label="Summary">
        <Fields
          className="upgrade-summary"
          items={[
            [direction, `${result.from_version} to ${result.to_version}`],
            ['Releases crossed', result.releases_between.toLocaleString()],
            ['Bugs compared', result.candidates.toLocaleString()],
            ['Not affected at either', (counts.unchanged ?? 0).toLocaleString()],
            ['Not checked', result.unchecked.toLocaleString()],
            ['Read in this run', result.read.toLocaleString()],
          ]}
        />
        {result.unchecked > 0 && (
          <p className="widget-sub upgrade-unchecked">Raise Model reads to check the rest.</p>
        )}
        {result.errors > 0 && (
          <ErrorNote>
            Check failed for {plural(result.errors, 'issue')}; listed as Inconclusive.
          </ErrorNote>
        )}
      </section>

      <div className="w-12 count-tiles upgrade-tiles" role="tablist" aria-label="Changes">
        {CHANGES.map((c) => (
          <button
            key={c}
            role="tab"
            aria-selected={tab === c}
            className={`widget count-tile change-${c}`}
            onClick={() => {
              setTab(c)
              setSelectedKey(undefined)
            }}
          >
            <span className="count-label">{changeText(c, result.direction)}</span>
            <span className="count-value">{(counts[c] ?? 0).toLocaleString()}</span>
          </button>
        ))}
      </div>

      <section
        className="widget w-5 list-widget"
        role="tabpanel"
        aria-label={changeText(tab, result.direction)}
      >
        <div className="widget-head">
          <h2 className="widget-title">
            {changeText(tab, result.direction)}
            <sup>{shown.length}</sup>
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
        {shown.length === 0 ? (
          <p className="list-empty">{filter ? 'No matching issues' : 'No issues'}</p>
        ) : (
          <ul className="rows">
            {shown.map((item) => (
              <li key={item.issue_key}>
                <button
                  className="row"
                  aria-current={item.issue_key === selected?.issue_key ? 'true' : undefined}
                  onClick={() => setSelectedKey(item.issue_key)}
                >
                  <span className="row-key">{item.issue_key}</span>
                  <span className="row-state">
                    {[item.status, item.resolution].filter(Boolean).join(', ') || 'Open'}
                  </span>
                  <span className="row-title">{item.summary}</span>
                  <Transition item={item} result={result} />
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
      <section className="widget w-7 detail-widget">
        {selected ? (
          <UpgradeDetail key={selected.issue_key} item={selected} result={result} />
        ) : (
          <p className="list-empty">Select an issue</p>
        )}
      </section>
    </>
  )
}

/** The two answers side by side: the version you run, then the target. */
function Transition({ item, result }: { item: UpgradeItem; result: UpgradeResponse }) {
  return (
    <span
      className="transition"
      aria-label={`${result.from_version}: ${ANSWER_TEXT[item.current]}; ${result.to_version}: ${ANSWER_TEXT[item.target]}`}
    >
      <span className={`verdict verdict-sm verdict-${item.current}`}>
        {result.from_version} {ANSWER_TEXT[item.current]}
      </span>
      <span className="transition-arrow" aria-hidden="true">
        to
      </span>
      <span className={`verdict verdict-sm verdict-${item.target}`}>
        {result.to_version} {ANSWER_TEXT[item.target]}
      </span>
    </span>
  )
}

function UpgradeDetail({ item, result }: { item: UpgradeItem; result: UpgradeResponse }) {
  return (
    <article className="detail" aria-labelledby={`upgrade-${item.issue_key}`}>
      <header className="detail-head">
        <h2 id={`upgrade-${item.issue_key}`}>{item.summary}</h2>
        <p className="detail-meta">
          <a href={item.url} target="_blank" rel="noreferrer">
            {item.issue_key}
          </a>
          <span>{[item.status, item.resolution].filter(Boolean).join(', ') || 'Open'}</span>
          {item.fix_versions.length > 0 && <span>Fixed in {item.fix_versions.join(', ')}</span>}
        </p>
      </header>
      <Fields
        className="upgrade-answers"
        items={[
          [
            `At ${result.from_version}`,
            <span key="from" className={`verdict verdict-${item.current}`}>
              {ANSWER_TEXT[item.current]}
            </span>,
          ],
          [
            `At ${result.to_version}`,
            <span key="to" className={`verdict verdict-${item.target}`}>
              {ANSWER_TEXT[item.target]}
            </span>,
          ],
          ['Change', changeText(item.change, result.direction)],
        ]}
      />
      {/* The evidence and reason for the target, the version you would run. */}
      <AnswerBody item={{ ...item, answer: item.target }} pinned={result.to_version} />
      <RulerKey />
    </article>
  )
}
