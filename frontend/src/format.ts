import type { Answer } from './api/client'

export const ANSWER_TEXT: Record<Answer, string> = {
  affected: 'Affects your version',
  insufficient_information: "Can't tell from the issue",
  not_affected: "Doesn't affect your version",
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return ''
  return new Date(value).toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/** A calendar day. Scan dates are chosen as days and sent as midnight UTC, so they are shown
 * in UTC too; otherwise "since Sep 27" reads as Sep 26 west of Greenwich. */
export function formatDay(value: string): string {
  return new Date(value).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    timeZone: 'UTC',
  })
}

export const plural = (n: number, one: string, many = `${one}s`) =>
  `${n} ${n === 1 ? one : many}`
