import { Link } from 'react-router-dom'
import type { DocSummary } from '../api'

const statusTone: Record<string, string> = {
  Approved: 'text-ok',
  Pending: 'text-warn',
  Draft: 'text-ink-soft',
}

type Props = {
  doc: DocSummary
  index: number
}

export function DocumentRow({ doc, index }: Props) {
  return (
    <Link
      to={`/documents/${doc.number}`}
      className="group grid grid-cols-[7rem_1fr_auto] items-baseline gap-4 border-b border-line/80 py-4 transition-all duration-200 hover:bg-white/40 hover:pl-2 md:grid-cols-[8rem_1fr_9rem_7rem]"
      style={{ animationDelay: `${Math.min(index, 12) * 40}ms` }}
    >
      <span className="font-display text-sm font-bold tracking-wide text-accent">
        {doc.number}
      </span>
      <div className="min-w-0">
        <p className="truncate text-[1.05rem] font-semibold text-ink transition-colors group-hover:text-accent-deep">
          {doc.title}
        </p>
        <p className="mt-0.5 text-xs text-ink-soft/70 md:hidden">
          {doc.category} · v{doc.version} · {doc.approved}
        </p>
      </div>
      <span className="hidden text-sm text-ink-soft md:block">{doc.category}</span>
      <span
        className={[
          'justify-self-end text-right text-xs font-semibold tracking-wide',
          statusTone[doc.approved] ?? 'text-ink-soft',
        ].join(' ')}
      >
        v{doc.version} · {doc.approved}
      </span>
    </Link>
  )
}
