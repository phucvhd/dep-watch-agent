import { useState, type FormEvent } from 'react'
import { api, type Dependency } from '../api/client'
import { ErrorNote, PageIntro } from '../components/common'
import { formatDay } from '../format'
import { useLoad } from '../hooks'

const PAGE = 30

interface Props {
  dependency: Dependency
  version: string
  onCheck: (key: string) => void
}

export function Issues({ dependency, version, onCheck }: Props) {
  const [draft, setDraft] = useState('')
  const [filters, setFilters] = useState({ q: '', issue_type: 'Bug', status: '', fix_version: '' })
  const [offset, setOffset] = useState(0)
  const [selected, setSelected] = useState<string>()
  const page = useLoad(
    () => api.issues({ project: dependency.project, ...filters, limit: PAGE, offset }),
    [dependency.project, filters, offset],
  )

  function search(event: FormEvent) {
    event.preventDefault()
    setOffset(0)
    setFilters((f) => ({ ...f, q: draft.trim() }))
  }

  const set = (field: keyof typeof filters) => (value: string) => {
    setOffset(0)
    setFilters((f) => ({ ...f, [field]: value }))
  }

  const total = page.data?.total ?? 0
  const items = page.data?.items ?? []
  const current = selected ?? items[0]?.key
  return (
    <div className="page">
      <PageIntro title="Issues">
        <p>Every {dependency.name} issue synced from JIRA, newest first.</p>
      </PageIntro>
      <form className="toolbar toolbar-wide" onSubmit={search} role="search">
        <label className="grow">
          <span>Search</span>
          <input
            type="search"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Key or words in the title"
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
      <ErrorNote>{page.error}</ErrorNote>

      <div className="split split-wide">
        <div className="list-pane">
          <p className="list-count" aria-live="polite">
            {page.loading ? 'Loading…' : `${total.toLocaleString()} issues`}
          </p>
          <ul className="rows">
            {items.map((issue) => (
              <li key={issue.key}>
                <button
                  className="row"
                  aria-current={issue.key === current ? 'true' : undefined}
                  onClick={() => setSelected(issue.key)}
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
        </div>
        <div className="detail-pane">
          {current && (
            <IssuePanel key={current} issueKey={current} version={version} onCheck={onCheck} />
          )}
        </div>
      </div>
    </div>
  )
}

function IssuePanel({
  issueKey,
  version,
  onCheck,
}: {
  issueKey: string
  version: string
  onCheck: (key: string) => void
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
          <span>{[data.status, data.resolution].filter(Boolean).join(', ')}</span>
          <span>{formatDay(data.created_at)}</span>
        </p>
      </header>
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
      <div className="detail-actions">
        <button className="primary" onClick={() => onCheck(issueKey)} disabled={!version}>
          Check against {version || 'your version'}
        </button>
      </div>
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
