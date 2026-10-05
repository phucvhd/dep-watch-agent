import { useEffect, useMemo, useRef, useState } from 'react'
import { api, type Dependency, type DetectedDependency, type RepoScan } from '../api/client'
import { ErrorNote } from '../components/common'
import { plural } from '../format'
import { message, useLoad, type WatchItem } from '../hooks'
import { readRepo } from '../repo'

interface Props {
  dependencies: Dependency[]
  repo: string | null // what is watched now
  current: WatchItem[]
  nameOf: (dependency: string) => string
  onWatch: (repo: string | null, items: WatchItem[]) => void
  /** Leave Setup with nothing changed. Absent when nothing is watched yet. */
  onCancel?: () => void
}

type Stage =
  | { step: 'idle' }
  | { step: 'picking' } // the browser's folder dialog (and its confirmation) is open
  | { step: 'reading'; found?: number; total?: number }
  | { step: 'finding'; files: number }

const ECOSYSTEMS: [DetectedDependency['ecosystem'], string][] = [
  ['maven', 'Java and Scala libraries'],
  ['pypi', 'Python packages'],
  ['npm', 'npm packages'],
  ['image', 'Container images'],
]

const ECOSYSTEM_TAG: Record<DetectedDependency['ecosystem'], string> = {
  maven: 'Maven',
  pypi: 'PyPI',
  npm: 'npm',
  image: 'image',
}

const rowKey = (d: { key: string; version?: string | null }) => `${d.key}@${d.version ?? ''}`

