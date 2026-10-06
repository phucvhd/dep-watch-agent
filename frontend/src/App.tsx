import { useEffect, useMemo, useState } from 'react'
import { api, type ScanResponse } from './api/client'
import { VersionOrder } from './components/versionOrder'
import { formatAgoShort } from './format'
import { useLoad, useWatch } from './hooks'
import { Dashboard } from './pages/Dashboard'
import { Operations } from './pages/Operations'
import { Sources } from './pages/Sources'
import { Upgrade } from './pages/Upgrade'
import { useTheme, type ThemeChoice } from './theme'
import { ScanFlow } from './pages/ScanFlow'

// The pages, in the order of the flow: scan your repository, the database's numbers, where
// the issues come from, and the models that read them.
const PAGES = {
  scan: 'Scan',
  upgrade: 'Upgrade',
  dashboard: 'Dashboard',
  sources: 'Sources',
  operations: 'Models',
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
  const theme = useTheme()
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
              DWatcher
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
              {watch.repo ? 'Repository' : watch.items.length ? 'Added manually' : 'No repository selected'}
            </p>
            {watch.repo && <p className="watch-repo">{watch.repo}</p>}
            <a className="watch-change" href="#/scan/edit">
              {watch.items.length ? 'Change' : 'Select repository'}
            </a>
          </div>

          <div className="sb-section theme" role="group" aria-label="Theme">
            <p className="watch-label">Theme</p>
            <div className="theme-switch">
              {(['system', 'light', 'dark'] as ThemeChoice[]).map((choice) => (
                <button
                  key={choice}
                  aria-pressed={theme.choice === choice}
                  onClick={() => theme.choose(choice)}
                >
                  {choice === 'system' ? 'System' : choice === 'light' ? 'Light' : 'Dark'}
                </button>
              ))}
            </div>
          </div>

          <div className="sb-section status">
            <p
              title={[
                model ? `Model: ${model}` : 'No model configured',
                watermark && `Last sync: ${new Date(watermark).toLocaleString()}`,
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
                <h2>The API is not responding</h2>
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
              onSynced={() => {
                sync.reload()
                dependencies.reload()
              }}
              editing={route.key === 'edit'}
              tone={affected === undefined ? 'idle' : affected > 0 ? 'hit' : 'calm'}
            />
          ) : route.page === 'dashboard' ? (
            <Dashboard
              key={`dashboard/${route.key ?? ''}`}
              dependencies={dependencies.data}
              watched={watched}
              version={version}
              repo={watch.repo}
              systems={systems.data ?? []}
              issueKey={route.key}
            />
          ) : route.page === 'upgrade' ? (
            <Upgrade
              dependencies={dependencies.data}
              items={watch.items}
              systems={systems.data ?? []}
            />
          ) : route.page === 'sources' ? (
            <Sources
              dependencies={dependencies.data}
              onSynced={() => {
                sync.reload()
                dependencies.reload() // a first sync adds a source
              }}
            />
          ) : (
            <Operations dependency={watched ?? dependencies.data[0]} systems={systems.data ?? []} />
          )}
        </main>
      </div>
    </VersionOrder.Provider>
  )
}
