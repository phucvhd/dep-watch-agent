import { useEffect, useMemo, useRef, useState } from 'react'
import { api, type Dependency, type DetectedDependency, type RepoScan } from '../api/client'
import { ErrorNote, PageIntro } from '../components/common'
import { plural } from '../format'
import { message, useLoad, type WatchItem } from '../hooks'
import { readRepo } from '../repo'

interface Props {
  dependencies: Dependency[]
  current: WatchItem[]
  onWatch: (repo: string | null, items: WatchItem[]) => void
}

const rowKey = (d: { key: string; version?: string | null }) => `${d.key}@${d.version ?? ''}`

export function Setup({ dependencies, current, onWatch }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [repo, setRepo] = useState<string>()
  const [scan, setScan] = useState<RepoScan>()
  const [skipped, setSkipped] = useState(0)
  const [checked, setChecked] = useState<Set<string>>(new Set())
  const [reading, setReading] = useState(false)
  const [error, setError] = useState<string>()

  // React has no prop for folder picking; the attribute is set directly.
  useEffect(() => {
    inputRef.current?.setAttribute('webkitdirectory', '')
  }, [])

  async function pick(list: FileList | null) {
    if (!list || list.length === 0) return
    setReading(true)
    setError(undefined)
    setScan(undefined)
    try {
      const picked = await readRepo(list)
      setRepo(picked.name)
      setSkipped(picked.skipped)
      const result = await api.scanRepo(picked.files)
      setScan(result)
      // Start from what is already watched, else every dependency that can be.
      const watched = new Set(current.map((w) => `${w.dependency}@${w.version}`))
      const initial = result.dependencies.filter(
        (d) => d.watchable && (watched.size === 0 || watched.has(rowKey(d))),
      )
      setChecked(new Set(initial.map(rowKey)))
    } catch (e) {
      setError(message(e))
    } finally {
      setReading(false)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  const known = useMemo(() => scan?.dependencies.filter((d) => d.family) ?? [], [scan])
  const others = useMemo(() => scan?.dependencies.filter((d) => !d.family) ?? [], [scan])
  const selected = scan?.dependencies.filter((d) => checked.has(rowKey(d))) ?? []

  function toggle(d: DetectedDependency) {
    setChecked((prev) => {
      const next = new Set(prev)
      if (next.has(rowKey(d))) next.delete(rowKey(d))
      else next.add(rowKey(d))
      return next
    })
  }

  function watch() {
    onWatch(
      repo ?? null,
      selected.map((d) => ({ dependency: d.family!, version: d.version!, files: d.files })),
    )
    window.location.assign('#/alerts')
  }

  return (
    <div className="page">
      <PageIntro title="Your repository">
        <p>
          Choose the folder of the project you run. Its build files (Maven, Gradle, sbt, SBOM,
          Compose) are read in this browser; only those files are sent to find the dependencies
          and the versions you use. Your browser asks you to confirm the folder.
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          hidden
          onChange={(e) => void pick(e.target.files)}
        />
        <button className="primary" onClick={() => inputRef.current?.click()} disabled={reading}>
          {reading ? 'Reading…' : scan ? 'Choose another folder' : 'Choose repository folder'}
        </button>
        <ErrorNote>{error}</ErrorNote>
      </PageIntro>

      {scan && (
        <section className="detected" aria-labelledby="detected-title">
          <div className="detected-head">
            <h2 id="detected-title">
              {repo}
              <sup>{scan.dependencies.length}</sup>
            </h2>
            <p>
              Read {plural(scan.files_read.length, 'build file')}
              {skipped > 0 && `; ${plural(skipped, 'file')} left out for size`}. Choose the
              dependencies to watch. Only Apache Kafka can be watched for now; the others are
              listed so you can see what the repository uses.
            </p>
          </div>

          {scan.dependencies.length === 0 ? (
            <p className="list-empty">
              No dependencies found. The folder has no Maven, Gradle, sbt, SBOM or Compose build
              files, or they declare no versions.
            </p>
          ) : (
            <>
              <ul className="dep-list">
                {known.map((d) => (
                  <DependencyRow
                    key={rowKey(d)}
                    d={d}
                    checked={checked.has(rowKey(d))}
                    onToggle={() => toggle(d)}
                  />
                ))}
              </ul>
              {others.length > 0 && (
                <details className="dep-others">
                  <summary>
                    Other dependencies<sup>{others.length}</sup>
                  </summary>
                  <ul className="dep-list dep-list-compact">
                    {others.map((d) => (
                      <DependencyRow key={rowKey(d)} d={d} checked={false} onToggle={() => {}} />
                    ))}
                  </ul>
                </details>
              )}
            </>
          )}

          <div className="detected-actions">
            <button className="primary" onClick={watch} disabled={selected.length === 0}>
              {selected.length === 0
                ? 'Choose a dependency to watch'
                : `Watch ${selected.map((d) => `${d.name} ${d.version}`).join(', ')}`}
            </button>
          </div>
        </section>
      )}

      <ManualAdd dependencies={dependencies} onWatch={onWatch} />
    </div>
  )
}

function DependencyRow({
  d,
  checked,
  onToggle,
}: {
  d: DetectedDependency
  checked: boolean
  onToggle: () => void
}) {
  const id = `dep-${rowKey(d)}`
  return (
    <li className={d.watchable ? 'dep' : 'dep dep-off'}>
      <input
        id={id}
        type="checkbox"
        checked={checked}
        disabled={!d.watchable}
        onChange={onToggle}
      />
      <label htmlFor={id}>
        <span className="dep-name">{d.name}</span>
        <span className="dep-version">{d.version ?? 'version unknown'}</span>
      </label>
      <span className="dep-meta">
        {d.reason ?? plural(d.artifacts.length, 'artifact')}
        <span className="dep-files">{d.files.join(', ')}</span>
      </span>
    </li>
  )
}

/** For a dependency the repository doesn't declare, such as a broker run elsewhere. */
function ManualAdd({
  dependencies,
  onWatch,
}: {
  dependencies: Dependency[]
  onWatch: (repo: string | null, items: WatchItem[]) => void
}) {
  const [dependency, setDependency] = useState(dependencies[0]?.id ?? '')
  const project = dependencies.find((d) => d.id === dependency)?.project ?? ''
  const versions = useLoad(
    () => (project ? api.versions(project) : Promise.resolve([])),
    [project],
  )
  const released = (versions.data ?? [])
    .filter((v) => v.released && /^\d+(\.\d+)+$/.test(v.name))
    .reverse()
  const [version, setVersion] = useState('')

  return (
    <details className="manual">
      <summary>Not in your repository? Add a version by hand</summary>
      <div className="toolbar">
        <label>
          <span>Dependency</span>
          <select value={dependency} onChange={(e) => setDependency(e.target.value)}>
            {dependencies.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>Version</span>
          <select value={version} onChange={(e) => setVersion(e.target.value)}>
            <option value="" disabled>
              Choose
            </option>
            {released.map((v) => (
              <option key={v.name}>{v.name}</option>
            ))}
          </select>
        </label>
        <button
          disabled={!version}
          onClick={() => {
            onWatch(null, [{ dependency, version }])
            window.location.assign('#/alerts')
          }}
        >
          Watch this version
        </button>
      </div>
    </details>
  )
}
