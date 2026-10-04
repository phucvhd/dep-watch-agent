import { useEffect, useRef, useState, type FormEvent } from 'react'
import { api, type CheckResponse } from '../api/client'
import { IssueResult } from '../components/IssueResult'
import { RulerKey } from '../components/VersionRuler'
import { ErrorNote } from '../components/common'
import { message } from '../hooks'

interface Props {
  pinned: string
  initialKey?: string
}

export function Check({ pinned, initialKey = '' }: Props) {
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
        await api.check({ issue_key: issueKey.trim().toUpperCase(), kafka_version: kafkaVersion.trim() }),
      )
    } catch (e) {
      setError(message(e))
    } finally {
      setBusy(false)
    }
  }

  function check(event: FormEvent) {
    event.preventDefault()
    void run(key, version)
  }

  // Arriving from an issue's "Check against" button: answer right away.
  const autoRan = useRef(false)
  useEffect(() => {
    if (initialKey && pinned && !autoRan.current) {
      autoRan.current = true
      void run(initialKey, pinned)
    }
  }, [initialKey, pinned])

  return (
    <section aria-labelledby="check-title">
      <h1 id="check-title" className="headline">
        Does one issue affect a version?
      </h1>
      <form className="scan-form" onSubmit={check}>
        <label>
          Issue
          <input
            value={key}
            onChange={(e) => setKey(e.target.value)}
            placeholder="KAFKA-19785"
            required
            pattern="[A-Za-z][A-Za-z0-9_]*-[0-9]+"
            title="A JIRA key such as KAFKA-19785"
          />
        </label>
        <label>
          Kafka version
          <input
            value={version}
            onChange={(e) => setVersion(e.target.value)}
            placeholder="3.9.1"
            required
          />
        </label>
        <button type="submit" disabled={busy}>
          {busy ? 'Checking' : 'Check issue'}
        </button>
      </form>
      <p className="hint">
        The first check of an issue waits for the model, up to a minute or two. Later checks,
        for any version, use the stored facts.
      </p>
      <ErrorNote>{error}</ErrorNote>
      {result && (
        <>
          <p className="lede">
            {result.issue_key} on Kafka {result.kafka_version}:{' '}
            <strong className={`answer-${result.answer}`}>
              {result.answer === 'affected'
                ? 'affected.'
                : result.answer === 'not_affected'
                  ? 'not affected.'
                  : "can't tell from the issue."}
            </strong>
          </p>
          <RulerKey />
          <IssueResult item={result} pinned={result.kafka_version} open />
        </>
      )}
    </section>
  )
}
