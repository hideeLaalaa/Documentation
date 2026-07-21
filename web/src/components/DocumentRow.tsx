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
    <div
      className="grid grid-cols-1 gap-2 border-b border-line/80 py-4 md:grid-cols-[1fr_auto] md:items-center"
      style={{ animationDelay: `${Math.min(index, 12) * 40}ms` }}
    >
      <Link
        to={`/documents/${doc.number}`}
        className="group grid grid-cols-[7rem_1fr] items-baseline gap-4 transition-all duration-200 hover:pl-1 md:grid-cols-[8rem_1fr_9rem]"
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
      </Link>
      <div className="flex items-center justify-end gap-4 pl-[7rem] md:pl-0">
        <span
          className={[
            'text-xs font-semibold tracking-wide',
            statusTone[doc.approved] ?? 'text-ink-soft',
          ].join(' ')}
        >
          v{doc.version} · {doc.approved}
        </span>
        <Link
          to={`/portal/${doc.number}`}
          className="text-xs font-semibold tracking-wide text-accent transition-colors hover:text-accent-deep"
        >
          Read
        </Link>
      </div>
    </div>
  )
}
