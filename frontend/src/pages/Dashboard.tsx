import { useState, type FormEvent } from 'react'
import { api, type Dependency } from '../api/client'
import { useAnswers, type Answers, type AnswerState } from '../answers'
import { AnswerBody } from '../components/IssueResult'
import { RulerKey } from '../components/VersionRuler'
import { IssueSources } from '../components/IssueSources'
import { LineChart } from '../components/charts'
import { ErrorNote, PageIntro } from '../components/common'
import { ANSWER_TEXT, formatDay, plural } from '../format'
import { useLoad } from '../hooks'

const PAGE = 30

interface Props {
  dependencies: Dependency[] // every synced source
  watched?: Dependency // the dependency whose version is watched, if any
  version: string // the watched version, or '' when nothing is watched
  repo: string | null // the repository it was read from; null when added by hand
  systems: string[]
  issueKey?: string // from the URL: #/dashboard/PROJECT-123
}

/** Statistics from the database: where issues come from, then one source's numbers, trend and
 * issues. For the watched dependency an issue also shows whether it affects your version. */
export function Dashboard({ dependencies, watched, version, repo, systems, issueKey }: Props) {
  const [sourceId, setSourceId] = useState(() => {
    const fromKey = issueKey && dependencies.find((d) => issueKey.startsWith(`${d.project}-`))
    return (fromKey || watched || dependencies[0]).id
  })
  const dependency = dependencies.find((d) => d.id === sourceId) ?? dependencies[0]
  return (
    <SourceDashboard
      key={dependency.id}
      dependencies={dependencies}
      dependency={dependency}
      onSource={setSourceId}
      answerFor={dependency.watchable && dependency.id === watched?.id ? version : ''}
      repo={repo}
      systems={systems}
      issueKey={issueKey}
    />
  )
}

