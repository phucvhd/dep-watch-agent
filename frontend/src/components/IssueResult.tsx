import type { Answer, DroppedEvidence, Evidence } from '../api/client'
import { ANSWER_TEXT } from '../format'
import { Fields } from './common'
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
  introduced: 'Introduced in',
  affects: 'Observed in',
  unaffected: 'Not present in',
  fix: 'Fixed in',
}

// Why verdict.decide set a statement aside, in the API's words and in a reader's.
const DROPPED_TEXT: Record<string, string> = {
  'citation not found': 'the quote does not appear in the issue',
  'version not in quote': 'the quote does not mention this version',
  'release line, not a release': 'names a release line, not a release',
  'not a version': 'not a version number',
}

const state = (item: { status?: string | null; resolution?: string | null }) =>
  [item.status, item.resolution].filter(Boolean).join(', ') || 'Open'

/** One plain sentence on why the answer came out this way. */
function reason(item: AnsweredIssue, pinned: string): string {
  if (item.error) return `The issue could not be checked: ${item.error}`
  if (item.decided_by === 'fix_versions') {
    return `Fixed in ${item.fix_versions.join(', ')}; ${pinned} includes the fix.`
  }
  const startKnown = item.evidence.some((e) => e.kind === 'introduced')
  switch (item.answer) {
    case 'affected':
      return `The issue reports the bug at or before ${pinned}, and no fix covers ${pinned}.`
    case 'not_affected':
      return startKnown
        ? `The issue states the bug was introduced after ${pinned}.`
        : `The issue states that ${pinned} does not have the bug.`
    case 'insufficient_information':
      if (item.evidence.length === 0) return 'The issue text does not mention a specific release.'
      return startKnown
        ? `The releases the issue mentions do not determine whether ${pinned} is affected.`
        : `The issue reports where the bug was observed, not where it was introduced; ${pinned} can be neither confirmed nor ruled out.`
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
          {item.fix_versions.length > 0 && <span>Fixed in {item.fix_versions.join(', ')}</span>}
        </p>
      </header>
      <AnswerBody item={item} pinned={pinned} />
    </article>
  )
}

/** The answer for one version: the ruler, the reason, and the quotes it rests on. */
export function AnswerBody({ item, pinned }: { item: AnsweredIssue; pinned: string }) {
  const source =
    item.decided_by === 'fix_versions'
      ? 'JIRA fix versions (issue text not read)'
      : `${item.decided_by}${item.cached ? ' (stored evidence)' : ''}`
  return (
    <>
      <div className="detail-ruler">
        <VersionRuler pinned={pinned} evidence={item.evidence} fixVersions={item.fix_versions} />
      </div>
      <p className="detail-reason">{reason(item, pinned)}</p>

      {item.evidence.length > 0 && (
        <section aria-label="Evidence from the issue">
          <h3>Evidence from the issue</h3>
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
              ? '1 statement excluded'
              : `${item.dropped.length} statements excluded`}
          </summary>
          <ul>
            {item.dropped.map((d, i) => (
              <li key={i}>
                <span className="fact-kind">
                  {KIND_TEXT[d.kind] ?? d.kind} {d.version}: {DROPPED_TEXT[d.reason] ?? d.reason}
                </span>
                <Quote text={d.quote} />
              </li>
            ))}
          </ul>
        </details>
      )}

      <Fields className="detail-source" items={[['Decided by', source]]} />
    </>
  )
}
