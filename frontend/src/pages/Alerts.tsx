import { useMemo, useState, type FormEvent } from 'react'
import { api, type Answer, type Job, type ScanResponse } from '../api/client'
import { IssueResult } from '../components/IssueResult'
import { RulerKey } from '../components/VersionRuler'
import { ErrorNote, JobLine } from '../components/common'
import { ANSWER_TEXT, formatDay, plural } from '../format'
import { isActive, message, useJob, useLoad } from '../hooks'

const GROUPS: Answer[] = ['affected', 'insufficient_information', 'not_affected']

function weekAgo(): string {
  const d = new Date(Date.now() - 7 * 24 * 3600 * 1000)
  return d.toISOString().slice(0, 10)
}

interface Props {
  pinned: string
  systems: string[]
}

export function Alerts({ pinned, systems }: Props) {
  // Scan jobs live in the API's memory; pick up the latest one for this version.
  const scans = useLoad(() => api.jobs('scan'), [])
  const latest = useMemo(
    () => scans.data?.find((j) => j.params.kafka_version === pinned),
    [scans.data, pinned],
  )
  const [startedId, setJobId] = useState<string>()
  const { job } = useJob(startedId ?? latest?.id)

  const [since, setSince] = useState(weekAgo)
  const [limit, setLimit] = useState(50)
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState<string>()

  async function startScan(event: FormEvent) {
    event.preventDefault()
    setStarting(true)
    setError(undefined)
    try {
      const started = await api.startScan({
        kafka_version: pinned,
        since: since ? new Date(`${since}T00:00:00Z`).toISOString() : null,
        limit,
      })
      setJobId(started.id)
    } catch (e) {
      setError(message(e))
    } finally {
      setStarting(false)
    }
  }

  const result = job?.status === 'succeeded' ? (job.result as unknown as ScanResponse) : undefined
  const running = isActive(job)

  return (
    <section aria-labelledby="alerts-title">
      <Headline id="alerts-title" pinned={pinned} result={result} running={running} />

      <form className="scan-form" onSubmit={startScan}>
        <label>
          Bugs updated since
          <input type="date" value={since} onChange={(e) => setSince(e.target.value)} />
        </label>
        <label>
          Read at most
          <input
            type="number"
            min={1}
            max={10000}
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
          />
        </label>
        <button type="submit" disabled={starting || running || systems.length === 0}>
          {running ? 'Scanning' : 'Scan issues'}
        </button>
      </form>
      <p className="hint">
        Issues the fix versions settle are answered at once. The others are read by the model,
        30 to 90 seconds each the first time, then from stored facts.
      </p>
      {systems.length === 0 && (
        <ErrorNote>
          No model is configured, so issues can't be read. Set DEP_WATCH_LLM_MODEL and restart
          the API.
        </ErrorNote>
      )}
      <ErrorNote>{error ?? scans.error}</ErrorNote>
      {job && job.status !== 'succeeded' && (
        <JobLine
          job={job}
          describe={(j: Job) =>
            j.status === 'queued' ? 'Waiting to start.' : `${plural(j.progress, 'issue')} read so far.`
          }
        />
      )}

      {result && <ScanResult result={result} pinned={pinned} />}
    </section>
  )
}

function Headline({
  id,
  pinned,
  result,
  running,
}: {
  id: string
  pinned: string
  result?: ScanResponse
  running: boolean
}) {
  if (running || !result) {
    return (
      <h1 id={id} className="headline">
        {running ? `Reading new Kafka bugs against ${pinned}.` : `Which new bugs affect Kafka ${pinned}?`}
      </h1>
    )
  }
  const affected = result.counts.affected ?? 0
  return (
    <h1 id={id} className="headline">
      {affected === 0
        ? `No new bug is shown to affect Kafka ${pinned}.`
        : `${plural(affected, 'bug')} ${affected === 1 ? 'affects' : 'affect'} Kafka ${pinned}.`}
    </h1>
  )
}

function ScanResult({ result, pinned }: { result: ScanResponse; pinned: string }) {
  const counts = result.counts
  const more = result.candidates_total - result.scanned
  return (
    <>
      <p className="lede">
        Read {plural(result.scanned, 'bug')}
        {result.since ? ` updated since ${formatDay(result.since)}` : ''} with {result.system}.{' '}
        {plural(counts.insufficient_information ?? 0, 'issue')} can't be settled from the issue
        text, and {counts.not_affected ?? 0} don't affect you.
        {result.cached > 0 && ` ${result.cached} came from stored facts.`}
        {more > 0 && ` ${plural(more, 'more bug')} matched; raise the limit to read them.`}
        {result.errors > 0 && ` ${plural(result.errors, 'issue')} couldn't be read.`}
      </p>
      <RulerKey />
      {GROUPS.map((answer) => {
        const items = result.items.filter((i) => i.answer === answer)
        if (items.length === 0) return null
        return (
          <section key={answer} className={`group group-${answer}`} aria-label={ANSWER_TEXT[answer]}>
            <h2>
              {ANSWER_TEXT[answer]} <span className="count">{items.length}</span>
            </h2>
            {answer === 'insufficient_information' && (
              <p className="hint">
                Worth a read when the issue touches what you run: the text doesn't say where
                the bug starts.
              </p>
            )}
            {items.map((item) => (
              <IssueResult
                key={item.issue_key}
                item={item}
                pinned={pinned}
                open={answer === 'affected'}
              />
            ))}
          </section>
        )
      })}
    </>
  )
}
