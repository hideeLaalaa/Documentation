import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger'

const styles: Record<Variant, string> = {
  primary:
    'bg-accent text-white hover:bg-accent-deep shadow-[0_1px_0_rgba(255,255,255,0.15)_inset]',
  secondary:
    'bg-ink text-paper hover:bg-ink-soft',
  ghost:
    'bg-transparent text-ink border border-line hover:border-ink/40 hover:bg-white/50',
  danger:
    'bg-danger/90 text-white hover:bg-danger',
}

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant
  children: ReactNode
  busy?: boolean
}

export function Button({
  variant = 'primary',
  children,
  busy,
  className = '',
  disabled,
  ...rest
}: Props) {
  return (
    <button
      {...rest}
      disabled={disabled || busy}
      className={[
        'inline-flex cursor-pointer items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-semibold tracking-wide transition-all duration-200',
        'disabled:cursor-not-allowed disabled:opacity-50',
        'active:translate-y-px',
        styles[variant],
        className,
      ].join(' ')}
    >
      {busy ? <span className="animate-pulse-soft">Working…</span> : children}
    </button>
  )
}
