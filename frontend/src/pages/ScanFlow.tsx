import { useState } from 'react'
import type { Dependency } from '../api/client'
import { PageIntro, StepHead, type Tone } from '../components/common'
import type { WatchItem } from '../hooks'
import { daysAgo } from '../format'
import { Alerts } from './Alerts'
import { Setup } from './Setup'
import { SyncStep } from './SyncStep'

interface Props {
  dependencies: Dependency[]
  repo: string | null
  items: WatchItem[]
  activeIndex: number
  nameOf: (id: string) => string
  onSelect: (index: number) => void
  onWatch: (repo: string | null, items: WatchItem[]) => void
  systems: string[]
  latestScanId?: string
  onScanned: () => void
  onSynced: () => void
  /** Open step 1 for editing (the sidebar's Change, or an old #/setup link). */
  editing?: boolean
  tone: Tone
}

/** The flow, top to bottom: 1 choose the repository, 2 sync its dependencies' issues, 3 scan,
 * 4 the results. Steps 2 and 3 share the scan window. */
export function ScanFlow(props: Props) {
  const { dependencies, repo, items, activeIndex, nameOf, onSelect, onWatch } = props
  const [editing, setEditing] = useState(props.editing || items.length === 0)
  const active = items[activeIndex]
  const dependency = dependencies.find((d) => d.id === active?.dependency)
  const [since, setSince] = useState(() => daysAgo(7))
  const [scanned, setScanned] = useState(0) // a finished scan changes what is checked

  return (
    <div className="dash">
      <PageIntro title="Scan" tone={props.tone} />

      <StepHead n={1} title="Repository" />
      {editing ? (
        <Setup
          dependencies={dependencies}
          repo={repo}
          current={items}
          nameOf={nameOf}
          onWatch={(r, next) => {
            onWatch(r, next)
            setEditing(false)
          }}
          onCancel={items.length ? () => setEditing(false) : undefined}
        />
      ) : (
        <section className="widget w-12 repo-summary" aria-label="The repository you run">
          <div>
            <p className="repo-summary-label">{repo ? 'Repository' : 'Added manually'}</p>
            <p className="repo-summary-name">{repo ?? 'No repository'}</p>
          </div>
          <ul className="repo-deps">
            {items.map((item, i) => (
              <li key={`${item.dependency}@${item.version}`}>
                <button aria-pressed={i === activeIndex} onClick={() => onSelect(i)}>
                  <span className="watch-name">{nameOf(item.dependency)}</span>
                  <span className="watch-version">{item.version}</span>
                </button>
              </li>
            ))}
          </ul>
          <button onClick={() => setEditing(true)}>Change</button>
        </section>
      )}

      <StepHead n={2} title="Sync" muted={items.length === 0} />
      {items.length > 0 && (
        <SyncStep
          items={items}
          dependencies={dependencies}
          since={since}
          scanned={scanned}
          onSynced={props.onSynced}
        />
      )}

      {dependency && active ? (
        <Alerts
          key={`${dependency.project}/${active.version}`}
          dependency={dependency}
          version={active.version}
          systems={props.systems}
          latestScanId={props.latestScanId}
          onScanned={() => {
            setScanned((n) => n + 1)
            props.onScanned()
          }}
          since={since}
          onSince={setSince}
        />
      ) : (
        <>
          <StepHead n={3} title="Scan" muted />
          <StepHead n={4} title="Results" muted />
        </>
      )}
    </div>
  )
}
