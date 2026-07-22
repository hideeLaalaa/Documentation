import { Link } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'
import { api, type DocSummary, type StatusPayload } from '../api'
import { Button } from '../components/Button'
import { DocumentRow } from '../components/DocumentRow'
import { Shell } from '../components/Shell'

export function LibraryPage() {
  const [status, setStatus] = useState<StatusPayload | null>(null)
  const [docs, setDocs] = useState<DocSummary[]>([])
  const [category, setCategory] = useState('All')
  const [query, setQuery] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [flash, setFlash] = useState<string | null>(null)

  async function load() {
    setError(null)
    try {
      const [s, list] = await Promise.all([api.status(), api.list()])
      setStatus(s)
      setDocs(list.documents)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load library')
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const filtered = useMemo(() => {
    return docs.filter((d) => {
      const catOk = category === 'All' || d.category === category
      const q = query.trim().toLowerCase()
      const qOk =
        !q ||
        d.number.toLowerCase().includes(q) ||
        d.title.toLowerCase().includes(q)
      return catOk && qOk
    })
  }, [docs, category, query])

  async function onRebuild() {
    setBusy(true)
    setFlash(null)
    setError(null)
    try {
      const result = await api.rebuild(false)
      setFlash(`Rebuilt ${result.count} document(s)`)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Rebuild failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Shell
      statusLine={
        status
          ? `${status.document_count} documents · template ${status.template ? 'ready' : 'missing'}`
          : undefined
      }
    >
      <section className="animate-rise">
        <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
          <div className="max-w-xl">
            <p className="text-xs font-semibold tracking-[0.22em] text-gold uppercase">
              Library
            </p>
            <h2 className="font-display mt-2 text-4xl font-extrabold tracking-tight text-ink md:text-5xl">
              Every document, one source.
            </h2>
            <p className="mt-3 text-base leading-relaxed text-ink-soft/85">
              Edit content as structured data. Generate polished Word files from the
              gold master template — formatting solved once.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button variant="secondary" onClick={() => void onRebuild()} busy={busy}>
              Rebuild library
            </Button>
            <Link to="/new">
              <Button>New document</Button>
            </Link>
          </div>
        </div>
      </section>

      <section className="animate-rise-delay mt-10">
        <div className="flex flex-col gap-3 border-b border-line pb-4 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-wrap gap-2">
            {['All', ...(status?.categories ?? [])].map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setCategory(cat)}
                className={[
                  'cursor-pointer rounded-md px-3 py-1.5 text-xs font-semibold tracking-wide transition-colors',
                  category === cat
                    ? 'bg-ink text-paper'
                    : 'text-ink-soft hover:bg-white/50',
                ].join(' ')}
              >
                {cat}
              </button>
            ))}
          </div>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search number or title"
            className="w-full rounded-md border border-line bg-white/70 px-3 py-2 text-sm outline-none ring-accent/30 placeholder:text-ink-soft/50 focus:ring-2 md:w-72"
          />
        </div>

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

        <div className="mt-2">
          <div className="hidden grid-cols-[8rem_1fr_9rem_7rem] gap-4 border-b border-line py-3 text-[0.65rem] font-semibold tracking-[0.18em] text-ink-soft/60 uppercase md:grid">
            <span>Number</span>
            <span>Title</span>
            <span>Category</span>
            <span className="text-right">Status</span>
          </div>
          {filtered.length === 0 ? (
            <p className="py-16 text-center text-ink-soft/70">No documents match.</p>
          ) : (
            filtered.map((doc, i) => (
              <div key={doc.number} className="animate-rise">
                <DocumentRow doc={doc} index={i} />
              </div>
            ))
          )}
        </div>
      </section>
    </Shell>
  )
}
