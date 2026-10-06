import { useEffect, useState } from 'react'
import {
  api,
  type Dependency,
  type Job,
  type SourceCount,
  type SyncRun,
  type TypeCount,
} from '../api/client'
import { ColumnChart } from '../components/charts'
import { ErrorNote, Fields, PageIntro, Timestamp } from '../components/common'
import { formatDate } from '../format'
import { useLoad, useSyncJobs } from '../hooks'

const DAYS = 30
const TYPES_SHOWN = 6 // the rest fold into Other
const STALE_MS = 60 * 60 * 1000

interface Props {
  dependencies: Dependency[]
  onSynced: () => void
}

/** One source at a time, picked from the catalog: an added one shows its sync and what is new
 * in it; one not added yet offers its first sync. */
export function Sources({ dependencies, onSynced }: Props) {
  const sources = useLoad(() => api.sources(), [])
  const reloadSources = sources.reload
  const sync = useSyncJobs(() => {
    reloadSources()
    onSynced()
  })
  const [picked, setPicked] = useState<string>()
  const { running, finished, start, error } = sync
  // While a sync runs, its source's counts move too.
  useEffect(() => {
    if (!sync.anyRunning) return
    const timer = window.setInterval(reloadSources, 3000)
    return () => window.clearInterval(timer)
  }, [sync.anyRunning, reloadSources])

  const catalog = sources.data ?? []
  const added = catalog.filter((s) => s.added || running(s.project))
  const available = catalog.filter((s) => !added.includes(s))
  const current = catalog.find((s) => s.project === picked) ?? added[0] ?? catalog[0]
  const lastJob = current && sync.latest(current.project)
  const isAdded = current ? added.includes(current) : false

  return (
    <div className="dash">
      <PageIntro title="Sources" />

      {/* One source at a time: the selection is the only list. */}
      <form className="widget w-12 toolbar search-widget" onSubmit={(e) => e.preventDefault()}>
        <label>
          <span>Source</span>
          <select
            className="source-select"
            value={current?.project ?? ''}
            onChange={(e) => setPicked(e.target.value)}
            disabled={!sources.data}
          >
            {added.length > 0 && (
              <optgroup label={`Added (${added.length})`}>
                {added.map((s) => (
                  <option key={s.project} value={s.project}>
                    {s.name}
                  </option>
                ))}
              </optgroup>
            )}
            {available.length > 0 && (
              <optgroup label={`Available (${available.length})`}>
                {available.map((s) => (
                  <option key={s.project} value={s.project}>
                    {s.name}
                  </option>
                ))}
              </optgroup>
            )}
          </select>
        </label>
      </form>
      {sources.error && (
        <div className="w-12">
          <ErrorNote>{sources.error}</ErrorNote>
        </div>
      )}

      {current && !isAdded && (
        <NotAdded
          source={current}
          dependency={dependencies.find((d) => d.id === current.dependency)}
          onAdd={() => void start(current.project, false)}
          error={error}
        />
      )}

      {current && isAdded && (
        <SourceDetail
          key={`${current.project}/${finished}`}
          source={current}
          dependency={dependencies.find((d) => d.id === current.dependency)}
          job={running(current.project)}
          lastJob={lastJob}
          onSync={(full) => start(current.project, full)}
          error={error}
        />
      )}
    </div>
  )
}

/** A supported source not added yet: adding it is its first sync, which fetches every issue. */
function NotAdded({
  source,
  dependency,
  onAdd,
  error,
}: {
  source: SourceCount
  dependency?: Dependency
  onAdd: () => void
  error?: string
}) {
  return (
    <section className="widget w-12 source-head" aria-labelledby="source-title">
      <div className="source-head-top">
        <SourceTitle source={source} dependency={dependency} />
        <button className="primary" onClick={onAdd}>
          Add and sync
        </button>
      </div>
      <Fields
        className="source-facts"
        items={[
          ['Status', 'Not added'],
          ['First sync', 'All issues in the project'],
          ['Estimated duration', 'Up to 1 hour for large projects'],
        ]}
      />
      <ErrorNote>{error}</ErrorNote>
    </section>
  )
}

