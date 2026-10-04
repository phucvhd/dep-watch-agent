import { useEffect, useMemo, useState } from 'react'
import { api, type Dependency, type ScanResponse } from './api/client'
import { VersionOrder } from './components/versionOrder'
import { formatAgo } from './format'
import { useLoad, useWatch } from './hooks'
import { Alerts } from './pages/Alerts'
import { Check } from './pages/Check'
import { Issues } from './pages/Issues'
import { Operations } from './pages/Operations'

const PAGES = {
  alerts: 'New bugs',
  check: 'Check an issue',
  issues: 'Issues',
  operations: 'Data and models',
} as const
type Page = keyof typeof PAGES

function routeFromHash(): { page: Page; key?: string } {
  const [page, key] = window.location.hash.replace(/^#\/?/, '').split('/')
  return page in PAGES ? { page: page as Page, key } : { page: 'alerts' }
}

export function App() {
  const [route, setRoute] = useState(routeFromHash)
  useEffect(() => {
    const onHash = () => setRoute(routeFromHash())
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  const watch = useWatch()
  const dependencies = useLoad(() => api.dependencies(), [])
  const dependency: Dependency | undefined =
    dependencies.data?.find((d) => d.id === watch.dependency) ?? dependencies.data?.[0]
  const project = dependency?.project ?? ''

  const versions = useLoad(() => (project ? api.versions(project) : Promise.resolve([])), [project])
  const systems = useLoad(() => api.systems(), [])
  const sync = useLoad(() => api.syncState(), [])
  const scans = useLoad(() => api.jobs('scan'), [])

  const order = useMemo(
    () => new Map((versions.data ?? []).map((v, i) => [v.name, i])),
    [versions.data],
  )
  // Released versions, newest first: what someone can actually run.
  const released = useMemo(
    () =>
      (versions.data ?? [])
        .filter((v) => v.released && /^\d+(\.\d+)+$/.test(v.name))
        .reverse(),
    [versions.data],
  )
  const version = watch.version

  // The latest scan of what is watched, for the badge and the New bugs page.
  const latestScan = scans.data?.find(
    (j) => j.params.kafka_version === version && (j.params.project ?? 'KAFKA') === project,
  )
  const affected =
    latestScan?.status === 'succeeded'
      ? ((latestScan.result as unknown as ScanResponse).counts.affected ?? 0)
      : undefined
  const watermark = sync.data?.find((s) => s.source === `jira:${project}`)?.watermark
  const model = systems.data?.[0]

  const apiDown = dependencies.error && !dependencies.data
  return (
    <VersionOrder.Provider value={order}>
      <a className="skip" href="#main">
        Skip to content
      </a>
      <div className="shell">
        <aside className="sidebar">
          <a className="brand" href="#/alerts">
            <svg viewBox="0 0 24 24" aria-hidden="true" className="brand-mark">
              <line x1="2" x2="22" y1="15" y2="15" />
              <circle cx="7" cy="15" r="2.6" />
              <line className="brand-pin" x1="15" x2="15" y1="4" y2="20" />
            </svg>
            dep-watch
          </a>

          <div className="watch" aria-label="What you run">
            <label>
              <span>Dependency</span>
              <select
                value={dependency?.id ?? ''}
                onChange={(e) => watch.setDependency(e.target.value)}
              >
                {dependencies.data?.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Version you run</span>
              <select
                className="version-select"
                value={version}
                onChange={(e) => watch.setVersion(e.target.value)}
              >
                <option value="" disabled>
                  Choose a version
                </option>
                {released.map((v) => (
                  <option key={v.name}>{v.name}</option>
                ))}
              </select>
            </label>
          </div>

          <nav className="nav" aria-label="Pages">
            {(Object.keys(PAGES) as Page[]).map((page) => (
              <a
                key={page}
                href={`#/${page}`}
                aria-current={route.page === page ? 'page' : undefined}
              >
                {PAGES[page]}
                {page === 'alerts' && affected !== undefined && affected > 0 && (
                  <span className="badge" aria-label={`${affected} affect you`}>
                    {affected}
                  </span>
                )}
              </a>
            ))}
          </nav>

          <div className="status">
            <p>
              <span className={model ? 'status-dot' : 'status-dot status-off'} aria-hidden="true" />
              {model ? `Reading with ${model}` : 'No model configured'}
            </p>
            <p>{watermark ? `Issues synced ${formatAgo(watermark)}` : 'Issues not synced yet'}</p>
          </div>
        </aside>

        <main id="main">
          {apiDown ? (
            <div className="page">
              <div className="empty">
                <h2>The API isn't answering</h2>
                <p>{dependencies.error}</p>
              </div>
            </div>
          ) : !dependency ? null : !version && route.page !== 'operations' ? (
            <div className="page">
              <div className="empty">
                <h2>Which {dependency.name} version do you run?</h2>
                <p>
                  Choose it in the sidebar. Every page then answers for that version: which new
                  upstream bugs affect it, and the sentences in each issue that show why.
                </p>
              </div>
            </div>
          ) : route.page === 'alerts' ? (
            <Alerts
              key={`${project}/${version}`}
              dependency={dependency}
              version={version}
              systems={systems.data ?? []}
              latestScanId={latestScan?.id}
              onScanned={scans.reload}
            />
          ) : route.page === 'check' ? (
            <Check
              key={`${version}/${route.key ?? ''}`}
              dependency={dependency}
              version={version}
              initialKey={route.key}
            />
          ) : route.page === 'issues' ? (
            <Issues
              dependency={dependency}
              version={version}
              onCheck={(key) => (window.location.hash = `#/check/${key}`)}
            />
          ) : (
            <Operations dependency={dependency} systems={systems.data ?? []} onSynced={sync.reload} />
          )}
        </main>
      </div>
    </VersionOrder.Provider>
  )
}
