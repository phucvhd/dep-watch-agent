import { useState, type FormEvent } from 'react'
import { api, type CheckResponse, type Dependency } from '../api/client'
import { AnswerBody } from '../components/IssueResult'
import { RulerKey } from '../components/VersionRuler'
import { LineChart } from '../components/charts'
import { ErrorNote, PageIntro } from '../components/common'
import { ANSWER_TEXT, formatDay } from '../format'
import { message, useLoad } from '../hooks'

const PAGE = 30

interface Props {
  dependency: Dependency
  version: string // the watched version, or '' when nothing is watched
  systems: string[]
  issueKey?: string // from the URL: #/issues/KAFKA-123
}

/** Every synced issue, and for the selected one, whether it affects the version you run. */
export function Issues({ dependency, version, systems, issueKey }: Props) {
  const [draft, setDraft] = useState(issueKey ?? '')
  const [filters, setFilters] = useState({
    q: issueKey ?? '',
    issue_type: issueKey ? '' : 'Bug',
    status: '',
    fix_version: '',
  })
  const [offset, setOffset] = useState(0)
  const [selected, setSelected] = useState<string | undefined>(issueKey)
  const page = useLoad(
    () => api.issues({ project: dependency.project, ...filters, limit: PAGE, offset }),
    [dependency.project, filters, offset],
  )
  const stats = useLoad(() => api.issueStats(dependency.project), [dependency.project])
  // The current month is still filling up: plotted, it reads as a drop. Complete months only.
  const monthly = useLoad(
    () => api.monthly(dependency.project, 25).then((rows) => rows.slice(0, -1)),
    [dependency.project],
  )

  function search(event: FormEvent) {
    event.preventDefault()
    setOffset(0)
    setSelected(undefined)
    setFilters((f) => ({ ...f, q: draft.trim() }))
  }

  const set = (field: keyof typeof filters) => (value: string) => {
    setOffset(0)
    setSelected(undefined)
    setFilters((f) => ({ ...f, [field]: value }))
  }

  const total = page.data?.total ?? 0
  const items = page.data?.items ?? []
  const current = selected ?? items[0]?.key
  const s = stats.data
  return (
    <div className="dash">
      <PageIntro title="Issues" />

      {s && (
        <div className="w-12 stat-tiles">
          {[
            ['Bugs', s.bugs],
            ['Open bugs', s.open_bugs],
            ['Fixed bugs', s.fixed_bugs],
            ['Read by the model', s.read],
          ].map(([label, value]) => (
            <div key={label as string} className="widget stat-tile">
              <span className="count-label">{label}</span>
              <span className="count-value">{(value as number).toLocaleString()}</span>
            </div>
          ))}
        </div>
      )}

      {monthly.data && (
        <section className="widget w-12">
          <LineChart
            title="Bugs filed and fixed each month"
            categories={monthly.data.map((m) => m.month)}
            categoryLabel="Month"
            formatCategory={(m) =>
              new Date(`${m}-01T00:00:00Z`).toLocaleDateString(undefined, {
                month: 'short',
                year: '2-digit',
                timeZone: 'UTC',
              })
            }
            series={[
              { key: 'filed', label: 'Filed', color: 'var(--ink)', values: monthly.data.map((m) => m.filed) },
              { key: 'fixed', label: 'Fixed', color: 'var(--ink-3)', values: monthly.data.map((m) => m.fixed) },
            ]}
          />
        </section>
      )}

      <form className="widget w-12 toolbar search-widget" onSubmit={search} role="search">
        <label className="grow">
          <span>Search</span>
          <input
            type="search"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder={`A key such as ${dependency.project}-19785, or words in the title`}
          />
        </label>
        <label>
          <span>Type</span>
          <select value={filters.issue_type} onChange={(e) => set('issue_type')(e.target.value)}>
            <option value="">Any</option>
            <option>Bug</option>
            <option>Improvement</option>
            <option>Task</option>
            <option>Sub-task</option>
          </select>
        </label>
        <label>
          <span>Status</span>
          <select value={filters.status} onChange={(e) => set('status')(e.target.value)}>
            <option value="">Any</option>
            <option>Open</option>
            <option>In Progress</option>
            <option>Patch Available</option>
            <option>Resolved</option>
            <option>Closed</option>
          </select>
        </label>
        <label>
          <span>Fixed in</span>
          <input
            value={filters.fix_version}
            onChange={(e) => set('fix_version')(e.target.value)}
            placeholder="4.1.1"
            size={7}
          />
        </label>
        <button type="submit">Search</button>
      </form>
      {page.error && (
        <div className="w-12">
          <ErrorNote>{page.error}</ErrorNote>
        </div>
      )}

      <section className="widget w-5 list-widget" aria-label="Issues">
        <div className="widget-head">
          <h2 className="widget-title">
            Matching
            <sup>{page.loading ? '…' : total.toLocaleString()}</sup>
          </h2>
        </div>
        <ul className="rows">
          {items.map((issue) => (
            <li key={issue.key}>
              <button
                className="row"
                aria-current={issue.key === current ? 'true' : undefined}
                onClick={() => {
                  setSelected(issue.key)
                  window.history.replaceState(null, '', `#/issues/${issue.key}`)
                }}
              >
                <span className="row-key">{issue.key}</span>
                <span className="row-state">
                  {[issue.status, issue.resolution].filter(Boolean).join(', ')}
                </span>
                <span className="row-title">{issue.summary}</span>
                <span className="row-date">{formatDay(issue.created_at)}</span>
              </button>
            </li>
          ))}
        </ul>
        <nav className="pager" aria-label="Pages">
          <button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))}>
            Newer
          </button>
          <span>
            {total
              ? `${offset + 1}–${Math.min(offset + PAGE, total)} of ${total.toLocaleString()}`
              : ''}
          </span>
          <button disabled={offset + PAGE >= total} onClick={() => setOffset(offset + PAGE)}>
            Older
          </button>
        </nav>
      </section>
      <section className="widget w-7 detail-widget">
        {current ? (
          <IssuePanel
            key={`${current}@${version}`}
            issueKey={current}
            dependency={dependency}
            version={version}
            systems={systems}
          />
        ) : (
          <p className="list-empty">No issue matches.</p>
        )}
      </section>
    </div>
  )
}

