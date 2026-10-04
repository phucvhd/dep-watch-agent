import { useState, type FormEvent } from 'react'
import { api } from '../api/client'
import { ErrorNote } from '../components/common'
import { formatDay } from '../format'
import { useLoad } from '../hooks'

const PAGE = 25

interface Props {
  pinned: string
  onCheck: (key: string) => void
}

export function Issues({ pinned, onCheck }: Props) {
  const [draft, setDraft] = useState('')
  const [filters, setFilters] = useState({ q: '', issue_type: 'Bug', status: '', fix_version: '' })
  const [offset, setOffset] = useState(0)
  const [selected, setSelected] = useState<string>()
  const page = useLoad(
    () => api.issues({ ...filters, limit: PAGE, offset }),
    [filters, offset],
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
  return (
    <section aria-labelledby="issues-title">
      <h1 id="issues-title" className="headline">
        Synced Kafka issues
      </h1>
      <form className="scan-form" onSubmit={search} role="search">
        <label className="grow">
          Key or words in the title
          <input value={draft} onChange={(e) => setDraft(e.target.value)} placeholder="rebalance" />
        </label>
        <label>
          Type
          <select value={filters.issue_type} onChange={(e) => set('issue_type')(e.target.value)}>
            <option value="">Any</option>
            <option>Bug</option>
            <option>Improvement</option>
            <option>Task</option>
            <option>Sub-task</option>
          </select>
        </label>
        <label>
          Status
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
          Fixed in
          <input
            value={filters.fix_version}
            onChange={(e) => set('fix_version')(e.target.value)}
            placeholder="4.1.1"
            size={8}
          />
        </label>
        <button type="submit">Search</button>
      </form>
      <ErrorNote>{page.error}</ErrorNote>

      <p className="lede" aria-live="polite">
        {page.loading ? 'Loading.' : `${total.toLocaleString()} issues, newest first.`}
      </p>
      <div className="table-wrap">
        <table className="issues">
          <thead>
            <tr>
              <th scope="col">Issue</th>
              <th scope="col">Title</th>
              <th scope="col">State</th>
              <th scope="col">Reported</th>
            </tr>
          </thead>
          <tbody>
            {page.data?.items.map((issue) => (
              <tr key={issue.key} className={issue.key === selected ? 'selected' : undefined}>
                <td>
                  <button className="link" onClick={() => setSelected(issue.key)}>
                    {issue.key}
                  </button>
                </td>
                <td>{issue.summary}</td>
                <td>{[issue.status, issue.resolution].filter(Boolean).join(', ')}</td>
                <td className="nowrap">{formatDay(issue.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <nav className="pager" aria-label="Pages">
        <button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))}>
          Newer
        </button>
        <span>
          {total ? `${offset + 1} to ${Math.min(offset + PAGE, total)} of ${total.toLocaleString()}` : ''}
        </span>
        <button disabled={offset + PAGE >= total} onClick={() => setOffset(offset + PAGE)}>
          Older
        </button>
      </nav>

      {selected && (
        <IssuePanel issueKey={selected} pinned={pinned} onCheck={onCheck} onClose={() => setSelected(undefined)} />
      )}
    </section>
  )
}

function IssuePanel({
  issueKey,
  pinned,
  onCheck,
  onClose,
}: {
  issueKey: string
  pinned: string
  onCheck: (key: string) => void
  onClose: () => void
}) {
  const issue = useLoad(() => api.issue(issueKey), [issueKey])
  const data = issue.data
  return (
    <aside className="panel" aria-label={`Issue ${issueKey}`}>
      <div className="panel-head">
        <h2>
          {issueKey} {data && <span className="panel-title">{data.summary}</span>}
        </h2>
        <button className="quiet" onClick={onClose}>
          Close
        </button>
      </div>
      <ErrorNote>{issue.error}</ErrorNote>
      {data && (
        <>
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
            <div>
              <dt>State</dt>
              <dd>{[data.status, data.resolution].filter(Boolean).join(', ')}</dd>
            </div>
          </dl>
          <div className="panel-actions">
            <button onClick={() => onCheck(issueKey)} disabled={!pinned}>
              Check against Kafka {pinned || '(choose a version)'}
            </button>
            <a href={data.url} target="_blank" rel="noreferrer">
              Open in JIRA
            </a>
          </div>
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
        </>
      )}
    </aside>
  )
}
