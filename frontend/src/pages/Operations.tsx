import { useEffect, useRef, useState } from 'react'
import { api, type Dependency, type EvalRunSummary, type Job } from '../api/client'
import { ColumnChart } from '../components/charts'
import { ErrorNote, JobLine, PageIntro } from '../components/common'
import { formatAgo, formatDate, plural } from '../format'
import { isActive, message, useJob, useLoad } from '../hooks'

const METRICS: [string, string][] = [
  ['macro_f1', 'Macro F1'],
  ['accuracy', 'Accuracy'],
  ['precision', 'Precision'],
  ['recall', 'Recall'],
  ['abstention_rate', 'Abstains'],
  ['citation_validity', 'Valid quotes'],
]

interface Props {
  dependency: Dependency
  systems: string[]
  onSynced: () => void
}

export function Operations({ dependency, systems, onSynced }: Props) {
  return (
    <div className="dash">
      <PageIntro title="Data and models" />
      <Sync onSynced={onSynced} />
      <Models systems={systems} />
      <Facts dependency={dependency} />
      <ReadingTimeChart dependency={dependency} />
      <Evaluation systems={systems} />
      <Jobs />
    </div>
  )
}

const SOURCE_COLOR: Record<string, string> = {
  kafka: 'var(--src-kafka)',
  spark: 'var(--src-spark)',
  hadoop: 'var(--src-hadoop)',
}

/** Every synced source: its issues, when it was last synced, and a sync of its own. */
function Sync({ onSynced }: { onSynced: () => void }) {
  const sources = useLoad(() => api.sources(), [])
  const jobs = useLoad(() => api.jobs('sync-jira'), [])
  const [error, setError] = useState<string>()
  const running = (project: string) =>
    jobs.data?.find((j) => j.params.project === project && isActive(j))

  // While a sync runs, follow it; when it ends, refresh the counts.
  const anyRunning = jobs.data?.some(isActive) ?? false
  const reloadJobs = jobs.reload
  const reloadSources = sources.reload
  useEffect(() => {
    if (!anyRunning) return
    const timer = window.setInterval(() => {
      reloadJobs()
      reloadSources()
    }, 4000)
    return () => window.clearInterval(timer)
  }, [anyRunning, reloadJobs, reloadSources])
  const wasRunning = useRef(false)
  useEffect(() => {
    if (wasRunning.current && !anyRunning) onSynced()
    wasRunning.current = anyRunning
  }, [anyRunning, onSynced])

  async function start(project: string) {
    setError(undefined)
    try {
      await api.startSync(project)
      jobs.reload()
    } catch (e) {
      setError(message(e))
    }
  }

  return (
    <section className="widget w-4" aria-labelledby="sync-title">
      <h2 id="sync-title" className="widget-title">
        Issue trackers
      </h2>
      <ul className="source-list">
        {sources.data?.map((src) => {
          const job = running(src.project)
          return (
            <li key={src.dependency}>
              <span
                className="legend-swatch"
                style={{ background: SOURCE_COLOR[src.dependency] ?? 'var(--ink-3)' }}
                aria-hidden="true"
              />
              <span className="source-name">{src.name}</span>
              <button onClick={() => start(src.project)} disabled={Boolean(job)}>
                {job ? 'Syncing…' : 'Sync'}
              </button>
              <span className="source-meta">
                {src.issues.toLocaleString()} issues
                {job
                  ? `, ${plural(job.progress, 'issue')} synced so far`
                  : src.synced_at
                    ? `, synced ${formatAgo(src.synced_at)}`
                    : ', not synced yet'}
              </span>
            </li>
          )
        })}
      </ul>
      <ErrorNote>{error ?? sources.error}</ErrorNote>
    </section>
  )
}

function Facts({ dependency }: { dependency: Dependency }) {
  const stats = useLoad(() => api.issueStats(dependency.project), [dependency.project])
  const s = stats.data
  return (
    <section className="widget w-4 stat-tile" aria-labelledby="facts-title">
      <h2 id="facts-title" className="widget-title">
        Stored facts
      </h2>
      <span className="count-value">{s ? s.read.toLocaleString() : '…'}</span>
      <span className="count-hint">{s ? `of ${s.bugs.toLocaleString()} bugs read` : ''}</span>
    </section>
  )
}

function ReadingTimeChart({ dependency }: { dependency: Dependency }) {
  const reading = useLoad(() => api.readingTime(dependency.project), [dependency.project])
  const r = reading.data
  if (!r || r.count === 0) return null
  const seconds = (ms: number | null | undefined) => (ms == null ? 'n/a' : `${Math.round(ms / 1000)} s`)
  return (
    <section className="widget w-12">
      <ColumnChart
        title={`Reading time per issue (median ${seconds(r.median_ms)}, 90% under ${seconds(r.p90_ms)})`}
        categories={r.bins.map((b) => (b.to_s == null ? `${b.from_s} s+` : `${b.from_s}–${b.to_s} s`))}
        categoryLabel="Reading time"
        series={[
          { key: 'issues', label: 'Issues', color: 'var(--ink-2)', values: r.bins.map((b) => b.count) },
        ]}
        height={170}
      />
    </section>
  )
}

