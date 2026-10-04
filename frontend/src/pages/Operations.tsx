import { useState } from 'react'
import { api, type Dependency, type EvalRunSummary, type Job } from '../api/client'
import { ErrorNote, JobLine, PageIntro } from '../components/common'
import { formatAgo, formatDate, plural } from '../format'
import { message, useJob, useLoad } from '../hooks'

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
    <div className="page">
      <PageIntro title="Data and models">
        <p>Where the issues come from, and how well each model reads them.</p>
      </PageIntro>
      <div className="panes">
        <Sync dependency={dependency} onSynced={onSynced} />
        <Models systems={systems} />
      </div>
      <Evaluation systems={systems} />
      <Jobs />
    </div>
  )
}

function Sync({ dependency, onSynced }: { dependency: Dependency; onSynced: () => void }) {
  const state = useLoad(() => api.syncState(), [])
  const [jobId, setJobId] = useState<string>()
  const [error, setError] = useState<string>()
  const { job } = useJob(jobId, () => {
    state.reload()
    onSynced()
  })
  const watermark = state.data?.find((s) => s.source === `jira:${dependency.project}`)

  async function start() {
    setError(undefined)
    try {
      setJobId((await api.startSync(dependency.project)).id)
    } catch (e) {
      setError(message(e))
    }
  }

  return (
    <section className="pane" aria-labelledby="sync-title">
      <h2 id="sync-title">Issue tracker</h2>
      <p className="pane-lead">
        {dependency.name} issues from{' '}
        <a href={dependency.tracker_url} target="_blank" rel="noreferrer">
          JIRA
        </a>
        .{' '}
        {watermark
          ? `Synced ${formatAgo(watermark.watermark)}; a sync fetches only what changed since.`
          : 'Not synced yet; the first sync takes a few minutes.'}
      </p>
      <button onClick={start} disabled={job?.status === 'running'}>
        Sync now
      </button>
      <ErrorNote>{error ?? state.error}</ErrorNote>
      {job && (
        <JobLine
          job={job}
          describe={(j: Job) =>
            j.status === 'succeeded'
              ? `Synced ${plural(j.progress, 'issue')}.`
              : `${plural(j.progress, 'issue')} synced so far.`
          }
        />
      )}
    </section>
  )
}

function Models({ systems }: { systems: string[] }) {
  return (
    <section className="pane" aria-labelledby="models-title">
      <h2 id="models-title">Models</h2>
      {systems.length === 0 ? (
        <p className="pane-lead">
          None configured. Set DEP_WATCH_LLM_MODEL to a model on an OpenAI-compatible server and
          restart the API.
        </p>
      ) : (
        <>
          <p className="pane-lead">
            The model reads issue text and quotes what it says about versions; code makes every
            decision. Scans and checks use the first one.
          </p>
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
    <section className="pane" aria-labelledby="eval-title">
      <div className="pane-head">
        <div>
          <h2 id="eval-title">Evaluation</h2>
          <p className="pane-lead">
            Scores a model on labeled issues through the same decision code as scans. Every issue
            is read again, so a 100-issue run takes about an hour.
          </p>
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
    <section className="pane" aria-labelledby="jobs-title">
      <div className="pane-head">
        <div>
          <h2 id="jobs-title">Background jobs</h2>
          <p className="pane-lead">Since the API last started; a restart forgets them.</p>
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
