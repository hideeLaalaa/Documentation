import { useEffect, useState } from 'react'
import { api, type StatusPayload } from '../api'
import { Button } from '../components/Button'
import { Shell } from '../components/Shell'

export function SystemPage() {
  const [status, setStatus] = useState<StatusPayload | null>(null)
  const [validation, setValidation] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function load() {
    setError(null)
    try {
      setStatus(await api.status())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load status')
    }
  }

  useEffect(() => {
    void load()
  }, [])

  async function onValidate() {
    setBusy(true)
    setValidation(null)
    try {
      const report = await api.validate()
      if (report.ok) {
        setValidation(`All ${report.count} documents OK`)
      } else {
        const failed = report.documents.filter((d) => !d.ok)
        setValidation(
          failed.map((d) => `${d.number}: ${d.errors.join('; ')}`).join('\n'),
        )
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Validation failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Shell>
      <section className="animate-rise max-w-3xl">
        <p className="text-xs font-semibold tracking-[0.22em] text-gold uppercase">
          System
        </p>
        <h2 className="font-display mt-2 text-4xl font-extrabold tracking-tight text-ink">
          Health & tooling
        </h2>
        <p className="mt-3 text-ink-soft/85">
          Check the gold master, PDF converters, and validate every JSON source.
        </p>

        {error ? (
          <p className="mt-6 rounded-md border border-danger/30 bg-danger/5 px-4 py-3 text-sm text-danger">
            {error}
          </p>
        ) : null}

        <dl className="animate-rise-delay mt-10 space-y-5 border-t border-line pt-6">
          <Row label="Documents" value={String(status?.document_count ?? '—')} />
          <Row
            label="Template"
            value={status?.template ?? status?.template_error ?? '—'}
          />
          <Row
            label="PDF backends"
            value={
              status?.pdf_backends?.length
                ? status.pdf_backends.join(' · ')
                : 'None — install LibreOffice or use DOCX only'
            }
          />
          <Row label="Project root" value={status?.root ?? '—'} />
        </dl>

        <div className="mt-8 flex flex-wrap gap-3">
          <Button variant="secondary" onClick={() => void load()}>
            Refresh status
          </Button>
          <Button onClick={() => void onValidate()} busy={busy}>
            Validate library
          </Button>
        </div>

        {validation ? (
          <pre className="mt-6 overflow-x-auto rounded-md border border-line bg-white/60 px-4 py-3 text-xs leading-relaxed text-ink-soft whitespace-pre-wrap">
            {validation}
          </pre>
        ) : null}

        <div className="animate-rise-delay-2 mt-12 border-t border-line pt-8">
          <h3 className="font-display text-xl font-bold text-ink">How this works</h3>
          <ol className="mt-4 list-decimal space-y-3 pl-5 text-sm leading-relaxed text-ink-soft">
            <li>
              <strong className="text-ink">Write words</strong> in JSON (this app or
              Cursor).
            </li>
            <li>
              <strong className="text-ink">Look & feel</strong> lives only in the gold
              master template.
            </li>
            <li>
              <strong className="text-ink">Generate</strong> pours content into the
              template and saves a Word file under Output/DOCX.
            </li>
          </ol>
        </div>
      </section>
    </Shell>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid gap-1 sm:grid-cols-[9rem_1fr] sm:gap-4">
      <dt className="text-[0.7rem] font-semibold tracking-[0.16em] text-ink-soft/70 uppercase">
        {label}
      </dt>
      <dd className="break-all text-sm text-ink">{value}</dd>
    </div>
  )
}