function Models({ systems }: { systems: string[] }) {
  return (
    <section className="widget w-4" aria-labelledby="models-title">
      <h2 id="models-title" className="widget-title">
        Models
      </h2>
      {systems.length === 0 ? (
        <p className="pane-lead">None configured. Set DEP_WATCH_LLM_MODEL.</p>
      ) : (
        <>
          <ul className="model-list">
            {systems.map((s, i) => (
              <li key={s}>
                <span className="status-dot" aria-hidden="true" />
                {s}
                {i === 0 && <span className="muted">default</span>}
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  )
}

function Evaluation({ systems }: { systems: string[] }) {
  const runs = useLoad(() => api.runs(), [])
  const datasets = useLoad(() => api.datasets(), [])
  const [dataset, setDataset] = useState('kafka-ground-truth-v2')
  const [system, setSystem] = useState(systems[0] ?? '')
  const [jobId, setJobId] = useState<string>()
  const [error, setError] = useState<string>()
  const { job } = useJob(jobId, () => runs.reload())

  async function start() {
    setError(undefined)
    try {
      setJobId((await api.startRun({ dataset, system: system || systems[0] })).id)
    } catch (e) {
      setError(message(e))
    }
  }

  return (
    <section className="widget w-12" aria-labelledby="eval-title">
      <div className="pane-head">
        <div>
          <h2 id="eval-title" className="widget-title">
            Evaluation
          </h2>
        </div>
        <div className="toolbar">
          <label>
            <span>Dataset</span>
            <select value={dataset} onChange={(e) => setDataset(e.target.value)}>
              {datasets.data?.map((d) => (
                <option key={d.name} value={d.name}>
                  {d.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Model</span>
            <select value={system} onChange={(e) => setSystem(e.target.value)}>
              {systems.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>
          <button
            className="primary"
            onClick={start}
            disabled={systems.length === 0 || job?.status === 'running'}
          >
            Run
          </button>
        </div>
      </div>
      <ErrorNote>{error ?? runs.error ?? datasets.error}</ErrorNote>
      {job && (
        <JobLine
          job={job}
          describe={(j: Job) =>
            j.status === 'succeeded' ? 'Evaluation finished.' : 'Evaluating; this takes a while.'
          }
        />
      )}
      {runs.data && runs.data.length > 0 ? (
        <RunsTable runs={runs.data} />
      ) : (
        <p className="list-empty">No runs yet. Run one to compare models here.</p>
      )}
    </section>
  )
}

function RunsTable({ runs }: { runs: EvalRunSummary[] }) {
  const value = (run: EvalRunSummary, key: string) => {
    const v = run.metrics[key]
    return typeof v === 'number' ? v.toFixed(3) : 'n/a'
  }
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th scope="col">Run</th>
            <th scope="col">Model</th>
            {METRICS.map(([key, label]) => (
              <th key={key} scope="col" className="num">
                {label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr key={`${run.dataset}/${run.run_name}`}>
              <td>
                {run.run_name}
                {run.provisional && <span className="tag">provisional</span>}
              </td>
              <td>{run.system}</td>
              {METRICS.map(([key]) => (
                <td key={key} className="num">
                  {value(run, key)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function Jobs() {
  const jobs = useLoad(() => api.jobs(), [])
  return (
    <section className="widget w-12" aria-labelledby="jobs-title">
      <div className="pane-head">
        <div>
          <h2 id="jobs-title" className="widget-title">
            Background jobs
          </h2>
        </div>
        <button onClick={jobs.reload}>Refresh</button>
      </div>
      <ErrorNote>{jobs.error}</ErrorNote>
      {jobs.data && jobs.data.length > 0 ? (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th scope="col">Job</th>
                <th scope="col">Status</th>
                <th scope="col" className="num">
                  Progress
                </th>
                <th scope="col">Started</th>
              </tr>
            </thead>
            <tbody>
              {jobs.data.map((j) => (
                <tr key={j.id}>
                  <td>
                    {j.kind}
                    {typeof j.params.kafka_version === 'string' && ` ${j.params.kafka_version}`}
                  </td>
                  <td>
                    <span className={`job-status job-${j.status}`}>{j.status}</span>
                    {j.error && <span className="muted"> {j.error}</span>}
                  </td>
                  <td className="num">{j.progress}</td>
                  <td className="nowrap">{formatDate(j.started_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="list-empty">No jobs since the API started.</p>
      )}
    </section>
  )
}
