import { api, type Dependency, type SourceCount } from '../api/client'
import { ErrorNote, Fields, Timestamp } from '../components/common'
import { dayStart, formatDay } from '../format'
import { useLoad, useSyncJobs, type WatchItem } from '../hooks'

interface Props {
  items: WatchItem[] // the dependencies the repository runs, at their versions
  dependencies: Dependency[]
  since: string // the scan window, as the Scan step will use it
  scanned: number // goes up after each scan, which changes what is checked
  onSynced: () => void
}

/** Step 2: bring each watched dependency's issues up to date before the scan, and show, per
 * dependency, how many issues in the scan window a scan would still have the model read. */
export function SyncStep({ items, dependencies, since, scanned, onSynced }: Props) {
  const sources = useLoad(() => api.sources(), [])
  const reloadSources = sources.reload
  const sync = useSyncJobs(() => {
    reloadSources()
    onSynced()
  })

  // Only catalog dependencies can be synced; one row per watched version.
  const rows = items
    .map((item) => ({ item, dependency: dependencies.find((d) => d.id === item.dependency) }))
    .filter((r): r is { item: WatchItem; dependency: Dependency } => Boolean(r.dependency))
  const projects = [...new Set(rows.map((r) => r.dependency.project))]
  const idle = projects.filter((p) => !sync.running(p))

  return (
    <section className="widget w-12 sync-step" aria-labelledby="sync-title">
      <div className="sync-head">
        <div>
          <h2 id="sync-title" className="widget-title">
            Sync sources
          </h2>
          <Fields
            className="sync-window"
            items={[['Scan window', since ? `Updated since ${formatDay(dayStart(since)!)}` : 'All issues']]}
          />
        </div>
        <button
          className="primary"
          disabled={idle.length === 0}
          onClick={() => idle.forEach((p) => void sync.start(p))}
        >
          {idle.length === 0 && projects.length > 0 ? 'Syncing…' : 'Sync all'}
        </button>
      </div>

      {rows.length === 0 ? (
        <p className="list-empty">No supported dependencies selected</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th scope="col">Dependency</th>
                <th scope="col">Version</th>
                <th scope="col">Last sync</th>
                <th scope="col" className="num" title="Candidate bugs updated in the scan window">
                  Bugs
                </th>
                <th
                  scope="col"
                  className="num"
                  title="Answered by the fix versions, without a model call"
                >
                  Settled
                </th>
                <th scope="col" className="num" title="Answered from stored evidence">
                  Checked
                </th>
                <th scope="col" className="num" title="Each takes a model call in a scan">
                  Not checked
                </th>
                <th scope="col">
                  <span className="sr-only">Action</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map(({ item, dependency }) => (
                <SyncRow
                  key={`${dependency.id}@${item.version}`}
                  dependency={dependency}
                  version={item.version}
                  source={sources.data?.find((s) => s.project === dependency.project)}
                  since={since}
                  // Reload the counts after a sync or a scan changes them.
                  refresh={`${sync.finished}/${scanned}`}
                  syncing={sync.running(dependency.project)?.progress}
                  onSync={() => void sync.start(dependency.project)}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
      <ErrorNote>{sync.error ?? sources.error}</ErrorNote>
    </section>
  )
}

function SyncRow({
  dependency,
  version,
  source,
  since,
  refresh,
  syncing,
  onSync,
}: {
  dependency: Dependency
  version: string
  source?: SourceCount
  since: string
  refresh: string
  syncing?: number // issues fetched so far, while a sync runs
  onSync: () => void
}) {
  const backlog = useLoad(
    () =>
      dependency.watchable
        ? api.scanBacklog(dependency.project, version, dayStart(since))
        : Promise.resolve(undefined),
    [dependency.project, version, since, refresh],
  )
  const b = backlog.data
  const count = (n?: number) => (n === undefined ? '…' : n.toLocaleString())
  const added = source?.added ?? dependency.added

  return (
    <tr>
      <td className="sync-name">{dependency.name}</td>
      <td>{version}</td>
      <td className="nowrap">
        {syncing !== undefined ? (
          <span className="with-spinner">
            <span className="spinner" aria-hidden="true" />
            Syncing ({syncing.toLocaleString()} fetched)
          </span>
        ) : source?.synced_at ? (
          <Timestamp value={source.synced_at} />
        ) : added ? (
          'Incomplete'
        ) : (
          'Never'
        )}
      </td>
      {dependency.watchable ? (
        backlog.error ? (
          <td colSpan={4} className="note-error">
            {backlog.error}
          </td>
        ) : (
          <>
            <td className="num">{count(b?.candidates)}</td>
            <td className="num">{count(b?.settled)}</td>
            <td className="num">{count(b?.checked)}</td>
            <td className={b && b.unchecked > 0 ? 'num sync-unchecked' : 'num'}>
              {count(b?.unchecked)}
            </td>
          </>
        )
      ) : (
        <td colSpan={4} className="muted">
          Not supported for checks
        </td>
      )}
      <td className="num">
        <button className="btn-sm" onClick={onSync} disabled={syncing !== undefined}>
          {added ? 'Sync' : 'Add and sync'}
        </button>
      </td>
    </tr>
  )
}
