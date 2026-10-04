import { useEffect, useRef, useState, type FormEvent } from 'react'
import { api, type CheckResponse, type Dependency } from '../api/client'
import { IssueDetail } from '../components/IssueResult'
import { RulerKey } from '../components/VersionRuler'
import { ErrorNote } from '../components/common'
import { message } from '../hooks'

interface Props {
  dependency: Dependency
  version: string
  initialKey?: string
}

export function Check({ dependency, version: pinned, initialKey = '' }: Props) {
  const [key, setKey] = useState(initialKey)
  const [version, setVersion] = useState(pinned)
  const [result, setResult] = useState<CheckResponse>()
  const [error, setError] = useState<string>()
  const [busy, setBusy] = useState(false)

  async function run(issueKey: string, kafkaVersion: string) {
    setBusy(true)
    setError(undefined)
    setResult(undefined)
    try {
      setResult(
        await api.check({
          issue_key: issueKey.trim().toUpperCase(),
          kafka_version: kafkaVersion.trim(),
        }),
      )
    } catch (e) {
      setError(message(e))
    } finally {
      setBusy(false)
    }
  }

  // Opened from an issue's "Check" button: answer right away.
  const autoRan = useRef(false)
  useEffect(() => {
    if (initialKey && pinned && !autoRan.current) {
      autoRan.current = true
      void run(initialKey, pinned)
    }
  }, [initialKey, pinned])

  function submit(event: FormEvent) {
    event.preventDefault()
    void run(key, version)
  }

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Check an issue</h1>
          <p className="page-sub">
            Does one {dependency.name} issue affect a version? The first check of an issue waits
            for the model; later ones, for any version, use stored facts.
          </p>
        </div>
      </header>
      <form className="toolbar toolbar-wide" onSubmit={submit}>
        <label className="grow">
          <span>Issue</span>
          <input
            value={key}
            onChange={(e) => setKey(e.target.value)}
            placeholder={`${dependency.project}-19785`}
            required
            pattern="[A-Za-z][A-Za-z0-9_]*-[0-9]+"
            title={`A JIRA key such as ${dependency.project}-19785`}
          />
        </label>
        <label>
          <span>Version</span>
          <input value={version} onChange={(e) => setVersion(e.target.value)} required size={10} />
        </label>
        <button className="primary" type="submit" disabled={busy}>
          {busy ? 'Checking…' : 'Check'}
        </button>
      </form>
      <ErrorNote>{error}</ErrorNote>
      {busy && (
        <p className="job-line" aria-live="polite">
          <span className="spinner" aria-hidden="true" />
          Reading the issue. A first read takes 30 to 90 seconds.
        </p>
      )}
      {result && (
        <div className="check-result">
          <IssueDetail item={result} pinned={result.kafka_version} />
          <RulerKey />
        </div>
      )}
    </div>
  )
}
