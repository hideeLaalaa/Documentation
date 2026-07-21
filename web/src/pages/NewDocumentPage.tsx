import { useEffect, useState, type FormEvent, type ReactNode } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { Button } from '../components/Button'
import { Shell } from '../components/Shell'

export function NewDocumentPage() {
  const navigate = useNavigate()
  const [categories, setCategories] = useState<string[]>([])
  const [number, setNumber] = useState('SA-')
  const [title, setTitle] = useState('')
  const [category, setCategory] = useState('Legal')
  const [purpose, setPurpose] = useState('')
  const [scope, setScope] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    void api.status().then((s) => {
      setCategories(s.categories)
      if (s.categories.includes('Legal')) setCategory('Legal')
      else if (s.categories.length) setCategory(s.categories[0])
    })
  }, [])

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const num = number.trim().toUpperCase()
      await api.create({
        number: num,
        title,
        category,
        purpose,
        scope,
      })
      navigate(`/documents/${num}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create document')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Shell>
      <section className="animate-rise mx-auto max-w-2xl">
        <Link
          to="/"
          className="text-xs font-semibold tracking-[0.18em] text-ink-soft/70 uppercase transition-colors hover:text-accent"
        >
          ← Library
        </Link>
        <h2 className="font-display mt-4 text-4xl font-extrabold tracking-tight text-ink">
          New document
        </h2>
        <p className="mt-3 text-ink-soft/85">
          Creates a JSON source under <code className="text-sm">Documents/</code>. You can
          edit content next, then generate Word.
        </p>

        <form onSubmit={(e) => void onCreate(e)} className="animate-rise-delay mt-10 space-y-5">
          <Field label="Number">
            <input
              required
              className={inputClass}
              value={number}
              onChange={(e) => setNumber(e.target.value.toUpperCase())}
              placeholder="SA-200"
            />
          </Field>
          <Field label="Title">
            <input
              required
              className={inputClass}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Official document title"
            />
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
          <Field label="Purpose">
            <textarea
              className={`${inputClass} min-h-24`}
              value={purpose}
              onChange={(e) => setPurpose(e.target.value)}
            />
          </Field>
          <Field label="Scope">
            <textarea
              className={`${inputClass} min-h-24`}
              value={scope}
              onChange={(e) => setScope(e.target.value)}
            />
          </Field>

          {error ? (
            <p className="rounded-md border border-danger/30 bg-danger/5 px-4 py-3 text-sm text-danger">
              {error}
            </p>
          ) : null}

          <Button type="submit" busy={busy}>
            Create document
          </Button>
        </form>
      </section>
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
