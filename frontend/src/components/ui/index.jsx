import React, { useRef, useEffect } from 'react'

/* ── Utility: join class strings ──────────────────────── */
function cn(...args) {
  return args.filter(Boolean).join(' ')
}

/* ══════════════════════════════════════════════════════════
   Button
   Variants: primary | secondary | ghost | danger
   Sizes:    sm | md | lg
   ══════════════════════════════════════════════════════════ */
const BTN_BASE = 'inline-flex items-center justify-center gap-2 font-medium transition-default rounded-[var(--radius-md)] select-none disabled:opacity-50 disabled:pointer-events-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-ring)] focus-visible:ring-offset-2'
const BTN_VARIANTS = {
  primary:   'bg-[var(--color-ring)] text-white hover:opacity-90',
  secondary: 'border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] hover:bg-gray-50 dark:hover:bg-gray-800',
  ghost:     'text-[var(--color-text-secondary)] hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-[var(--color-text)]',
  danger:    'bg-red-600 text-white hover:bg-red-700',
  'danger-ghost': 'text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20',
}
const BTN_SIZES = {
  sm: 'h-8 px-3 text-xs',
  md: 'h-9 px-4 text-sm',
  lg: 'h-11 px-5 text-sm',
}

export const Button = React.forwardRef(function Button({ variant = 'primary', size = 'md', className, children, ...props }, ref) {
  return (
    <button
      ref={ref}
      type="button"
      className={cn(BTN_BASE, BTN_VARIANTS[variant], BTN_SIZES[size], className)}
      {...props}
    >
      {children}
    </button>
  )
})

/* ══════════════════════════════════════════════════════════
   Input
   ══════════════════════════════════════════════════════════ */
const INPUT_BASE = 'w-full rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] text-sm transition-default px-3 py-2'

export function Input({ icon, className, ...props }) {
  if (icon) {
    return (
      <div className="relative">
        <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] text-lg pointer-events-none">{icon}</span>
        <input className={cn(INPUT_BASE, 'pl-10', className)} {...props} />
      </div>
    )
  }
  return <input className={cn(INPUT_BASE, className)} {...props} />
}

export function Textarea({ className, ...props }) {
  return <textarea className={cn(INPUT_BASE, 'resize-none', className)} {...props} />
}

export function Label({ children, htmlFor, required, className }) {
  return (
    <label htmlFor={htmlFor} className={cn('block text-sm font-medium text-[var(--color-text-secondary)] mb-1.5', className)}>
      {children}
      {required && <span className="text-red-500 ml-0.5">*</span>}
    </label>
  )
}

/* ══════════════════════════════════════════════════════════
   Card
   ══════════════════════════════════════════════════════════ */
export function Card({ children, className, noPadding }) {
  return (
    <div className={cn(
      'rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] shadow-[var(--shadow-sm)]',
      !noPadding && 'p-5',
      className
    )}>
      {children}
    </div>
  )
}

export function CardHeader({ title, icon, description, actions, className }) {
  return (
    <div className={cn('flex items-start justify-between gap-4 border-b border-[var(--color-border)] px-5 py-4', className)}>
      <div className="min-w-0">
        <h2 className="text-base font-semibold text-[var(--color-text)] flex items-center gap-2">
          {icon && <span className="material-symbols-outlined text-[var(--color-ring)] text-lg">{icon}</span>}
          {title}
        </h2>
        {description && <p className="text-sm text-[var(--color-text-muted)] mt-0.5">{description}</p>}
      </div>
      {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
    </div>
  )
}

/* ══════════════════════════════════════════════════════════
   Page Header
   ══════════════════════════════════════════════════════════ */
export function PageHeader({ title, description, actions, backLink, backLabel, className }) {
  return (
    <div className={cn('mb-6', className)}>
      {backLink && (
        <a href={backLink} className="inline-flex items-center gap-1 text-xs font-medium text-[var(--color-ring)] hover:underline mb-2">
          <span className="material-symbols-outlined text-sm">arrow_back</span>
          {backLabel || 'Back'}
        </a>
      )}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-2xl font-bold tracking-tight text-[var(--color-text)]">{title}</h1>
          {description && <p className="text-sm text-[var(--color-text-secondary)] mt-1 max-w-2xl">{description}</p>}
        </div>
        {actions && <div className="flex flex-wrap items-center gap-2 shrink-0">{actions}</div>}
      </div>
    </div>
  )
}

/* ══════════════════════════════════════════════════════════
   Badge
   ══════════════════════════════════════════════════════════ */
const BADGE_VARIANTS = {
  default: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
  success: 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  danger:  'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  warning: 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  info:    'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
}
export function Badge({ children, variant = 'default', className }) {
  return (
    <span className={cn('inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium', BADGE_VARIANTS[variant], className)}>
      {children}
    </span>
  )
}

/* ══════════════════════════════════════════════════════════
   Spinner / LoadingState
   ══════════════════════════════════════════════════════════ */
export function Spinner({ size = 'md', className }) {
  const sz = { sm: 'h-4 w-4', md: 'h-6 w-6', lg: 'h-8 w-8' }[size]
  return (
    <svg className={cn('animate-spin text-[var(--color-ring)]', sz, className)} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  )
}

export function LoadingState({ message = 'Loading...', subMessage, useLottie, className }) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-12 text-center', className)}>
      {useLottie ? (
        <lottie-player
          src="/loading/registro.json"
          background="transparent"
          speed={1}
          style={{ width: 180, height: 220 }}
          loop
          autoplay
        />
      ) : (
        <Spinner size="lg" className="mb-3" />
      )}
      <p className="text-sm font-medium text-[var(--color-text-secondary)] mt-2">{message}</p>
      {subMessage && <p className="text-xs text-[var(--color-text-muted)] mt-1">{subMessage}</p>}
    </div>
  )
}

