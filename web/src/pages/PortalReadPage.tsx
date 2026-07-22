import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, type PortalDocument } from '../api'
import { Button } from '../components/Button'
import { Shell } from '../components/Shell'

export function PortalReadPage() {
  const { number = '' } = useParams()
  const [doc, setDoc] = useState<PortalDocument | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [docxUrl, setDocxUrl] = useState<string | null>(null)
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)

  useEffect(() => {
    setError(null)
    void api
      .portal(number)
      .then(setDoc)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load'))
    void api
      .files(number)
      .then((f) => {
        setDocxUrl(f.download_docx)
        setPdfUrl(f.download_pdf)
      })
      .catch(() => {
        setDocxUrl(null)
        setPdfUrl(null)
      })
  }, [number])

  if (error) {
    return (
      <Shell>
        <p className="text-danger">{error}</p>
        <Link to="/manual" className="mt-4 inline-block text-sm text-accent">
          ← Back to manual
        </Link>
      </Shell>
    )
  }

  if (!doc) {
    return (
      <Shell>
        <p className="animate-pulse-soft text-ink-soft">Loading {number}…</p>
      </Shell>
    )
  }

  return (
    <Shell statusLine={`${doc.category} · v${doc.version} · ${doc.approved}`}>
      <article className="animate-rise mx-auto max-w-3xl">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Link
            to="/manual"
            className="text-xs font-semibold tracking-[0.18em] text-ink-soft/70 uppercase transition-colors hover:text-accent"
          >
            ← Operations manual
          </Link>
          <div className="flex flex-wrap gap-2">
            <Link to={`/documents/${doc.number}`}>
              <Button variant="ghost" className="!py-1.5 !text-xs">
                Edit source
              </Button>
            </Link>
            {docxUrl ? (
              <a href={docxUrl}>
                <Button variant="secondary" className="!py-1.5 !text-xs">
                  Download Word
                </Button>
              </a>
            ) : null}
            {pdfUrl ? (
              <a href={pdfUrl}>
                <Button variant="secondary" className="!py-1.5 !text-xs">
                  Download PDF
                </Button>
              </a>
            ) : (
              <Link to={`/documents/${doc.number}`}>
                <Button variant="ghost" className="!py-1.5 !text-xs">
                  Generate PDF
                </Button>
              </Link>
            )}
          </div>
        </div>

        <p className="font-display mt-8 text-sm font-bold tracking-wide text-accent">
          {doc.number}
        </p>
        <h1 className="font-display mt-2 text-4xl font-extrabold tracking-tight text-ink md:text-5xl">
          {doc.title}
        </h1>
        <p className="mt-3 text-sm text-ink-soft">
          Version {doc.version} · {doc.category} · {doc.owner} · {doc.approved}
        </p>

        <div className="mt-8 border-t border-line pt-8">
          <h2 className="font-display text-lg font-bold text-ink">At a glance</h2>
          <ul className="mt-4 space-y-3">
            {doc.summary.bullets.map((b, i) => (
              <li key={i} className="border-l-2 border-accent/40 pl-4 text-sm leading-relaxed text-ink-soft">
                {b}
              </li>
            ))}
          </ul>
        </div>

        <section className="mt-10">
          <h2 className="font-display text-xl font-bold text-ink">Purpose</h2>
          <p className="mt-3 text-base leading-relaxed text-ink-soft">{doc.purpose}</p>
        </section>

        <section className="mt-8">
          <h2 className="font-display text-xl font-bold text-ink">Scope</h2>
          <p className="mt-3 text-base leading-relaxed text-ink-soft">{doc.scope}</p>
        </section>

        <div className="mt-10 space-y-10">
          {doc.sections
            .filter((section) => {
              const h = section.heading.trim().toLowerCase()
              return h !== 'purpose' && h !== 'scope'
            })
            .map((section, i) => (
              <section key={i} className="animate-rise border-t border-line/80 pt-8">
                {section.heading ? (
                  <h2 className="font-display text-xl font-bold text-ink">{section.heading}</h2>
                ) : null}
                {section.type === 'table' && section.rows?.length ? (
                  <div className="mt-4 overflow-x-auto">
                    <table className="w-full border-collapse text-left text-sm text-ink-soft">
                      <thead>
                        <tr>
                          {section.rows[0].map((cell, ci) => (
                            <th
                              key={ci}
                              className="border-b border-line px-3 py-2 font-semibold text-ink"
                            >
                              {cell}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {section.rows.slice(1).map((row, ri) => (
                          <tr key={ri}>
                            {row.map((cell, ci) => (
                              <td key={ci} className="border-b border-line/70 px-3 py-2">
                                {cell}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : null}
                {section.type === 'image' && section.src ? (
                  <p className="mt-3 text-sm text-ink-soft/70">Figure: {section.src}</p>
                ) : null}
                {section.body ? (
                  <p className="mt-3 whitespace-pre-wrap text-base leading-relaxed text-ink-soft">
                    {section.body}
                  </p>
                ) : null}
              </section>
            ))}
        </div>

        <footer className="mt-14 border-t border-line pt-6 text-xs text-ink-soft/60">
          Web reading view generated from JSON source · {doc.path}
        </footer>
      </article>
    </Shell>
  )
}
