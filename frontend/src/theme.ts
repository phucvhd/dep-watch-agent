import { useCallback, useEffect, useState } from 'react'

export type ThemeChoice = 'system' | 'light' | 'dark'

const KEY = 'dwatcher.theme' // read before the first paint by index.html too
const SYSTEM_DARK = '(prefers-color-scheme: dark)'

function saved(): ThemeChoice {
  try {
    const value = localStorage.getItem(KEY)
    if (value === 'light' || value === 'dark') return value
  } catch {
    // storage blocked: follow the system
  }
  return 'system'
}

function apply(choice: ThemeChoice) {
  const dark = choice === 'dark' || (choice === 'system' && window.matchMedia(SYSTEM_DARK).matches)
  document.documentElement.dataset.theme = dark ? 'dark' : 'light'
}

/** Light, dark, or the system's: applied as ``data-theme`` on <html>, which picks the tokens
 * in styles.css. With "system" the page follows the system as it changes. */
export function useTheme() {
  const [choice, setChoice] = useState<ThemeChoice>(saved)

  useEffect(() => {
    apply(choice)
    if (choice !== 'system') return
    const media = window.matchMedia(SYSTEM_DARK)
    const follow = () => apply('system')
    media.addEventListener('change', follow)
    return () => media.removeEventListener('change', follow)
  }, [choice])

  const choose = useCallback((next: ThemeChoice) => {
    setChoice(next)
    try {
      if (next === 'system') localStorage.removeItem(KEY)
      else localStorage.setItem(KEY, next)
    } catch {
      // private mode: the choice lasts for this visit only
    }
  }, [])

  return { choice, choose }
}