/* ══════════════════════════════════════════════════════════
   EmptyState
   ══════════════════════════════════════════════════════════ */
export function EmptyState({ icon = 'inbox', title, description, action, className }) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-16 text-center px-4', className)}>
      <div className="inline-flex items-center justify-center size-14 rounded-full bg-gray-100 dark:bg-gray-800 text-[var(--color-text-muted)] mb-4">
        <span className="material-symbols-outlined text-2xl">{icon}</span>
      </div>
      <h3 className="text-base font-semibold text-[var(--color-text)]">{title}</h3>
      {description && <p className="mt-1 text-sm text-[var(--color-text-muted)] max-w-sm">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}

/* ══════════════════════════════════════════════════════════
   StatusBanner (inline error/success/info)
   ══════════════════════════════════════════════════════════ */
const STATUS_VARIANTS = {
  error:   'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800/50 text-red-800 dark:text-red-300',
  success: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800/50 text-green-800 dark:text-green-300',
  warning: 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800/50 text-amber-800 dark:text-amber-300',
  info:    'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800/50 text-blue-800 dark:text-blue-300',
}
export function StatusBanner({ type = 'info', children, className }) {
  return (
    <div className={cn('rounded-[var(--radius-md)] border px-4 py-3 text-sm', STATUS_VARIANTS[type], className)}>
      {children}
    </div>
  )
}

/* ══════════════════════════════════════════════════════════
   Toast
   ══════════════════════════════════════════════════════════ */
export function AppToast({ toast, onDismiss }) {
  if (!toast) return null
  const isSuccess = toast.type === 'success'
  return (
    <div
      role="alert"
      className={cn(
        'fixed bottom-4 right-4 z-[300] px-4 py-3 rounded-[var(--radius-md)] shadow-[var(--shadow-lg)] flex items-center gap-2.5 text-sm font-medium text-white animate-[fadeInUp_0.2s_ease-out]',
        isSuccess ? 'bg-green-600' : 'bg-red-600'
      )}
    >
      <span className="material-symbols-outlined text-lg">{isSuccess ? 'check_circle' : 'error'}</span>
      <span>{toast.message}</span>
      <button type="button" onClick={onDismiss} className="ml-1 p-0.5 rounded hover:bg-white/20 transition-default" aria-label="Dismiss">
        <span className="material-symbols-outlined text-base">close</span>
      </button>
    </div>
  )
}

/* ══════════════════════════════════════════════════════════
   Confirm Dialog
   ══════════════════════════════════════════════════════════ */
export function ConfirmDialog({ open, title, message, confirmLabel, cancelLabel, variant, onConfirm, onCancel }) {
  const cancelRef = useRef(null)

  useEffect(() => {
    if (open) {
      cancelRef.current?.focus()
      const onKey = (e) => { if (e.key === 'Escape') onCancel?.() }
      document.addEventListener('keydown', onKey)
      return () => document.removeEventListener('keydown', onKey)
    }
  }, [open, onCancel])

  if (!open) return null
  const isDanger = variant === 'danger'
  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/50 backdrop-blur-[2px]" role="dialog" aria-modal="true">
      <div className="bg-[var(--color-surface)] rounded-[var(--radius-xl)] shadow-[var(--shadow-xl)] max-w-md w-full p-6 border border-[var(--color-border)]">
        <h3 className="text-lg font-semibold text-[var(--color-text)]">{title}</h3>
        <p className="mt-2 text-sm text-[var(--color-text-secondary)]">{message}</p>
        <div className="mt-6 flex gap-3 justify-end">
          <Button ref={cancelRef} variant="secondary" size="md" onClick={onCancel}>
            {cancelLabel || 'Cancel'}
          </Button>
          <Button variant={isDanger ? 'danger' : 'primary'} size="md" onClick={onConfirm}>
            {confirmLabel || 'Confirm'}
          </Button>
        </div>
      </div>
    </div>
  )
}

/* ══════════════════════════════════════════════════════════
   DataTable (generic)
   ══════════════════════════════════════════════════════════ */
export function DataTable({ caption, columns, rows, getRowKey, onRowClick, stickyHeader, emptyState }) {
  if (!rows || rows.length === 0) {
    return emptyState || <EmptyState icon="table_rows" title="No data" />
  }
  const theadBg = 'bg-gray-50 dark:bg-gray-900'
  const theadClass = cn(
    'text-[var(--color-text-muted)] text-xs font-medium uppercase tracking-wider border-b border-[var(--color-border)]',
    stickyHeader && 'sticky top-0 z-10',
    theadBg,
  )
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm whitespace-nowrap" aria-label={caption}>
        <thead className={theadClass}>
          <tr>
            {columns.map((col) => (
              <th key={col.key || col.accessorKey} className={cn('px-4 py-3', col.align === 'right' && 'text-right')}>
                {col.header ?? col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-[var(--color-border-subtle)]">
          {rows.map((row, idx) => (
            <tr
              key={getRowKey ? getRowKey(row) : idx}
              onClick={() => onRowClick?.(row)}
              className={cn(
                'transition-default',
                onRowClick && 'cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50',
              )}
            >
              {columns.map((col) => (
                <td key={col.key || col.accessorKey} className={cn('px-4 py-3 text-sm text-[var(--color-text)]', col.align === 'right' && 'text-right', col.cellClassName)}>
                  {typeof col.cell === 'function' ? col.cell(row) : typeof col.render === 'function' ? col.render(row) : row[col.accessorKey]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
