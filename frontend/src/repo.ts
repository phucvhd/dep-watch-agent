// Read a repository folder the user picks, in the browser. Only build files are kept, and only
// their text is sent to the API (POST /repo/scan), which finds dependencies and versions.
import type { RepoFile } from './api/client'

const MANIFEST_NAMES = new Set([
  'pom.xml',
  'gradle.lockfile',
  'gradle.properties',
  'libs.versions.toml',
  'build.sbt',
  'bom.json',
  'sbom.json',
])

// Folders of generated or downloaded files: their build files aren't the project's own.
const SKIPPED_DIRS = new Set([
  'node_modules',
  '.git',
  'target',
  'build',
  'dist',
  'out',
  '.gradle',
  '.idea',
  '.venv',
  'vendor',
])

const MAX_FILES = 500
const MAX_BYTES = 2_000_000

/** Mirrors the API's `manifests.is_manifest`, so only files it would read are sent. */
export function isManifest(path: string): boolean {
  const name = path.split('/').pop()!.toLowerCase()
  return (
    MANIFEST_NAMES.has(name) ||
    name.endsWith('.cdx.json') ||
    name.endsWith('.gradle') ||
    name.endsWith('.gradle.kts') ||
    ((name.startsWith('docker-compose') || name.startsWith('compose')) &&
      (name.endsWith('.yml') || name.endsWith('.yaml')))
  )
}

export interface PickedRepo {
  name: string
  files: RepoFile[]
  skipped: number // build files left out because of size or count
}

/** The build files in a folder picked with <input webkitdirectory>, with their text. */
export async function readRepo(list: FileList): Promise<PickedRepo> {
  const all = Array.from(list)
  const name = all[0]?.webkitRelativePath.split('/')[0] ?? 'repository'
  const candidates = all.filter((file) => {
    const parts = file.webkitRelativePath.split('/').slice(1) // drop the repo folder itself
    return parts.slice(0, -1).every((dir) => !SKIPPED_DIRS.has(dir)) && isManifest(parts.join('/'))
  })
  const kept = candidates.filter((f) => f.size <= MAX_BYTES).slice(0, MAX_FILES)
  const files = await Promise.all(
    kept.map(async (file) => ({
      path: file.webkitRelativePath.split('/').slice(1).join('/'),
      content: await file.text(),
    })),
  )
  return { name, files, skipped: candidates.length - kept.length }
}
