import { useEffect, useRef, useState } from 'react'
import { api, type StatusPayload, type TemplateStatus } from '../api'
import { Button } from '../components/Button'
import { Shell } from '../components/Shell'

export function SystemPage() {
  const [status, setStatus] = useState<StatusPayload | null>(null)
  const [template, setTemplate] = useState<TemplateStatus | null>(null)
  const [validation, setValidation] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [flash, setFlash] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [busyTemplate, setBusyTemplate] = useState(false)
  const templateInput = useRef<HTMLInputElement>(null)
  const logoInput = useRef<HTMLInputElement>(null)

  async function load() {
    setError(null)
    try {
      const [s, t] = await Promise.all([api.status(), api.templateStatus()])
      setStatus(s)
      setTemplate(t)
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
        const warned = report.documents.filter((d) => (d.warnings?.length ?? 0) > 0)
        setValidation(
          warned.length
            ? `All ${report.count} documents OK\n` +
                warned
                  .map((d) => `${d.number}: ${(d.warnings ?? []).join('; ')}`)
                  .join('\n')
            : `All ${report.count} documents OK`,
        )
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

  async function onTemplateFile(file: File | undefined) {
    if (!file) return
    setBusyTemplate(true)
    setFlash(null)
    setError(null)
    try {
      const next = await api.uploadTemplate(file)
      setTemplate(next)
      setFlash(
        next.validation?.ok
          ? 'Master template uploaded and validated. Rebuild the library to refresh all Word files.'
          : 'Template uploaded — check missing placeholders below.',
      )
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Template upload failed')
    } finally {
      setBusyTemplate(false)
      if (templateInput.current) templateInput.current.value = ''
    }
  }

  async function onLogoFile(file: File | undefined) {
    if (!file) return
    setBusyTemplate(true)
    setFlash(null)
    setError(null)
    try {
      const next = await api.uploadLogo(file)
      setTemplate(next)
      setFlash(
        'Logo uploaded and applied to the gold master header. Generate a document to see it.',
      )
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Logo upload failed')
    } finally {
      setBusyTemplate(false)
      if (logoInput.current) logoInput.current.value = ''
    }
  }

  async function onRebuildStarter() {
    setBusyTemplate(true)
    setFlash(null)
    setError(null)
    try {
      const next = await api.rebuildStarterTemplate()
      setTemplate(next)
      setFlash('Starter gold master rebuilt' + (next.logo_exists ? ' (logo re-applied).' : '.'))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Rebuild failed')
    } finally {
      setBusyTemplate(false)
    }
  }

  return (
    <Shell>
      <section className="animate-rise max-w-3xl">
        <p className="text-xs font-semibold tracking-[0.22em] text-gold uppercase">
          System
        </p>
        <h2 className="font-display mt-2 text-4xl font-extrabold tracking-tight text-ink">
          Health & branding
        </h2>
        <p className="mt-3 text-ink-soft/85">
          Manage the master template and logo here — no repository access required.
        </p>

        {error ? (
          <p className="mt-6 rounded-md border border-danger/30 bg-danger/5 px-4 py-3 text-sm text-danger">
            {error}
          </p>
        ) : null}
        {flash ? (
          <p className="mt-6 rounded-md border border-ok/30 bg-ok/5 px-4 py-3 text-sm text-ok">
            {flash}
          </p>
        ) : null}

        <div className="animate-rise-delay mt-10 border-t border-line pt-8">
          <h3 className="font-display text-xl font-bold text-ink">Master template</h3>
          <p className="mt-2 text-sm leading-relaxed text-ink-soft">
            Upload a designed Word file (<code className="text-xs">.docx</code> or{' '}
            <code className="text-xs">.dotx</code>). Keep placeholders such as{' '}
            <code className="text-xs">{'{{TITLE}}'}</code> and{' '}
            <code className="text-xs">{'{{BODY}}'}</code> exactly as written.
          </p>

          <dl className="mt-6 space-y-3">
            <Row label="Active file" value={template?.active ?? template?.active_error ?? '—'} />
            <Row
              label="Placeholders"
              value={
                template?.validation?.ok
                  ? 'OK — all required placeholders present'
                  : template?.validation?.missing?.length
                    ? `Missing: ${template.validation.missing.join(', ')}`
                    : template?.validation?.error ?? '—'
              }
            />
          </dl>

          <div className="mt-6 flex flex-wrap gap-3">
            <input
              ref={templateInput}
              type="file"
              accept=".docx,.dotx,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.wordprocessingml.template"
              className="hidden"
              onChange={(e) => void onTemplateFile(e.target.files?.[0])}
            />
            <Button
              busy={busyTemplate}
              onClick={() => templateInput.current?.click()}
            >
              Upload master template
            </Button>
            <a href="/api/template/download?format=docx">
              <Button variant="secondary">Download .docx</Button>
            </a>
            <a href="/api/template/download?format=dotx">
              <Button variant="ghost">Download .dotx</Button>
            </a>
            <Button
              variant="ghost"
              busy={busyTemplate}
              onClick={() => void onRebuildStarter()}
            >
              Reset starter template
            </Button>
          </div>
        </div>

        <div className="animate-rise-delay-2 mt-12 border-t border-line pt-8">
          <h3 className="font-display text-xl font-bold text-ink">Logo / header</h3>
          <p className="mt-2 text-sm leading-relaxed text-ink-soft">
            Upload a PNG or JPG. It is saved and inserted into the gold master header so
            generated Word files show the brand mark.
          </p>

          {template?.logo_url ? (
            <div className="mt-5 flex items-center gap-4 rounded-md border border-line bg-white/50 px-4 py-3">
              <img
                src={`${template.logo_url}?t=${Date.now()}`}
                alt="Current logo"
                className="h-12 w-auto object-contain"
              />
              <p className="text-xs text-ink-soft">{template.logo}</p>
            </div>
          ) : (
            <p className="mt-4 text-sm text-warn">
              No logo uploaded yet — this is why generated docs had no logo.
            </p>
          )}

          <div className="mt-6 flex flex-wrap gap-3">
            <input
              ref={logoInput}
              type="file"
              accept="image/png,image/jpeg,image/webp,image/gif,.png,.jpg,.jpeg,.webp,.gif"
              className="hidden"
              onChange={(e) => void onLogoFile(e.target.files?.[0])}
            />
            <Button busy={busyTemplate} onClick={() => logoInput.current?.click()}>
              Upload logo
            </Button>
          </div>
        </div>

        <dl className="mt-12 space-y-5 border-t border-line pt-6">
          <Row label="Documents" value={String(status?.document_count ?? '—')} />
          <Row
            label="PDF backends"
            value={
              status?.pdf_backends?.length
                ? status.pdf_backends.join(' · ')
                : 'None — install LibreOffice or use Word only'
            }
          />
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

        <div className="mt-12 border-t border-line pt-8">
          <h3 className="font-display text-xl font-bold text-ink">House style (frozen)</h3>
          <p className="mt-2 text-sm leading-relaxed text-ink-soft">
            Visual identity is locked. Change the gold master only for real usability
            problems — not fonts, spacing, or decorative polish. Content evolves;
            presentation stays deterministic.
          </p>
          {status?.category_ranges ? (
            <dl className="mt-5 grid gap-2 text-sm sm:grid-cols-2">
              {Object.entries(status.category_ranges).map(([cat, range]) => (
                <div key={cat} className="flex justify-between gap-3 border-b border-line/60 py-1.5">
                  <dt className="text-ink">{cat}</dt>
                  <dd className="text-ink-soft">
                    {range.from}–{range.to}
                  </dd>
                </div>
              ))}
            </dl>
          ) : null}
          {status?.standard_section_order?.length ? (
            <p className="mt-5 text-sm text-ink-soft">
              Standard section order:{' '}
              <span className="text-ink">{status.standard_section_order.join(' → ')}</span>
            </p>
          ) : null}
          {status?.section_types?.length ? (
            <p className="mt-2 text-sm text-ink-soft">
              Body components:{' '}
              <span className="text-ink">{status.section_types.join(', ')}</span>
            </p>
          ) : null}
        </div>

        <div className="mt-12 border-t border-line pt-8">
          <h3 className="font-display text-xl font-bold text-ink">Update branding</h3>
          <ol className="mt-4 list-decimal space-y-3 pl-5 text-sm leading-relaxed text-ink-soft">
            <li>
              Upload a <strong className="text-ink">logo</strong> (PNG/JPG) — it is applied
              to the document header automatically.
            </li>
            <li>
              Optional: upload a full <strong className="text-ink">master template</strong>{' '}
              (<code className="text-xs">.docx</code> / <code className="text-xs">.dotx</code>) —
              keep placeholders such as <code className="text-xs">{'{{TITLE}}'}</code> and{' '}
              <code className="text-xs">{'{{BODY}}'}</code>.
            </li>
            <li>
              Open any document in the <strong className="text-ink">Library</strong>, then
              click <strong className="text-ink">Generate</strong> to produce Word output with
              the new look.
            </li>
            <li>
              After a template change, use <strong className="text-ink">Rebuild library</strong>{' '}
              to refresh every document at once.
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
