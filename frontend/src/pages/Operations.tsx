import { api, type Dependency, type Job } from '../api/client'
import { ColumnChart } from '../components/charts'
import { ErrorNote, Fields, PageIntro } from '../components/common'
import { formatDate } from '../format'
import { useLoad } from '../hooks'

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

/** The models that read issues: how many issues they have read and how long it takes. How they
 * score on the ground truth is in Langfuse, where every eval run is an experiment. */
export function Operations({ dependency, systems }: Props) {
  return (
    <div className="dash">
      <PageIntro title="Models" />
      <Models systems={systems} />
      <Facts dependency={dependency} />
      <ReadingTimeChart dependency={dependency} />
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
