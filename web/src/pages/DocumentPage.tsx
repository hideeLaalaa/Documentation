import { useEffect, useState, type ReactNode } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, type DocumentDetail, type Section } from '../api'
import { Button } from '../components/Button'
import { Shell } from '../components/Shell'

const emptySection = (): Section => ({ heading: '', body: '' })

export function DocumentPage() {
  const { number = '' } = useParams()
  const [doc, setDoc] = useState<DocumentDetail | null>(null)
  const [title, setTitle] = useState('')
  const [version, setVersion] = useState('1.0')
  const [category, setCategory] = useState('Legal')
  const [owner, setOwner] = useState('Spotlight Advocate')
  const [approved, setApproved] = useState('Pending')
  const [purpose, setPurpose] = useState('')
  const [scope, setScope] = useState('')
  const [sections, setSections] = useState<Section[]>([emptySection()])
  const [categories, setCategories] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)
  const [flash, setFlash] = useState<string | null>(null)
  const [busySave, setBusySave] = useState(false)
  const [busyGen, setBusyGen] = useState(false)
  const [includePdf, setIncludePdf] = useState(true)
  const [downloadDocx, setDownloadDocx] = useState<string | null>(null)
  const [downloadPdf, setDownloadPdf] = useState<string | null>(null)
  const [pdfHint, setPdfHint] = useState<string | null>(null)

  async function refreshFiles(num: string) {
    try {
      const files = await api.files(num)
      setDownloadDocx(files.download_docx)
      setDownloadPdf(files.download_pdf)
    } catch {
      /* ignore */
    }
  }

  async function load() {
    setError(null)
    try {
      const [detail, status] = await Promise.all([api.get(number), api.status()])
      setDoc(detail)
      setCategories(status.categories)
      setTitle(detail.raw.title)
      setVersion(detail.raw.version)
      setCategory(detail.raw.category)
      setOwner(detail.raw.owner)
      setApproved(detail.raw.approved)
      setPurpose(detail.raw.purpose)
      setScope(detail.raw.scope)
      setSections(detail.raw.sections.length ? detail.raw.sections : [emptySection()])
      if (!status.pdf_backends.length) {
        setPdfHint('No PDF converter found. Install LibreOffice for PDF export.')
        setIncludePdf(false)
      } else {
        setPdfHint(null)
      }
      await refreshFiles(number)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load document')
    }
  }

  useEffect(() => {
    void load()
  }, [number])

  async function onSave() {
    setBusySave(true)
    setFlash(null)
    setError(null)
    try {
      const updated = await api.save(number, {
        number,
        title,
        version,
        category,
        owner,
        approved,
        purpose,
        scope,
        sections: sections.filter((s) => s.heading.trim() || s.body.trim()),
        revision_history: doc?.raw.revision_history ?? [],
        force: true,
      })
      setDoc(updated)
      setFlash('Saved to JSON source')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed')
    } finally {
      setBusySave(false)
    }
  }

  async function onGenerate() {
    setBusyGen(true)
    setFlash(null)
    setError(null)
    try {
      const updated = await api.save(number, {
        number,
        title,
        version,
        category,
        owner,
        approved,
        purpose,
        scope,
        sections: sections.filter((s) => s.heading.trim() || s.body.trim()),
        revision_history: doc?.raw.revision_history ?? [],
        force: true,
      })
      setDoc(updated)
      const result = await api.generate(number, includePdf)
      setDownloadDocx(result.download_docx)
      setDownloadPdf(result.download_pdf)
      if (includePdf && result.pdf) {
        setFlash('Generated Word + PDF')
      } else if (includePdf && result.pdf_note) {
        setFlash(`Generated Word · PDF unavailable: ${result.pdf_note}`)
      } else {
        setFlash('Generated Word')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generate failed')
    } finally {
      setBusyGen(false)
    }
  }

  function updateSection(i: number, patch: Partial<Section>) {
    setSections((prev) => prev.map((s, idx) => (idx === i ? { ...s, ...patch } : s)))
  }

  if (!doc && !error) {
    return (
      <Shell>
        <p className="animate-pulse-soft text-ink-soft">Loading {number}…</p>
      </Shell>
    )
  }

  return (
    <Shell statusLine={doc ? `${doc.path} · ${doc.owner}` : undefined}>
      <div className="animate-rise mb-8 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <Link
            to="/"
            className="text-xs font-semibold tracking-[0.18em] text-ink-soft/70 uppercase transition-colors hover:text-accent"
          >
            ← Library
          </Link>
          <p className="font-display mt-3 text-sm font-bold tracking-wide text-accent">
            {number}
          </p>
          <h2 className="font-display mt-1 max-w-3xl text-3xl font-extrabold tracking-tight text-ink md:text-4xl">
            {title || 'Untitled'}
          </h2>
        </div>
        <div className="flex flex-col items-stretch gap-3 sm:items-end">
          <label className="flex items-center justify-end gap-2 text-xs text-ink-soft">
            <input
              type="checkbox"
              checked={includePdf}
              onChange={(e) => setIncludePdf(e.target.checked)}
              className="accent-accent"
            />
            Also generate PDF
          </label>
          <div className="flex flex-wrap justify-end gap-3">
            <Button variant="ghost" onClick={() => void onSave()} busy={busySave}>
              Save JSON
            </Button>
            <Button onClick={() => void onGenerate()} busy={busyGen}>
              Generate
            </Button>
            {downloadDocx ? (
              <a href={downloadDocx}>
                <Button variant="secondary">Download Word</Button>
              </a>
            ) : null}
            {downloadPdf ? (
              <a href={downloadPdf}>
                <Button variant="secondary">Download PDF</Button>
              </a>
            ) : null}
          </div>
          {pdfHint ? (
            <p className="max-w-sm text-right text-[0.7rem] leading-relaxed text-warn">
              {pdfHint}
            </p>
          ) : null}
        </div>
      </div>

      {error ? (
        <p className="mb-6 rounded-md border border-danger/30 bg-danger/5 px-4 py-3 text-sm text-danger">
          {error}
        </p>
      ) : null}
      {flash ? (
        <p className="mb-6 rounded-md border border-ok/30 bg-ok/5 px-4 py-3 text-sm text-ok">
          {flash}
        </p>
      ) : null}

      <div className="animate-rise-delay grid gap-10 lg:grid-cols-[1fr_18rem]">
        <div className="space-y-8">
          <Field label="Title">
            <input className={inputClass} value={title} onChange={(e) => setTitle(e.target.value)} />
          </Field>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Purpose">
              <textarea
                className={`${inputClass} min-h-28`}
                value={purpose}
                onChange={(e) => setPurpose(e.target.value)}
              />
            </Field>
            <Field label="Scope">
              <textarea
                className={`${inputClass} min-h-28`}
                value={scope}
                onChange={(e) => setScope(e.target.value)}
              />
            </Field>
          </div>

          <div>
            <div className="mb-3 flex items-center justify-between">
              <h3 className="font-display text-lg font-bold text-ink">Sections</h3>
              <Button
                variant="ghost"
                className="!py-1.5 !text-xs"
                onClick={() => setSections((s) => [...s, emptySection()])}
              >
                Add section
              </Button>
            </div>
            <div className="space-y-5">
              {sections.map((section, i) => (
                <div key={i} className="border-t border-line/80 pt-5">
                  <input
                    className={`${inputClass} mb-2 font-semibold`}
                    placeholder="Section heading"
                    value={section.heading}
                    onChange={(e) => updateSection(i, { heading: e.target.value })}
                  />
                  <textarea
                    className={`${inputClass} min-h-28`}
                    placeholder="Section body"
                    value={section.body}
                    onChange={(e) => updateSection(i, { body: e.target.value })}
                  />
                  {sections.length > 1 ? (
                    <button
                      type="button"
                      className="mt-2 text-xs font-semibold text-danger/80 hover:text-danger"
                      onClick={() =>
                        setSections((prev) => prev.filter((_, idx) => idx !== i))
                      }
                    >
                      Remove section
                    </button>
                  ) : null}
                </div>
              ))}
            </div>
          </div>
        </div>

        <aside className="animate-rise-delay-2 space-y-4 lg:sticky lg:top-8 lg:self-start">
          <h3 className="font-display text-sm font-bold tracking-[0.16em] text-ink-soft uppercase">
            Metadata
          </h3>
          <Field label="Version">
            <input className={inputClass} value={version} onChange={(e) => setVersion(e.target.value)} />
          </Field>
          <Field label="Category">
            <select
              className={inputClass}
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Owner">
            <input className={inputClass} value={owner} onChange={(e) => setOwner(e.target.value)} />
          </Field>
          <Field label="Approved">
            <select
              className={inputClass}
              value={approved}
              onChange={(e) => setApproved(e.target.value)}
            >
              {['Pending', 'Draft', 'Approved'].map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </Field>

          <div className="border-t border-line pt-4">
            <p className="text-xs font-semibold tracking-wide text-ink-soft/70 uppercase">
              Revision history
            </p>
            <ul className="mt-3 space-y-3">
              {(doc?.revision_history ?? []).map((r, i) => (
                <li key={`${r.version}-${i}`} className="text-xs leading-relaxed text-ink-soft">
                  <span className="font-semibold text-ink">{r.version}</span> · {r.date}
                  <br />
                  {r.notes}
                </li>
              ))}
            </ul>
          </div>
        </aside>
      </div>
    </Shell>
  )
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-[0.7rem] font-semibold tracking-[0.16em] text-ink-soft/70 uppercase">
        {label}
      </span>
      {children}
    </label>
  )
}

const inputClass =
  'w-full rounded-md border border-line bg-white/75 px-3 py-2.5 text-sm text-ink outline-none ring-accent/25 placeholder:text-ink-soft/40 focus:ring-2'
