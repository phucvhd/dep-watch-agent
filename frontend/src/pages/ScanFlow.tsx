import { useState } from 'react'
import type { Dependency } from '../api/client'
import { PageIntro, StepHead } from '../components/common'
import type { WatchItem } from '../hooks'
import { Alerts } from './Alerts'
import { Setup } from './Setup'

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
  /** Open step 1 for editing (the sidebar's Change, or an old #/setup link). */
  editing?: boolean
}

/** The flow, top to bottom: 1 choose the repository, 2 scan, 3 the results. */
export function ScanFlow(props: Props) {
  const { dependencies, repo, items, activeIndex, nameOf, onSelect, onWatch } = props
  const [editing, setEditing] = useState(props.editing || items.length === 0)
  const active = items[activeIndex]
  const dependency = dependencies.find((d) => d.id === active?.dependency)

  return (
    <div className="dash">
      <PageIntro title="Scan" />

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
            <p className="repo-summary-label">{repo ? 'Repository' : 'Added by hand'}</p>
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

      {dependency && active ? (
        <Alerts
          key={`${dependency.project}/${active.version}`}
          dependency={dependency}
          version={active.version}
          systems={props.systems}
          latestScanId={props.latestScanId}
          onScanned={props.onScanned}
        />
      ) : (
        <>
          <StepHead n={2} title="Scan" muted />
          <StepHead n={3} title="Results" muted />
        </>
      )}
    </div>
  )
}