function SourceTitle({ source, dependency }: { source: SourceCount; dependency?: Dependency }) {
  return (
    <div>
      <h2 id="source-title" className="source-title">
        {source.name}
      </h2>
      <p className="widget-sub">
        {dependency ? (
          <a href={dependency.tracker_url} target="_blank" rel="noreferrer">
            JIRA project {source.project}
          </a>
        ) : (
          `JIRA project ${source.project}`
        )}
      </p>
    </div>
  )
}

function SourceDetail({
  source,
  dependency,
  job,
  lastJob,
  onSync,
  error,
}: {
  source: SourceCount
  dependency?: Dependency
  job?: Job
  lastJob?: Job
  onSync: (full: boolean) => void
  error?: string
}) {
  const activity = useLoad(() => api.activity(source.project, DAYS), [source.project])
  const runs = useLoad(() => api.syncRuns(source.project), [source.project])
  const [confirmFull, setConfirmFull] = useState(false)
  const [openedAt] = useState(() => Date.now()) // remounted after each sync, so it stays fresh
  const a = activity.data
  const last = runs.data?.[0]
  const resolved = a?.days.reduce((sum, d) => sum + d.resolved, 0) ?? 0
  // The counts cover what has been synced: a day-old sync shows no issues from today.
  const stale = !job && source.synced_at && openedAt - Date.parse(source.synced_at) > STALE_MS
  const types = a ? foldTypes(a.by_type) : []

  return (
    <>
      <section className="widget w-12 source-head" aria-labelledby="source-title">
        <div className="source-head-top">
          <SourceTitle source={source} dependency={dependency} />
          <div className="button-row">
            <button className="primary" onClick={() => onSync(false)} disabled={Boolean(job)}>
              {job ? 'Syncing…' : 'Sync now'}
            </button>
            {!job && !confirmFull && (
              <button onClick={() => setConfirmFull(true)}>Full re-sync</button>
            )}
          </div>
        </div>

        {confirmFull && !job && (
          <div className="confirm" role="group" aria-label="Confirm full re-sync">
            <Fields
              items={[
                ['Full re-sync', `All ${source.issues.toLocaleString()} issues fetched again`],
                ['Estimated duration', 'Up to 1 hour for large projects'],
                ['When to use', 'Issues missing or out of date'],
              ]}
            />
            <div className="button-row">
              <button
                className="primary"
                onClick={() => {
                  setConfirmFull(false)
                  onSync(true)
                }}
              >
                Start full re-sync
              </button>
              <button onClick={() => setConfirmFull(false)}>Cancel</button>
            </div>
          </div>
        )}

        <Fields
          className="source-facts"
          items={[
            ['Issues synced', source.issues.toLocaleString()],
            ['Bugs', source.bugs.toLocaleString()],
            ['Open bugs', source.open_bugs.toLocaleString()],
          ]}
        />
        <div aria-live="polite">
          {job ? (
            <Fields
              className="source-facts"
              items={[
                [
                  'Status',
                  <span key="status" className="with-spinner">
                    <span className="spinner" aria-hidden="true" />
                    {job.status === 'queued' ? 'Queued' : job.params.full ? 'Full re-sync running' : 'Syncing'}
                  </span>,
                ],
                ['Issues fetched', job.progress.toLocaleString()],
              ]}
            />
          ) : (
            <Fields
              className="source-facts"
              items={[
                [
                  'Last sync',
                  last ? (
                    <Timestamp key="last" value={last.finished_at} />
                  ) : source.synced_at ? (
                    <Timestamp key="watermark" value={source.synced_at} />
                  ) : (
                    'Never'
                  ),
                ],
                ['Issues fetched', last?.fetched.toLocaleString()],
                ['New issues', last?.new_issues.toLocaleString()],
                // A success is the expected case; only a failure is worth a field of its own.
                ['Result', last?.status === 'failed' ? 'Failed' : null],
              ]}
            />
          )}
        </div>
        <ErrorNote>
          {error ?? (lastJob?.status === 'failed' && !job ? `Sync failed: ${lastJob.error}` : '')}
        </ErrorNote>
      </section>

      {stale && (
        <p className="w-12 note stale-note">
          <span>
            Data as of the last sync: <Timestamp value={source.synced_at!} />
          </span>
          <button className="btn-sm" onClick={() => onSync(false)}>
            Sync now
          </button>
        </p>
      )}

      <div className="w-12 stat-tiles source-tiles" aria-label={`What is new in ${source.name}`}>
        {(
          [
            ['New', '24 hours', a?.new_24h],
            ['New', '7 days', a?.new_7d],
            ['New', '30 days', a?.new_30d],
            ['Resolved', '30 days', a ? resolved : undefined],
          ] as const
        ).map(([label, period, value]) => (
          <div key={`${label} ${period}`} className="widget stat-tile">
            {/* The measure on the left, the period it covers on the right. */}
            <span className="count-label count-label-split">
              <span>{label}</span>
              <span className="count-period">{period}</span>
            </span>
            <span className="count-value">{value === undefined ? '…' : value.toLocaleString()}</span>
          </div>
        ))}
      </div>

      <section className="widget w-8">
        {a ? (
          <ColumnChart
            title="New issues per day"
            note={`Last ${DAYS} days`}
            categories={a.days.map((d) =>
              new Date(`${d.day}T00:00:00Z`).toLocaleDateString(undefined, {
                month: 'short',
                day: 'numeric',
                timeZone: 'UTC',
              }),
            )}
            categoryLabel="Day"
            series={[
              { key: 'bugs', label: 'Bugs', color: 'var(--accent)', values: a.days.map((d) => d.bugs) },
              {
                key: 'other',
                label: 'Other issues',
                color: 'var(--accent-light)',
                values: a.days.map((d) => d.created - d.bugs),
              },
            ]}
            height={220}
          />
        ) : (
          <p className="list-empty">{activity.error ?? 'Loading…'}</p>
        )}
      </section>

      <section className="widget w-4" aria-labelledby="types-title">
        <div className="widget-title-row">
          <h2 id="types-title" className="widget-title">
            New issues by type
          </h2>
          <span className="count-period">{DAYS} days</span>
        </div>
        {types.length > 0 ? (
          <ul className="type-bars">
            {types.map((t) => (
              <li key={t.issue_type}>
                <span className="type-name">{t.issue_type}</span>
                <span className="type-count">{t.count.toLocaleString()}</span>
                <span className="type-bar" aria-hidden="true">
                  <span style={{ width: `${(t.count / Math.max(...types.map((x) => x.count))) * 100}%` }} />
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="list-empty">{a ? `No new issues in the last ${DAYS} days` : 'Loading…'}</p>
        )}
      </section>

      <section className="widget w-12" aria-labelledby="history-title">
        <h2 id="history-title" className="widget-title">
          Sync history
        </h2>
        {runs.data && runs.data.length > 0 ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th scope="col">Started</th>
                  <th scope="col">Kind</th>
                  <th scope="col" className="num">
                    Duration
                  </th>
                  <th scope="col" className="num">
                    Issues fetched
                  </th>
                  <th scope="col" className="num">
                    New issues
                  </th>
                  <th scope="col">Result</th>
                </tr>
              </thead>
              <tbody>
                {runs.data.map((r, i) => (
                  <tr key={i}>
                    <td className="nowrap">{formatDate(r.started_at)}</td>
                    <td>{r.full ? 'Full' : 'Incremental'}</td>
                    <td className="num">{duration(r)}</td>
                    <td className="num">{r.fetched.toLocaleString()}</td>
                    <td className="num">{r.new_issues.toLocaleString()}</td>
                    <td>
                      <span className={`job-status job-${r.status}`}>
                        {r.status === 'succeeded' ? 'Succeeded' : 'Failed'}
                      </span>
                      {r.error && <span className="muted"> {r.error}</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="list-empty">
            {runs.error ?? 'No sync history'}
          </p>
        )}
      </section>
    </>
  )
}

/** The most common types, and the rest as one Other row at the end. */
function foldTypes(types: TypeCount[]): TypeCount[] {
  if (types.length <= TYPES_SHOWN + 1) return types
  const rest = types.slice(TYPES_SHOWN).reduce((sum, t) => sum + t.count, 0)
  return [...types.slice(0, TYPES_SHOWN), { issue_type: 'Other', count: rest }]
}

function duration(run: SyncRun): string {
  const s = Math.round((Date.parse(run.finished_at) - Date.parse(run.started_at)) / 1000)
  if (s < 60) return `${s} s`
  const m = Math.round(s / 60)
  return m < 60 ? `${m} min` : `${Math.floor(m / 60)} h ${m % 60} min`
}
