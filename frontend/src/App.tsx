import { useEffect, useMemo, useState } from 'react'
import { api } from './api/client'
import { VersionOrder } from './components/versionOrder'
import { usePinnedVersion, useLoad } from './hooks'
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

function pageFromHash(): { page: Page; key?: string } {
  const [page, key] = window.location.hash.replace(/^#\/?/, '').split('/')
  return page in PAGES ? { page: page as Page, key } : { page: 'alerts' }
}

export function App() {
  const [route, setRoute] = useState(pageFromHash)
  useEffect(() => {
    const onHash = () => setRoute(pageFromHash())
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  const [pinned, setPinned] = usePinnedVersion()
  const versions = useLoad(() => api.versions(), [])
  const systems = useLoad(() => api.systems(), [])

  const order = useMemo(
    () => new Map((versions.data ?? []).map((v, i) => [v.name, i])),
    [versions.data],
  )
  // Newest first, released only: the versions someone can actually run.
  const released = useMemo(
    () => (versions.data ?? []).filter((v) => v.released && /^\d+(\.\d+)+$/.test(v.name)).reverse(),
    [versions.data],
  )

  const apiDown = versions.error && !versions.data
  return (
    <VersionOrder.Provider value={order}>
      <a className="skip" href="#main">
        Skip to content
      </a>
      <header className="masthead">
        <div className="masthead-inner">
          <a className="brand" href="#/alerts">
            dep-watch
            <span className="brand-sub">for Apache Kafka</span>
          </a>
          <nav aria-label="Pages">
            {(Object.keys(PAGES) as Page[]).map((page) => (
              <a key={page} href={`#/${page}`} aria-current={route.page === page ? 'page' : undefined}>
                {PAGES[page]}
              </a>
            ))}
          </nav>
          <label className="pin">
            <span>Your Kafka</span>
            <select value={pinned} onChange={(e) => setPinned(e.target.value)}>
              <option value="" disabled>
                Choose
              </option>
              {released.map((v) => (
                <option key={v.name}>{v.name}</option>
              ))}
            </select>
          </label>
        </div>
      </header>

      <main id="main">
        {apiDown ? (
          <p className="note note-error" role="alert">
            {versions.error}
          </p>
        ) : !pinned && route.page !== 'issues' && route.page !== 'operations' ? (
          <FirstVisit />
        ) : route.page === 'alerts' ? (
          <Alerts key={pinned} pinned={pinned} systems={systems.data ?? []} />
        ) : route.page === 'check' ? (
          <Check key={`${pinned}/${route.key ?? ''}`} pinned={pinned} initialKey={route.key} />
        ) : route.page === 'issues' ? (
          <Issues pinned={pinned} onCheck={(key) => (window.location.hash = `#/check/${key}`)} />
        ) : (
          <Operations systems={systems.data ?? []} />
        )}
      </main>
    </VersionOrder.Provider>
  )
}

function FirstVisit() {
  return (
    <section className="first-visit">
      <h1 className="headline">Which Kafka version do you run?</h1>
      <p className="lede">
        Choose it under Your Kafka, top right. Every page answers for that version: which new
        upstream bugs affect it, with the sentences from each issue that show why.
      </p>
    </section>
  )
}
