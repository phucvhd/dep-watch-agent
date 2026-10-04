import { useState } from 'react'
import { api, type EvalRunSummary, type Job } from '../api/client'
import { ErrorNote, JobLine } from '../components/common'
import { formatDate, plural } from '../format'
import { message, useJob, useLoad } from '../hooks'

const METRICS: [string, string][] = [
  ['macro_f1', 'Macro F1'],
  ['accuracy', 'Accuracy'],
  ['precision', 'Precision'],
  ['recall', 'Recall'],
  ['abstention_rate', 'Abstains'],
  ['citation_validity', 'Valid quotes'],
]

export function Operations({ systems }: { systems: string[] }) {
  return (
    <section aria-labelledby="ops-title">
      <h1 id="ops-title" className="headline">
        Data and models
      </h1>
      <Sync />
      <Evaluation systems={systems} />
      <Jobs />
    </section>
  )
}

function Sync() {
  const state = useLoad(() => api.syncState(), [])
  const [jobId, setJobId] = useState<string>()
  const [error, setError] = useState<string>()
  const { job } = useJob(jobId, () => state.reload())
  const watermark = state.data?.find((s) => s.source === 'jira:KAFKA')

  async function start() {
    setError(undefined)
    try {
      setJobId((await api.startSync()).id)
    } catch (e) {
      setError(message(e))
    }
  }

  return (
    <section className="block" aria-labelledby="sync-title">
      <h2 id="sync-title">Kafka JIRA</h2>
      <p>
        {watermark
          ? `Synced up to ${formatDate(watermark.watermark)}. A sync fetches only issues updated since then.`
          : 'Not synced yet. The first sync fetches about 20,000 issues and takes a few minutes.'}
      </p>
      <button onClick={start} disabled={job?.status === 'running'}>
        Sync JIRA now
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
    <section className="block" aria-labelledby="eval-title">
      <h2 id="eval-title">Evaluation</h2>
      <p>
        Scores a model on the labeled issues, through the same decision code as scans. Each
        issue is read again, so a run of the 100-issue set takes about an hour.
      </p>
      <div className="scan-form">
        <label>
          Dataset
          <select value={dataset} onChange={(e) => setDataset(e.target.value)}>
            {datasets.data?.map((d) => (
              <option key={d.name} value={d.name}>
                {d.name} ({d.labeled} of {d.total} labeled)
              </option>
            ))}
          </select>
        </label>
        <label>
          Model
          <select value={system} onChange={(e) => setSystem(e.target.value)}>
            {systems.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
        <button onClick={start} disabled={systems.length === 0 || job?.status === 'running'}>
          Run evaluation
        </button>
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
        <p className="hint">No runs yet. Run an evaluation to compare models here.</p>
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
      <table className="runs">
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
    <section className="block" aria-labelledby="jobs-title">
      <h2 id="jobs-title">
        Background jobs{' '}
        <button className="quiet" onClick={jobs.reload}>
          Refresh
        </button>
      </h2>
      <p>Jobs since the API last started; a restart forgets them.</p>
      <ErrorNote>{jobs.error}</ErrorNote>
      {jobs.data && jobs.data.length > 0 && (
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
                    {typeof j.params.kafka_version === 'string' && ` for ${j.params.kafka_version}`}
                  </td>
                  <td>{j.status === 'failed' ? `failed: ${j.error}` : j.status}</td>
                  <td className="num">{j.progress}</td>
                  <td className="nowrap">{formatDate(j.started_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