function SourceDashboard({
  dependencies,
  dependency,
  onSource,
  answerFor: version,
  repo,
  systems,
  issueKey,
}: {
  dependencies: Dependency[]
  dependency: Dependency
  onSource: (id: string) => void
  answerFor: string // the version to answer for; '' hides the answers
  repo: string | null
  systems: string[]
  issueKey?: string
}) {
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
  // The watched version's answers, for every issue on the page: stored ones at once, the rest
  // when checked from a card or the panel.
  const answers = useAnswers(
    version,
    items.map((i) => i.key),
  )
  const target = `${dependency.name} ${version}`
  const canRead = systems.length > 0
  const s = stats.data
  return (
    <div className="dash">
      <PageIntro title="Dashboard" />

      {/* One filter row above everything it scopes. */}
      <form className="widget w-12 toolbar search-widget" onSubmit={search} role="search">
        <label>
          <span>Source</span>
          <select value={dependency.id} onChange={(e) => onSource(e.target.value)}>
            {dependencies
              .filter((d) => d.added || d.id === dependency.id)
              .map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
          </select>
        </label>
        <label className="grow">
          <span>Search</span>
          <input
            type="search"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder={`Issue key (${dependency.project}-19785) or summary text`}
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

      <section className="widget w-4">
        <IssueSources picked={dependency.id} onPick={onSource} />
      </section>
      {s && (
        <div className="w-8 stat-tiles stat-tiles-2x2">
          {[
            ['Bugs', s.bugs],
            ['Open bugs', s.open_bugs],
            ['Fixed bugs', s.fixed_bugs],
            ['Checked by model', s.read],
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
            title="Bugs filed and fixed per month"
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
              { key: 'filed', label: 'Filed', color: 'var(--accent)', values: monthly.data.map((m) => m.filed) },
              { key: 'fixed', label: 'Fixed', color: 'var(--ink-3)', values: monthly.data.map((m) => m.fixed) },
            ]}
          />
        </section>
      )}

      {page.error && (
        <div className="w-12">
          <ErrorNote>{page.error}</ErrorNote>
        </div>
      )}

      <section className="widget w-5 list-widget" aria-label="Issues">
        <div className="widget-head">
          <div>
            <h2 className="widget-title">
              Issues
              <sup>{page.loading ? '…' : total.toLocaleString()}</sup>
            </h2>
            {version && (
              <p className="widget-sub">
                Target: {target}
                {repo ? ` (${repo})` : ''}
              </p>
            )}
          </div>
        </div>
        <ul className="rows">
          {items.map((issue) => (
            <li key={issue.key} className="row-item">
              <button
                className="row"
                aria-current={issue.key === current ? 'true' : undefined}
                onClick={() => {
                  setSelected(issue.key)
                  window.history.replaceState(null, '', `#/dashboard/${issue.key}`)
                }}
              >
                <span className="row-key">{issue.key}</span>
                <span className="row-state">
                  {[issue.status, issue.resolution].filter(Boolean).join(', ') || 'Open'}
                </span>
                <span className="row-title">{issue.summary}</span>
                <span className="row-date">Created {formatDay(issue.created_at)}</span>
              </button>
              {version && (
                <CardCheck
                  issueKey={issue.key}
                  state={answers.get(issue.key)}
                  target={target}
                  canRead={canRead}
                  onCheck={(refresh) => answers.check(issue.key, refresh)}
                />
              )}
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
            answers={answers}
            systems={systems}
          />
        ) : (
          <p className="list-empty">No issues match these filters.</p>
        )}
      </section>
    </div>
  )
}

/** A card's answer for the watched version, and the action that gets or refreshes it. Sits
 * beside the card's button rather than inside it, so it doesn't select the card. */
function CardCheck({
  issueKey,
  state: s,
  target,
  canRead,
  onCheck,
}: {
  issueKey: string
  state: AnswerState
  target: string
  canRead: boolean
  onCheck: (refresh: boolean) => void
}) {
  const result = 'result' in s ? s.result : undefined
  // Re-reading can't change an answer the fix versions settle, so those offer no re-check.
  const byFixes = result?.decided_by === 'fix_versions'
  return (
    <div className="card-check">
      {result ? (
        <span className={`verdict verdict-sm verdict-${result.answer}`}>
          {ANSWER_TEXT[result.answer]}
        </span>
      ) : s.state === 'unchecked' ? (
        <span className="card-check-note">Not checked</span>
      ) : null}
      {s.state === 'queued' || s.state === 'reading' ? (
        <span className="card-check-note" aria-live="polite">
          {s.state === 'reading' && <span className="spinner" aria-hidden="true" />}
          {s.state === 'reading' ? 'Checking…' : 'Queued'}
        </span>
      ) : s.state === 'failed' ? (
        <>
          <span className="card-check-note card-check-error" title={s.error}>
            Check failed
          </span>
          <button className="btn-sm" disabled={!canRead} onClick={() => onCheck(Boolean(result))}>
            Retry
          </button>
        </>
      ) : s.state === 'unchecked' ? (
        <button
          className="btn-sm"
          disabled={!canRead}
          title={canRead ? undefined : 'No model is configured'}
          aria-label={`Check ${issueKey} against ${target}`}
          onClick={() => onCheck(false)}
        >
          Check
        </button>
      ) : s.state === 'answered' && !byFixes ? (
        <button
          className="btn-sm"
          disabled={!canRead}
          aria-label={`Re-check ${issueKey} against ${target}`}
          onClick={() => onCheck(true)}
        >
          Re-check
        </button>
      ) : null}
    </div>
  )
}

function IssuePanel({
  issueKey,
  dependency,
  version,
  answers,
  systems,
}: {
  issueKey: string
  dependency: Dependency
  version: string
  answers: Answers
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

      {/* Only a watchable dependency is answered for a version; the others are synced only. */}
      {dependency.watchable && (
        <VersionAnswer
          issueKey={issueKey}
          dependency={dependency}
          version={version}
          answers={answers}
          systems={systems}
        />
      )}

      <dl className="facts-grid">
        <div>
          <dt>Affects versions</dt>
          <dd>{data.affects_versions.join(', ') || 'None'}</dd>
        </div>
        <div>
          <dt>Fix versions</dt>
          <dd>{data.fix_versions.join(', ') || 'None'}</dd>
        </div>
        <div>
          <dt>Components</dt>
          <dd>{data.components.join(', ') || 'None'}</dd>
        </div>
      </dl>
      <h3>Description</h3>
      <div className="issue-text">{data.description || 'No description.'}</div>
      {data.comments.length > 0 && (
        <details className="comments">
          <summary>{plural(data.comments.length, 'comment')}</summary>
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

/** The answer for a version: the watched one by default (shared with the cards), or another
 * typed in. Shown at once when it needs no model call; otherwise checked on request (the
 * first read of an issue takes the model 30 to 90 seconds). */
function VersionAnswer({
  issueKey,
  dependency,
  version: watched,
  answers: shared,
  systems,
}: {
  issueKey: string
  dependency: Dependency
  version: string
  answers: Answers
  systems: string[]
}) {
  const [draft, setDraft] = useState(watched)
  const [asked, setAsked] = useState(watched)
  const other = useAnswers(asked === watched ? '' : asked, [issueKey])
  const answers = asked === watched ? shared : other
  const s = answers.get(issueKey)
  const result = 'result' in s ? s.result : undefined
  const model = systems[0]

  return (
    <section className="answer" aria-labelledby="answer-title">
      <form
        className="answer-head"
        onSubmit={(e) => {
          e.preventDefault()
          setAsked(draft.trim())
        }}
      >
        <h3 id="answer-title">{dependency.name}</h3>
        <input
          aria-label="Version"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="3.9.1"
          size={8}
        />
        {draft.trim() !== asked && <button type="submit">Show answer</button>}
      </form>

      {!asked ? (
        <p className="hint-line">Enter a version.</p>
      ) : (
        <>
          {result && (
            <>
              <div className="verdict-row">
                <p className={`verdict verdict-${result.answer}`}>{ANSWER_TEXT[result.answer]}</p>
                {/* Re-reading can't change an answer the fix versions settle. */}
                {s.state === 'answered' && result.decided_by !== 'fix_versions' && (
                  <button
                    className="btn-sm"
                    onClick={() => answers.check(issueKey, true)}
                    disabled={!model}
                    title={`Re-read the issue${model ? ` with ${model}` : ''}; replaces the stored evidence`}
                  >
                    Re-check
                  </button>
                )}
              </div>
              <AnswerBody item={result} pinned={asked} />
              <RulerKey />
            </>
          )}
          {s.state === 'loading' ? (
            <p className="job-line" aria-live="polite">
              <span className="spinner" aria-hidden="true" />
              Loading…
            </p>
          ) : s.state === 'queued' || s.state === 'reading' ? (
            <p className="job-line" aria-live="polite">
              <span className="spinner" aria-hidden="true" />
              {s.state === 'queued' ? 'Queued' : 'Checking…'}
            </p>
          ) : s.state === 'unchecked' ? (
            <div className="unread">
              <p>Not checked</p>
              <button
                className="primary"
                onClick={() => answers.check(issueKey)}
                disabled={!model}
                title={model ? undefined : 'No model configured'}
              >
                Check
              </button>
            </div>
          ) : s.state === 'failed' ? (
            <div className="unread">
              <ErrorNote>Check failed: {s.error}</ErrorNote>
              <button onClick={() => answers.check(issueKey, Boolean(result))} disabled={!model}>
                Retry
              </button>
            </div>
          ) : null}
        </>
      )}
    </section>
  )
}
