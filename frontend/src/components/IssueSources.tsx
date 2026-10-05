import { api } from '../api/client'
import { useLoad } from '../hooks'
import { OTHER_COLOR, SOURCE_SLOTS, sourceColor } from '../sources'
import { DonutChart } from './charts'

/** Where the synced issues come from. ``onPick`` makes each source's segment and legend row
 * select it. */
export function IssueSources({ onPick, picked }: { onPick?: (id: string) => void; picked?: string }) {
  const sources = useLoad(() => api.sources(), [])
  if (!sources.data) return null
  const shown = sources.data.slice(0, SOURCE_SLOTS.length)
  const rest = sources.data.slice(SOURCE_SLOTS.length)
  const segments = shown.map((s, i) => ({
    key: s.dependency,
    label: s.name,
    value: s.issues,
    color: sourceColor(i),
    // The watermark is saved when a sync completes: until then the share is a floor.
    detail: s.synced_at ? undefined : 'sync incomplete',
  }))
  if (rest.length) {
    segments.push({
      key: 'other',
      label: `Other (${rest.length} sources)`,
      value: rest.reduce((sum, s) => sum + s.issues, 0),
      color: OTHER_COLOR,
      detail: undefined,
    })
  }
  return (
    <DonutChart
      title="Synced issues by source"
      centerLabel="issues"
      segments={segments}
      picked={picked}
      onPick={onPick && ((key) => key !== 'other' && onPick(key))}
    />
  )
}
