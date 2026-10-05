import type { Answer } from './api/client'

export const ANSWER_TEXT: Record<Answer, string> = {
  affected: 'Affects you',
  insufficient_information: "Can't tell",
  not_affected: "Doesn't affect you",
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

/** "5 minutes ago", "3 days ago". */
export function formatAgo(value: string, now = Date.now()): string {
  const seconds = Math.round((new Date(value).getTime() - now) / 1000)
  const units: [Intl.RelativeTimeFormatUnit, number][] = [
    ['day', 86400],
    ['hour', 3600],
    ['minute', 60],
  ]
  const format = new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' })
  for (const [unit, size] of units) {
    if (Math.abs(seconds) >= size) return format.format(Math.round(seconds / size), unit)
  }
  return 'just now'
}

/** "now", "9m ago", "3h ago", "2d ago": for tight spots. */
export function formatAgoShort(value: string, now = Date.now()): string {
  const minutes = Math.round((now - new Date(value).getTime()) / 60000)
  if (minutes < 1) return 'now'
  if (minutes < 60) return `${minutes}m ago`
  if (minutes < 60 * 24) return `${Math.round(minutes / 60)}h ago`
  return `${Math.round(minutes / 60 / 24)}d ago`
}

export const plural = (n: number, one: string, many = `${one}s`) =>
  `${n} ${n === 1 ? one : many}`
