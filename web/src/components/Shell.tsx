import { Link, NavLink } from 'react-router-dom'
import type { ReactNode } from 'react'

type Props = {
  children: ReactNode
  statusLine?: string
}

export function Shell({ children, statusLine }: Props) {
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    [
      'text-sm tracking-wide transition-colors duration-200',
      isActive ? 'text-accent font-semibold' : 'text-ink-soft/80 hover:text-ink',
    ].join(' ')

  return (
    <div className="relative min-h-screen surface-grain">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[420px] bg-[radial-gradient(ellipse_at_top,_rgba(255,255,255,0.55),_transparent_70%)]" />

      <header className="relative border-b border-line/70 bg-paper/55 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-end justify-between gap-6 px-6 py-5 md:px-8">
          <Link to="/" className="group block">
            <p className="font-display text-[0.7rem] font-bold tracking-[0.28em] text-accent">
              SPOTLIGHT ADVOCATE
            </p>
            <h1 className="font-display mt-1 text-2xl font-extrabold tracking-tight text-ink transition-transform duration-300 group-hover:translate-x-0.5 md:text-3xl">
              Documentation System
            </h1>
          </Link>

          <nav className="flex flex-wrap items-center gap-x-6 gap-y-2 pb-1">
            <NavLink to="/" end className={linkClass}>
              Library
            </NavLink>
            <NavLink to="/manual" className={linkClass}>
              Manual
            </NavLink>
            <NavLink to="/new" className={linkClass}>
              New document
            </NavLink>
            <NavLink to="/system" className={linkClass}>
              System
            </NavLink>
          </nav>
        </div>
        {statusLine ? (
          <div className="border-t border-line/50 bg-ink/[0.03]">
            <p className="mx-auto max-w-6xl px-6 py-2 text-xs text-ink-soft/80 md:px-8">
              {statusLine}
            </p>
          </div>
        ) : null}
      </header>

      <main className="relative mx-auto max-w-6xl px-6 py-10 md:px-8 md:py-12">
        {children}
      </main>

      <footer className="relative mx-auto max-w-6xl px-6 pb-10 pt-2 text-xs text-ink-soft/60 md:px-8">
        Content in JSON · Formatting in the gold master · Output is generated
      </footer>
    </div>
  )
}