function IssuePanel({
  issueKey,
  dependency,
  version,
  systems,
}: {
  issueKey: string
  dependency: Dependency
  version: string
  systems: string[]
}) {
  const issue = useLoad(() => api.issue(issueKey), [issueKey])
  const data = issue.data
  if (issue.error) return <ErrorNote>{issue.error}</ErrorNote>
  if (!data) return <p className="list-empty">Loading {issueKey}…</p>
  return (
    <article className="detail" aria-labelledby="issue-title">
      <header className="detail-head">
        <h2 id="issue-title">{data.summary}</h2>
        <p className="detail-meta">
          <a href={data.url} target="_blank" rel="noreferrer">
            {data.key}
          </a>
          <span>{[data.status, data.resolution].filter(Boolean).join(', ') || 'Open'}</span>
          <span>{formatDay(data.created_at)}</span>
        </p>
      </header>

      <VersionAnswer
        issueKey={issueKey}
        dependency={dependency}
        version={version}
        systems={systems}
      />

      <dl className="facts-grid">
        <div>
          <dt>Reported on</dt>
          <dd>{data.affects_versions.join(', ') || 'none listed'}</dd>
        </div>
        <div>
          <dt>Fixed in</dt>
          <dd>{data.fix_versions.join(', ') || 'not fixed'}</dd>
        </div>
        <div>
          <dt>Components</dt>
          <dd>{data.components.join(', ') || 'none listed'}</dd>
        </div>
      </dl>
      <h3>Description</h3>
      <div className="issue-text">{data.description || 'No description.'}</div>
      {data.comments.length > 0 && (
        <details className="comments">
          <summary>{data.comments.length} comments</summary>
          {data.comments.map((c, i) => (
            <div key={i} className="comment">
              <p className="comment-meta">
                {c.author ?? 'Unknown'}, {formatDay(c.created_at)}
              </p>
              <div className="issue-text">{c.body}</div>
            </div>
          ))}
        </details>
      )}
    </article>
  )
}

/** The answer for the watched version: shown at once when it needs no model call, else read
 * on request (the first read of an issue takes the model 30 to 90 seconds). */
function VersionAnswer({
  issueKey,
  dependency,
  version: watched,
  systems,
}: {
  issueKey: string
  dependency: Dependency
  version: string
  systems: string[]
}) {
  const [version, setVersion] = useState(watched)
  const [asked, setAsked] = useState(watched)
  const stored = useLoad(
    () => (asked ? api.storedAnswer(issueKey, asked) : Promise.resolve(undefined)),
    [issueKey, asked],
  )
  const [read, setRead] = useState<CheckResponse>()
  const [reading, setReading] = useState(false)
  const [error, setError] = useState<string>()

  async function readIssue() {
    setReading(true)
    setError(undefined)
    try {
      setRead(await api.check({ issue_key: issueKey, kafka_version: asked }))
    } catch (e) {
      setError(message(e))
    } finally {
      setReading(false)
    }
  }

  const result = read ?? stored.data?.result ?? undefined
  return (
    <section className="answer" aria-labelledby="answer-title">
      <form
        className="answer-head"
        onSubmit={(e) => {
          e.preventDefault()
          setRead(undefined)
          setAsked(version.trim())
        }}
      >
        <h3 id="answer-title">For {dependency.name}</h3>
        <input
          aria-label="Version"
          value={version}
          onChange={(e) => setVersion(e.target.value)}
          placeholder="3.9.1"
          size={8}
        />
        {version.trim() !== asked && <button type="submit">Answer</button>}
      </form>

      {!asked ? (
        <p className="hint-line">Enter a version.</p>
      ) : result ? (
        <>
          <p className={`verdict verdict-${result.answer}`}>{ANSWER_TEXT[result.answer]}</p>
          <AnswerBody item={result} pinned={asked} />
          <RulerKey />
        </>
      ) : stored.loading || reading ? (
        <p className="job-line" aria-live="polite">
          <span className="spinner" aria-hidden="true" />
          {reading ? 'Reading the issue (30–90 s)…' : 'Looking it up…'}
        </p>
      ) : stored.error ? (
        <ErrorNote>{stored.error}</ErrorNote>
      ) : (
        <div className="unread">
          <p>Not read yet for {asked}.</p>
          <button className="primary" onClick={readIssue} disabled={systems.length === 0}>
            {systems.length ? `Read with ${systems[0]}` : 'No model configured'}
          </button>
        </div>
      )}
      <ErrorNote>{error}</ErrorNote>
    </section>
  )
}
