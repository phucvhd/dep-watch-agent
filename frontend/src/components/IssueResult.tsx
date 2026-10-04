import type { Answer, DroppedEvidence, Evidence } from '../api/client'
import { VersionRuler } from './VersionRuler'

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

/** One plain sentence on why the answer came out this way. */
function reason(item: AnsweredIssue, pinned: string): string {
  if (item.error) return `This issue couldn't be read: ${item.error}`
  if (item.decided_by === 'fix_versions') {
    return `JIRA lists the fix in ${item.fix_versions.join(', ')}, which ${pinned} already includes.`
  }
  const starts = item.evidence.some((e) => e.kind === 'introduced' || e.kind === 'unaffected')
  switch (item.answer) {
    case 'affected':
      return `The issue shows the bug at or before ${pinned}, and no fix reaches ${pinned}.`
    case 'not_affected':
      return `The issue shows the bug starting after ${pinned}, or a fix that ${pinned} includes.`
    case 'insufficient_information':
      if (item.evidence.length === 0) return 'The issue text names no Kafka release.'
      return starts
        ? `The issue names releases, but none of them settles ${pinned}.`
        : `The issue says where the bug was seen, not where it starts, so ${pinned} can't be ruled in or out.`
  }
}

interface Props {
  item: AnsweredIssue
  pinned: string
  open?: boolean
}

export function IssueResult({ item, pinned, open = false }: Props) {
  const source =
    item.decided_by === 'fix_versions'
      ? 'Settled by JIRA fix versions'
      : `Read by ${item.decided_by}${item.cached ? ', from stored facts' : ''}`
  return (
    <details className={`result result-${item.answer}`} open={open}>
      <summary>
        <span className="result-key">{item.issue_key}</span>
        <span className="result-summary">{item.summary}</span>
        <span className="result-state">
          {[item.status, item.resolution].filter(Boolean).join(', ') || 'Open'}
        </span>
      </summary>
      <div className="result-body">
        <VersionRuler pinned={pinned} evidence={item.evidence} fixVersions={item.fix_versions} />
        <p className="result-reason">{reason(item, pinned)}</p>
        {item.evidence.length > 0 && (
          <ul className="facts">
            {item.evidence.map((e, i) => (
              <li key={i}>
                <span className="fact-kind">
                  {KIND_TEXT[e.kind]} {e.version}
                </span>
                <blockquote>{e.quote}</blockquote>
              </li>
            ))}
          </ul>
        )}
        {item.dropped.length > 0 && (
          <details className="dropped">
            <summary>
              {item.dropped.length === 1 ? '1 fact set aside' : `${item.dropped.length} facts set aside`}
            </summary>
            <ul>
              {item.dropped.map((d, i) => (
                <li key={i}>
                  {KIND_TEXT[d.kind]} {d.version}: {d.reason}
                  <blockquote>{d.quote}</blockquote>
                </li>
              ))}
            </ul>
          </details>
        )}
        <p className="result-source">
          {source}.{' '}
          <a href={item.url} target="_blank" rel="noreferrer">
            Open {item.issue_key} in JIRA
          </a>
        </p>
      </div>
    </details>
  )
}
