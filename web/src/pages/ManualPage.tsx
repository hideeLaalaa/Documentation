import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type ManualPayload, type SearchResult } from '../api'
import { Shell } from '../components/Shell'

const PRESETS = [
  { id: 'All', label: 'All documents', category: undefined as string | undefined },
  { id: 'Operations', label: 'Operations manual', category: 'Operations' },
  { id: 'HR', label: 'Employee handbook', category: 'HR' },
  { id: 'Licensing', label: 'Licensing manual', category: 'Licensing' },
  { id: 'Legal', label: 'Legal library', category: 'Legal' },
]

export function ManualPage() {
  const [preset, setPreset] = useState('All')
  const [query, setQuery] = useState('')
  const [manual, setManual] = useState<ManualPayload | null>(null)
  const [results, setResults] = useState<SearchResult[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const category = useMemo(
    () => PRESETS.find((p) => p.id === preset)?.category,
    [preset],
  )

  useEffect(() => {
    setBusy(true)
    setError(null)
    void api
      .manual(category)
      .then((m) => {
        setManual(m)
        setResults(null)
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load'))
      .finally(() => setBusy(false))
  }, [category])

  useEffect(() => {
    const q = query.trim()
    if (!q) {
      setResults(null)
      return
    }
    const handle = window.setTimeout(() => {
      void api
        .search(q, category)
        .then((r) => setResults(r.results))
        .catch((err) => setError(err instanceof Error ? err.message : 'Search failed'))
    }, 220)
    return () => window.clearTimeout(handle)
  }, [query, category])

  const showing = results ?? manual?.documents.map((d) => ({
    number: d.number,
    title: d.title,
    category: d.category,
    approved: d.approved,
    version: d.version,
    snippet: d.purpose,
    matches: [] as SearchResult['matches'],
  }))

  const presetMeta = PRESETS.find((p) => p.id === preset)

  return (
    <Shell
      statusLine={
        manual
          ? `${manual.document_count} documents in view · search the live JSON corpus`
          : undefined
      }
    >
      <section className="animate-rise">
        <p className="text-xs font-semibold tracking-[0.22em] text-gold uppercase">
          Internal portal
        </p>
        <h2 className="font-display mt-2 max-w-2xl text-4xl font-extrabold tracking-tight text-ink md:text-5xl">
          {presetMeta?.label ?? 'Operations manual'}
        </h2>
        <p className="mt-3 max-w-2xl text-base leading-relaxed text-ink-soft/85">
          One searchable reading surface built from the same JSON sources that generate
          Word and PDF. Format stays independent of content.
        </p>
      </section>

      <section className="animate-rise-delay mt-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex flex-wrap gap-2">
          {PRESETS.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => setPreset(p.id)}
              className={[
                'rounded-md px-3 py-1.5 text-xs font-semibold tracking-wide transition-colors',
                preset === p.id ? 'bg-ink text-paper' : 'text-ink-soft hover:bg-white/50',
              ].join(' ')}
            >
              {p.label}
            </button>
          ))}
        </div>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search purpose, scope, sections…"
          className="w-full rounded-md border border-line bg-white/70 px-3 py-2.5 text-sm outline-none ring-accent/30 placeholder:text-ink-soft/50 focus:ring-2 md:w-80"
        />
      </section>

      {error ? (
        <p className="mt-6 rounded-md border border-danger/30 bg-danger/5 px-4 py-3 text-sm text-danger">
          {error}
        </p>
      ) : null}

      <section className="animate-rise-delay-2 mt-8">
        {busy && !manual ? (
          <p className="animate-pulse-soft text-ink-soft">Loading manual…</p>
        ) : null}

        {showing && showing.length === 0 ? (
          <p className="py-16 text-center text-ink-soft/70">
            {query.trim()
              ? 'No matches.'
              : 'No documents in this collection yet. Add JSON sources under Documents/.'}
          </p>
        ) : null}

        <div className="divide-y divide-line/80">
          {showing?.map((item, i) => (
            <Link
              key={item.number}
              to={`/portal/${item.number}`}
              className="group block py-6 transition-all duration-200 hover:bg-white/35 hover:pl-2"
              style={{ animationDelay: `${Math.min(i, 10) * 35}ms` }}
            >
              <div className="flex flex-wrap items-baseline justify-between gap-3">
                <div>
                  <p className="font-display text-sm font-bold tracking-wide text-accent">
                    {item.number}
                  </p>
                  <h3 className="mt-1 text-xl font-semibold text-ink transition-colors group-hover:text-accent-deep">
                    {item.title}
                  </h3>
                </div>
                <p className="text-xs font-semibold tracking-wide text-ink-soft">
                  {item.category} · v{item.version} · {item.approved}
                </p>
              </div>
              {item.snippet ? (
                <p className="mt-2 max-w-3xl text-sm leading-relaxed text-ink-soft/80">
                  {item.snippet}
                </p>
              ) : null}
              {item.matches?.length ? (
                <ul className="mt-3 space-y-1.5">
                  {item.matches.map((m, idx) => (
                    <li key={idx} className="text-xs text-ink-soft/70">
                      <span className="font-semibold text-ink-soft">{m.field}:</span>{' '}
                      {m.excerpt}
                    </li>
                  ))}
                </ul>
              ) : null}
            </Link>
          ))}
        </div>
      </section>
    </Shell>
  )
}
