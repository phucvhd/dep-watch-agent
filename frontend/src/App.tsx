import { useEffect, useMemo, useState } from 'react'
import { api, type ScanResponse } from './api/client'
import { VersionOrder } from './components/versionOrder'
import { formatAgoShort } from './format'
import { useLoad, useWatch } from './hooks'
import { Dashboard } from './pages/Dashboard'
import { Operations } from './pages/Operations'
import { ScanFlow } from './pages/ScanFlow'

// The pages, in the order of the flow: scan your repository, then the database's numbers.
const PAGES = {
  scan: 'Scan',
  dashboard: 'Dashboard',
  operations: 'Data and models',
} as const
type Page = keyof typeof PAGES

/** The page in the URL; Scan by default. Links from before the pages were reorganized
 * (#/alerts, #/setup, #/issues/KEY, #/check/KEY) are rewritten to where that content lives. */
function routeFromHash(): { page: Page; key?: string } {
  const [page, key] = window.location.hash.replace(/^#\/?/, '').split('/')
  const legacy: Record<string, [Page, string | undefined]> = {
    alerts: ['scan', undefined],
    setup: ['scan', 'edit'],
    issues: ['dashboard', key],
    check: ['dashboard', key],
  }
  if (page in legacy) {
    const [to, toKey] = legacy[page]
    window.history.replaceState(null, '', `#/${to}${toKey ? `/${toKey}` : ''}`)
    return { page: to, key: toKey }
  }
  return page in PAGES ? { page: page as Page, key } : { page: 'scan' }
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
  const nameOf = (id: string) => dependencies.data?.find((d) => d.id === id)?.name ?? id
  // A watch item without a dependency (a shared link with only a version) means the first one
  // the API can answer for.
  const watched = watch.active
    ? dependencies.data?.find((d) =>
        watch.active!.dependency ? d.id === watch.active!.dependency : d.watchable,
      )
    : undefined
  const version = watched ? watch.active!.version : ''
  const project = (watched ?? dependencies.data?.[0])?.project ?? ''

  const versions = useLoad(() => (project ? api.versions(project) : Promise.resolve([])), [project])
  const systems = useLoad(() => api.systems(), [])
  const sync = useLoad(() => api.syncState(), [])
  const scans = useLoad(() => api.jobs('scan'), [])

  const order = useMemo(
    () => new Map((versions.data ?? []).map((v, i) => [v.name, i])),
    [versions.data],
  )

  // The latest scan of what is watched, for the count beside Scan and the Scan page.
  const latestScan = scans.data?.find(
    (j) => j.params.version === version && j.params.project === project,
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
          <div className="sb-section sb-brand">
            <a className="brand" href="#/scan">
              <svg viewBox="0 0 24 24" aria-hidden="true" className="brand-mark">
                <line x1="2" x2="22" y1="15" y2="15" />
                <circle cx="7" cy="15" r="2.6" />
                <line className="brand-pin" x1="15" x2="15" y1="4" y2="20" />
              </svg>
              dep-watch
            </a>
          </div>

          <nav className="sb-section nav" aria-label="Pages">
            {(Object.keys(PAGES) as Page[]).map((page) => (
              <a
                key={page}
                href={`#/${page}`}
                aria-current={route.page === page ? 'page' : undefined}
              >
                {PAGES[page]}
                {page === 'scan' && affected !== undefined && affected > 0 && (
                  <sup aria-label={`, ${affected} affect you`}>{affected}</sup>
                )}
              </a>
            ))}
          </nav>

          <div className="sb-section watch" aria-label="Your repository">
            <p className="watch-label">
              {watch.repo ? 'Repository' : watch.items.length ? 'Added by hand' : 'No repository yet'}
            </p>
            {watch.repo && <p className="watch-repo">{watch.repo}</p>}
            <a className="watch-change" href="#/scan/edit">
              {watch.items.length ? 'Change' : 'Choose a repository'}
            </a>
          </div>

          <div className="sb-section status">
            <p
              title={[
                model ? `Issues are read with ${model}` : 'No model configured',
                watermark && `issues synced ${new Date(watermark).toLocaleString()}`,
              ]
                .filter(Boolean)
                .join('; ')}
            >
              <span className={model ? 'status-dot' : 'status-dot status-off'} aria-hidden="true" />
              {model ?? 'No model'}
              {watermark && <span className="status-ago">({formatAgoShort(watermark)})</span>}
            </p>
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
          ) : !dependencies.data ? null : route.page === 'scan' ? (
            <ScanFlow
              key={`scan/${route.key ?? ''}`}
              dependencies={dependencies.data}
              repo={watch.repo}
              items={watch.items}
              activeIndex={watch.activeIndex}
              nameOf={nameOf}
              onSelect={watch.select}
              onWatch={watch.replace}
              systems={systems.data ?? []}
              latestScanId={latestScan?.id}
              onScanned={scans.reload}
              editing={route.key === 'edit'}
              tone={affected === undefined ? 'idle' : affected > 0 ? 'hit' : 'calm'}
            />
          ) : route.page === 'dashboard' ? (
            <Dashboard
              key={`dashboard/${route.key ?? ''}`}
              dependencies={dependencies.data}
              watched={watched}
              version={version}
              systems={systems.data ?? []}
              issueKey={route.key}
            />
          ) : (
            <Operations
              dependency={watched ?? dependencies.data[0]}
              systems={systems.data ?? []}
              onSynced={sync.reload}
            />
          )}
        </main>
      </div>
    </VersionOrder.Provider>
  )
}
