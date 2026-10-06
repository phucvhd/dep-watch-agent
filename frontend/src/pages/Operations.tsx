import { useState } from 'react'
import { api, type Dependency, type EvalRunSummary, type Job } from '../api/client'
import { ColumnChart } from '../components/charts'
import { ErrorNote, Fields, JobLine, PageIntro } from '../components/common'
import { formatDate } from '../format'
import { message, useJob, useLoad } from '../hooks'

const METRICS: [string, string][] = [
  ['macro_f1', 'Macro F1'],
  ['accuracy', 'Accuracy'],
  ['precision', 'Precision'],
  ['recall', 'Recall'],
  ['abstention_rate', 'Abstention rate'],
  ['citation_validity', 'Citation validity'],
]

const JOB_TEXT: Record<string, string> = {
  'sync-jira': 'JIRA sync',
  scan: 'Scan',
  'eval-run': 'Evaluation',
}

const STATUS_TEXT: Record<Job['status'], string> = {
  queued: 'Queued',
  running: 'Running',
  succeeded: 'Succeeded',
  failed: 'Failed',
}

interface Props {
  dependency: Dependency
  systems: string[]
}

/** The models that read issues: how many issues they have read, how long it takes, and how
 * they score on the ground truth. */
export function Operations({ dependency, systems }: Props) {
  return (
    <div className="dash">
      <PageIntro title="Models" />
      <Models systems={systems} />
      <Facts dependency={dependency} />
      <ReadingTimeChart dependency={dependency} />
      <Evaluation systems={systems} />
      <Jobs />
    </div>
  )
}

function Facts({ dependency }: { dependency: Dependency }) {
  const stats = useLoad(() => api.issueStats(dependency.project), [dependency.project])
  const s = stats.data
  return (
    <section className="widget w-4 stat-tile" aria-labelledby="facts-title">
      <h2 id="facts-title" className="widget-title">
        Checked bugs
      </h2>
      <span className="count-value">{s ? s.read.toLocaleString() : '…'}</span>
      <span className="count-hint">
        {s ? `of ${s.bugs.toLocaleString()} ${dependency.name} bugs` : ''}
      </span>
    </section>
  )
}

function ReadingTimeChart({ dependency }: { dependency: Dependency }) {
  const reading = useLoad(() => api.readingTime(dependency.project), [dependency.project])
  const r = reading.data
  if (!r || r.count === 0) return null
  const seconds = (ms: number | null | undefined) => (ms == null ? 'N/A' : `${Math.round(ms / 1000)} s`)
  return (
    <section className="widget w-12">
      <ColumnChart
        title="Reading time per issue"
        note={
          <Fields
            items={[
              ['Median', seconds(r.median_ms)],
              ['90th percentile', seconds(r.p90_ms)],
              ['Issues', r.count.toLocaleString()],
            ]}
          />
        }
        categories={r.bins.map((b) => (b.to_s == null ? `${b.from_s} s+` : `${b.from_s}–${b.to_s} s`))}
        categoryLabel="Reading time"
        series={[
          { key: 'issues', label: 'Issues', color: 'var(--accent)', values: r.bins.map((b) => b.count) },
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
        <p className="pane-lead">No model configured. Set DEP_WATCH_LLM_MODEL and restart the API.</p>
      ) : (
        <>
          <ul className="model-list">
            {systems.map((s, i) => (
              <li key={s}>
                <span className="status-dot" aria-hidden="true" />
                {s}
                {i === 0 && <span className="muted">Default</span>}
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
  const [chosenDataset, setDataset] = useState<string>()
  // Datasets are versioned by name (-v1, -v2); the newest supersedes the others.
  const dataset = chosenDataset ?? datasets.data?.map((d) => d.name).sort().at(-1) ?? ''
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
            j.status === 'succeeded'
              ? 'Evaluation completed'
              : 'Evaluation running (over 1 hour with a local model)'
          }
        />
      )}
      {runs.data && runs.data.length > 0 ? (
        <RunsTable runs={runs.data} />
      ) : (
        <p className="list-empty">No evaluation runs</p>
      )}
    </section>
  )
}

function RunsTable({ runs }: { runs: EvalRunSummary[] }) {
  const value = (run: EvalRunSummary, key: string) => {
    const v = run.metrics[key]
    return typeof v === 'number' ? v.toFixed(3) : 'N/A'
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
                {run.provisional && <span className="tag">Provisional</span>}
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
                    {JOB_TEXT[j.kind] ?? j.kind}
                    {typeof j.params.project === 'string' && ` ${j.params.project}`}
                    {typeof j.params.version === 'string' && ` ${j.params.version}`}
                  </td>
                  <td>
                    <span className={`job-status job-${j.status}`}>{STATUS_TEXT[j.status]}</span>
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
        <p className="list-empty">No jobs since the API started</p>
      )}
    </section>
  )
}