export function Setup({ dependencies, repo: watchedRepo, current, nameOf, onWatch, onCancel }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [stage, setStage] = useState<Stage>({ step: 'idle' })
  const [repo, setRepo] = useState<string>()
  const [scan, setScan] = useState<RepoScan>()
  const [leftOut, setLeftOut] = useState(0)
  const [checked, setChecked] = useState<Set<string>>(new Set())
  const [error, setError] = useState<string>()

  // Escape leaves Setup with nothing changed, as the Keep button does.
  useEffect(() => {
    if (!onCancel) return
    const onKey = (e: KeyboardEvent) => {
      const typing = e.target instanceof HTMLInputElement || e.target instanceof HTMLSelectElement
      if (e.key === 'Escape' && !typing) onCancel()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onCancel])

  // React has no prop for folder picking, nor for the dialog being dismissed.
  useEffect(() => {
    const input = inputRef.current
    if (!input) return
    input.setAttribute('webkitdirectory', '')
    const cancelled = () => setStage({ step: 'idle' })
    input.addEventListener('cancel', cancelled)
    return () => input.removeEventListener('cancel', cancelled)
  }, [])

  async function pick(list: FileList | null) {
    if (!list || list.length === 0) {
      setStage({ step: 'idle' })
      return
    }
    setStage({ step: 'reading' })
    setError(undefined)
    setScan(undefined)
    try {
      const picked = await readRepo(list, (found, total) =>
        setStage({ step: 'reading', found, total }),
      )
      setRepo(picked.name)
      setLeftOut(picked.leftOut)
      setStage({ step: 'finding', files: picked.files.length })
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
      setStage({ step: 'idle' })
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  const known = useMemo(() => scan?.dependencies.filter((d) => d.family) ?? [], [scan])
  const others = useMemo(() => scan?.dependencies.filter((d) => !d.family) ?? [], [scan])
  const selected = scan?.dependencies.filter((d) => checked.has(rowKey(d))) ?? []
  const busy = stage.step !== 'idle'

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
  }

  return (
    <section className="widget w-12 repo-step" aria-label="Choose the repository">
      <div className="repo-step-head">
        <p className="widget-text">Only the build files leave your browser.</p>
        <input
          ref={inputRef}
          type="file"
          multiple
          hidden
          onChange={(e) => void pick(e.target.files)}
        />
        {onCancel && (
          <p className="current-watch">
            Watching {watchedRepo ? `${watchedRepo}: ` : ''}
            {current.map((w) => `${nameOf(w.dependency)} ${w.version}`).join(', ')}.
          </p>
        )}
        <div className="button-row">
          <button
            className="primary"
            disabled={busy}
            onClick={() => {
              setStage({ step: 'picking' })
              inputRef.current?.click()
            }}
          >
            {busy ? 'Reading…' : scan ? 'Choose another folder' : 'Choose repository folder'}
          </button>
          {onCancel && (
            <button onClick={onCancel} title="Esc">
              Keep watching {current.length === 1 ? `${nameOf(current[0].dependency)} ${current[0].version}` : 'these'}
            </button>
          )}
        </div>
        <ErrorNote>{error}</ErrorNote>
      </div>

      {busy && <Progress stage={stage} />}

      {scan && !busy && (
        <section className="detected" aria-labelledby="detected-title">
          <div className="detected-head">
            <h2 id="detected-title">
              {repo}
              <sup>{scan.dependencies.length}</sup>
            </h2>
            <p>
              Read {plural(scan.files_read.length, 'build file')}
              {leftOut > 0 && `; ${plural(leftOut, 'file')} left out for size`}. Only Apache
              Kafka can be watched for now.
            </p>
          </div>

          {scan.dependencies.length === 0 ? (
            <p className="list-empty">
              No dependencies found in {plural(scan.files_read.length, 'build file')}. Is this the
              project's root folder?
            </p>
          ) : (
            <>
              {known.length > 0 && (
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
              )}
              {ECOSYSTEMS.map(([ecosystem, label]) => {
                const rows = others.filter((d) => d.ecosystem === ecosystem)
                if (rows.length === 0) return null
                return (
                  <details key={ecosystem} className="dep-others">
                    <summary>
                      {label}
                      <sup>{rows.length}</sup>
                    </summary>
                    <ul className="dep-list dep-list-compact">
                      {rows.map((d) => (
                        <DependencyRow key={rowKey(d)} d={d} checked={false} onToggle={() => {}} />
                      ))}
                    </ul>
                  </details>
                )
              })}
            </>
          )}

          <div className="detected-actions button-row">
            <button className="primary" onClick={watch} disabled={selected.length === 0}>
              {selected.length === 0
                ? 'Choose a dependency to watch'
                : `Watch ${selected.map((d) => `${d.name} ${d.version}`).join(', ')}`}
            </button>
            {onCancel && <button onClick={onCancel}>Cancel, keep what I watch</button>}
          </div>
        </section>
      )}

      <ManualAdd dependencies={dependencies.filter((d) => d.watchable)} onWatch={onWatch} />
    </section>
  )
}

function Progress({ stage }: { stage: Stage }) {
  const text =
    stage.step === 'picking'
      ? 'Waiting for the folder. Your browser lists every file in it and asks you to confirm; a large folder takes a moment.'
      : stage.step === 'reading'
        ? stage.found === undefined
          ? 'Reading the folder…'
          : `Found ${plural(stage.found, 'build file')} among ${stage.total?.toLocaleString()} files. Reading them…`
        : stage.step === 'finding'
          ? `Finding dependencies and versions in ${plural(stage.files, 'build file')}…`
          : ''
  const steps = ['picking', 'reading', 'finding']
  const current = steps.indexOf(stage.step)
  return (
    <section className="progress" aria-live="polite" aria-busy="true">
      <div className="progress-bar" aria-hidden="true" />
      <ol className="progress-steps">
        {['Choose the folder', 'Read build files', 'Find dependencies'].map((label, i) => (
          <li
            key={label}
            className={i < current ? 'done' : i === current ? 'current' : undefined}
            aria-current={i === current ? 'step' : undefined}
          >
            {label}
          </li>
        ))}
      </ol>
      <p className="progress-text">{text}</p>
    </section>
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
        <span className="dep-tag">{ECOSYSTEM_TAG[d.ecosystem]}</span>
      </label>
      <span className="dep-meta">
        {d.notes.length > 0 ? d.notes.join('; ') : (d.reason ?? plural(d.artifacts.length, 'artifact'))}
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
          onClick={() => onWatch(null, [{ dependency, version }])}
        >
          Watch this version
        </button>
      </div>
    </details>
  )
}
