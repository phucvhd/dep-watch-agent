import { useEffect, useMemo, useRef, useState } from 'react'
import { api, type ScanResponse } from './api/client'
import { PageIntro } from './components/common'
import { VersionOrder } from './components/versionOrder'
import { formatAgo } from './format'
import { useLoad, useWatch } from './hooks'
import { Alerts } from './pages/Alerts'
import { Issues } from './pages/Issues'
import { Operations } from './pages/Operations'
import { Setup } from './pages/Setup'

const PAGES = {
  alerts: 'New bugs',
  issues: 'Issues',
  operations: 'Data and models',
} as const
type Page = keyof typeof PAGES | 'setup'

/** The page in the URL, or none (a first visit opens Setup when nothing is watched yet).
 * `#/check/KEY` from before Check was merged into Issues opens that issue. */
function routeFromHash(): { page?: Page; key?: string } {
  const [page, key] = window.location.hash.replace(/^#\/?/, '').split('/')
  if (page === 'check') {
    window.history.replaceState(null, '', `#/issues${key ? `/${key}` : ''}`)
    return { page: 'issues', key }
  }
  return page in PAGES || page === 'setup' ? { page: page as Page, key } : {}
}

export function App() {
  const [hashRoute, setRoute] = useState(routeFromHash)
  useEffect(() => {
    const onHash = () => setRoute(routeFromHash())
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  const watch = useWatch()
  const route = { ...hashRoute, page: hashRoute.page ?? (watch.items.length ? 'alerts' : 'setup') }
  // Where Setup returns to when the change is abandoned.
  const lastPage = useRef<Page>('alerts')
  useEffect(() => {
    if (route.page !== 'setup') lastPage.current = route.page
  }, [route.page])
  const dependencies = useLoad(() => api.dependencies(), [])
  const nameOf = (id: string) => dependencies.data?.find((d) => d.id === id)?.name ?? id
  // The dependency every page answers for: the active watched one, else the first the API
  // supports, so Issues and Data and models work before anything is watched.
  const watched = dependencies.data?.find((d) => d.id === watch.active?.dependency)
  const dependency = watched ?? dependencies.data?.[0]
  const version = watched ? watch.active!.version : ''
  const project = dependency?.project ?? ''

  const versions = useLoad(() => (project ? api.versions(project) : Promise.resolve([])), [project])
  const systems = useLoad(() => api.systems(), [])
  const sync = useLoad(() => api.syncState(), [])
  const scans = useLoad(() => api.jobs('scan'), [])

  const order = useMemo(
    () => new Map((versions.data ?? []).map((v, i) => [v.name, i])),
    [versions.data],
  )

  // The latest scan of what is watched, for the count and the New bugs page.
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
          <div className="sb-section sb-brand">
            <a className="brand" href="#/alerts">
              <svg viewBox="0 0 24 24" aria-hidden="true" className="brand-mark">
                <line x1="2" x2="22" y1="15" y2="15" />
                <circle cx="7" cy="15" r="2.6" />
                <line className="brand-pin" x1="15" x2="15" y1="4" y2="20" />
              </svg>
              dep-watch
            </a>
          </div>

          <nav className="sb-section nav" aria-label="Pages">
            {(Object.keys(PAGES) as (keyof typeof PAGES)[]).map((page) => (
              <a
                key={page}
                href={`#/${page}`}
                aria-current={route.page === page ? 'page' : undefined}
              >
                {PAGES[page]}
                {page === 'alerts' && affected !== undefined && affected > 0 && (
                  <sup aria-label={`, ${affected} affect you`}>{affected}</sup>
                )}
              </a>
            ))}
          </nav>

          <div className="sb-section watch" aria-label="What you run">
            <p className="watch-label">
              {watch.repo ? 'Repository' : watch.items.length ? 'Added by hand' : 'Nothing watched'}
            </p>
            {watch.repo && <p className="watch-repo">{watch.repo}</p>}
            {watch.items.length > 0 && (
              <ul className="watch-items">
                {watch.items.map((item, i) => (
                  <li key={`${item.dependency}@${item.version}`}>
                    <button
                      aria-pressed={i === watch.activeIndex}
                      onClick={() => watch.select(i)}
                      title={item.files?.join(', ')}
                    >
                      <span className="watch-name">{nameOf(item.dependency)}</span>
                      <span className="watch-version">{item.version}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
            <a className="watch-change" href="#/setup" aria-current={route.page === 'setup' ? 'page' : undefined}>
              {watch.items.length ? 'Change' : 'Choose a repository'}
            </a>
          </div>

          <div className="sb-section status">
            <p>
              <span className={model ? 'status-dot' : 'status-dot status-off'} aria-hidden="true" />
              {model ? `Reading with ${model}` : 'No model configured'}
            </p>
            {dependency && (
              <p>
                {watermark
                  ? `${dependency.name} issues synced ${formatAgo(watermark)}`
                  : `${dependency.name} issues not synced yet`}
              </p>
            )}
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
          ) : !dependencies.data || !dependency ? null : route.page === 'setup' ? (
            <Setup
              dependencies={dependencies.data}
              repo={watch.repo}
              current={watch.items}
              nameOf={nameOf}
              onWatch={watch.replace}
              onCancel={
                watch.items.length
                  ? () => window.location.assign(`#/${lastPage.current}`)
                  : undefined
              }
            />
          ) : route.page === 'operations' ? (
            <Operations dependency={dependency} systems={systems.data ?? []} onSynced={sync.reload} />
          ) : route.page === 'alerts' && !version ? (
            <div className="page">
              <PageIntro title="New bugs">
                <p>
                  New bugs are answered for the dependency versions you run. Choose your
                  repository to find them, or add a version by hand.
                </p>
                <a className="button primary" href="#/setup">
                  Choose your repository
                </a>
              </PageIntro>
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
          ) : (
            <Issues
              key={`${project}/${route.key ?? ''}`}
              dependency={dependency}
              version={version}
              systems={systems.data ?? []}
              issueKey={route.key}
            />
          )}
        </main>
      </div>
    </VersionOrder.Provider>
  )
}
