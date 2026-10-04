import { createContext } from 'react'

/**
 * Release order as the API's version module sorts it (GET /versions). The UI never compares
 * versions itself; it only places them by this index.
 */
export const VersionOrder = createContext<Map<string, number>>(new Map())
