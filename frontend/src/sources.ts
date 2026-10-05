// Colors for sources (dependencies whose issues are synced), with no dependency named here:
// the API's list order (GET /dependencies, GET /stats/sources) assigns them, so a source keeps
// its color whatever its share. The palette is validated all-pairs for three slots (a donut puts
// every pair side by side); sources past it go gray, and the donut folds them into "Other".

export const SOURCE_SLOTS = ['var(--src-1)', 'var(--src-2)', 'var(--src-3)'] as const
export const OTHER_COLOR = 'var(--ink-3)'

/** The color of the source at ``index`` in the API's order. */
export function sourceColor(index: number): string {
  return index >= 0 && index < SOURCE_SLOTS.length ? SOURCE_SLOTS[index] : OTHER_COLOR
}
