import type { Answer, DroppedEvidence, Evidence } from '../api/client'
import { ANSWER_TEXT } from '../format'
import { MiniRuler, Quote, VersionRuler } from './VersionRuler'

/** What /scan items and /check responses have in common. */
export interface AnsweredIssue {
  issue_key: string
  url: string
  summary: string
  status?: string | null
  resolution?: string | null
  answer: Answer
  decided_by: string
  cached: boolean
  fix_versions: string[]
  evidence: Evidence[]
  dropped: DroppedEvidence[]
  error?: string | null
}

const KIND_TEXT: Record<Evidence['kind'], string> = {
  introduced: 'Bug starts in',
  affects: 'Bug seen on',
  unaffected: 'Bug absent on',
  fix: 'Fixed in',
}

const state = (item: { status?: string | null; resolution?: string | null }) =>
  [item.status, item.resolution].filter(Boolean).join(', ') || 'Open'

/** One plain sentence on why the answer came out this way. */
function reason(item: AnsweredIssue, pinned: string): string {
  if (item.error) return `This issue couldn't be read: ${item.error}`
  if (item.decided_by === 'fix_versions') {
    return `JIRA lists the fix in ${item.fix_versions.join(', ')}, which ${pinned} already includes.`
  }
  const startKnown = item.evidence.some((e) => e.kind === 'introduced')
  switch (item.answer) {
    case 'affected':
      return `The issue shows the bug at or before ${pinned}, and no fix reaches ${pinned}.`
    case 'not_affected':
      return startKnown
        ? `The issue says the bug starts after ${pinned}.`
        : `The issue says ${pinned} itself doesn't have the bug.`
    case 'insufficient_information':
      if (item.evidence.length === 0) return 'The issue text names no release.'
      return startKnown
        ? `The issue names releases, but none of them settles ${pinned}.`
        : `The issue says where the bug was seen, not where it starts, so ${pinned} can't be ruled in or out.`
  }
}

export function IssueRow({
  item,
  pinned,
  selected,
  onSelect,
}: {
  item: AnsweredIssue
  pinned: string
  selected: boolean
  onSelect: () => void
}) {
  return (
    <li>
      <button
        className={`row row-${item.answer}`}
        aria-current={selected ? 'true' : undefined}
        onClick={onSelect}
      >
        <span className="row-key">{item.issue_key}</span>
        <span className="row-state">{state(item)}</span>
        <span className="row-title">{item.summary}</span>
        <MiniRuler pinned={pinned} evidence={item.evidence} fixVersions={item.fix_versions} />
      </button>
    </li>
  )
}

export function IssueDetail({ item, pinned }: { item: AnsweredIssue; pinned: string }) {
  const source =
    item.decided_by === 'fix_versions'
      ? 'Settled by JIRA fix versions, without reading the text'
      : `Read by ${item.decided_by}${item.cached ? ' (stored facts)' : ''}`
  return (
    <article className="detail" aria-labelledby={`detail-${item.issue_key}`}>
      <header className="detail-head">
        <p className={`verdict verdict-${item.answer}`}>{ANSWER_TEXT[item.answer]}</p>
        <h2 id={`detail-${item.issue_key}`}>{item.summary}</h2>
        <p className="detail-meta">
          <a href={item.url} target="_blank" rel="noreferrer">
            {item.issue_key}
          </a>
          <span>{state(item)}</span>
          {item.fix_versions.length > 0 && <span>Fix in {item.fix_versions.join(', ')}</span>}
        </p>
      </header>

      <div className="detail-ruler">
        <VersionRuler pinned={pinned} evidence={item.evidence} fixVersions={item.fix_versions} />
      </div>
      <p className="detail-reason">{reason(item, pinned)}</p>

      {item.evidence.length > 0 && (
        <section aria-label="Evidence from the issue">
          <h3>What the issue says</h3>
          <ul className="facts">
            {item.evidence.map((e, i) => (
              <li key={i}>
                <span className={`fact-kind fact-${e.kind}`}>
                  {KIND_TEXT[e.kind]} <strong>{e.version}</strong>
                </span>
                <Quote text={e.quote} version={e.version} />
              </li>
            ))}
          </ul>
        </section>
      )}

      {item.dropped.length > 0 && (
        <details className="dropped">
          <summary>
            {item.dropped.length === 1
              ? '1 claim set aside'
              : `${item.dropped.length} claims set aside`}
          </summary>
          <ul>
            {item.dropped.map((d, i) => (
              <li key={i}>
                <span className="fact-kind">
                  {KIND_TEXT[d.kind] ?? d.kind} {d.version}: {d.reason}
                </span>
                <Quote text={d.quote} />
              </li>
            ))}
          </ul>
        </details>
      )}

      <p className="detail-source">{source}.</p>
    </article>
  )
}
