import React from 'react'

export function LoadingState({ message = 'Loading…', subMessage, useLottie, className = '' }) {
  return (
    <div className={`text-center ${useLottie ? 'p-6' : 'p-8'} ${className}`.trim()}>
      {useLottie ? (
        <div className="flex flex-col items-center justify-center">
          <lottie-player
            src="/loading/registro.json"
            background="transparent"
            speed={1}
            style={{ width: 200, height: 250 }}
            loop
            autoplay
          />
          <p className="text-gray-500 dark:text-gray-400 text-sm font-medium mt-2">{message}</p>
          {subMessage && <p className="text-gray-400 dark:text-gray-500 text-xs mt-1">{subMessage}</p>}
        </div>
      ) : (
        <>
          <div className="inline-flex items-center justify-center size-12 rounded-full bg-primary/10 text-primary animate-pulse mb-4">
            <span className="material-symbols-outlined">hourglass_empty</span>
          </div>
          <p className="font-medium text-[var(--color-text)]">{message}</p>
          {subMessage && <p className="text-sm text-[var(--color-text-muted)] mt-1">{subMessage}</p>}
        </>
      )}
    </div>
  )
}

export function AppToast({ toast, onDismiss }) {
  if (!toast) return null
  const isSuccess = toast.type === 'success'
  return (
    <div
      role="alert"
      className={`fixed top-4 right-4 z-[var(--z-toast)] px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 ${
        isSuccess ? 'bg-green-600 text-white' : 'bg-red-600 text-white'
      }`}
    >
      <span className="material-symbols-outlined">{isSuccess ? 'check_circle' : 'error'}</span>
      <span>{toast.message}</span>
      <button type="button" onClick={onDismiss} className="ml-2 p-1 rounded hover:bg-white/20" aria-label="Dismiss">
        <span className="material-symbols-outlined text-lg">close</span>
      </button>
    </div>
  )
}

export function ConfirmDialog({ open, title, message, confirmLabel, cancelLabel, variant, onConfirm, onCancel }) {
  if (!open) return null
  const isDanger = variant === 'danger'
  return (
    <div className="fixed inset-0 z-[var(--z-modal)] flex items-center justify-center p-4 bg-black/50" role="dialog" aria-modal="true">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6 border border-gray-100 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-[#110c1d] dark:text-white">{title}</h3>
        <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">{message}</p>
        <div className="mt-6 flex gap-3 justify-end">
          <button type="button" onClick={onCancel} className="px-4 py-2 rounded-md border border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
            {cancelLabel || 'Cancel'}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className={`px-4 py-2 rounded-md text-white transition-colors ${isDanger ? 'bg-red-600 hover:bg-red-700' : 'bg-primary hover:bg-primary-dark'}`}
          >
            {confirmLabel || 'Confirm'}
          </button>
        </div>
      </div>
    </div>
  )
}

export function PageHeader({ title, description, actions }) {
  return (
    <div className="mb-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-[#110c1d] dark:text-white">
          {title}
        </h1>
        {description && (
          <p className="text-gray-500 dark:text-gray-400 text-sm max-w-2xl">{description}</p>
        )}
      </div>
      {actions && (
        <div className="mt-4 flex flex-wrap items-center gap-2">{actions}</div>
      )}
    </div>
  )
}

export function AppCard({ children, noPadding, className = '' }) {
  return (
    <div className={`rounded-lg border border-gray-100/50 dark:border-gray-800/50 bg-surface-light dark:bg-surface-dark overflow-hidden ${noPadding ? '' : 'p-6'} ${className}`}>
      {children}
    </div>
  )
}

export function EmptyState({ icon, title, description, action }) {
  return (
    <div className="p-12 text-center">
      <div className="inline-flex items-center justify-center size-16 rounded-full bg-[var(--color-primary-muted)] text-[var(--color-primary)] mb-4">
        <span className="material-symbols-outlined text-3xl">{icon || 'inbox'}</span>
      </div>
      <h3 className="text-lg font-semibold text-[var(--color-text)]">{title}</h3>
      {description && <p className="mt-2 text-sm text-[var(--color-text-secondary)]">{description}</p>}
      {action && <div className="mt-6">{action}</div>}
    </div>
  )
}

export function Badge({ children, variant }) {
  const base = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium'
  const variants = {
    success: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    danger: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    default: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
  }
  return <span className={`${base} ${variants[variant] || variants.default}`}>{children}</span>
}

export function DataTable({ caption, columns, rows, getRowKey, onRowClick, stickyHeader, emptyState }) {
  if (!rows || rows.length === 0) {
    return emptyState || <p className="p-6 text-center text-[var(--color-text-muted)]">No data</p>
  }
  const theadClass = stickyHeader
    ? 'sticky top-0 z-10 bg-gray-50/30 dark:bg-gray-800/30 text-gray-500 dark:text-gray-400 font-medium border-b border-gray-100 dark:border-gray-800'
    : 'bg-gray-50/30 dark:bg-gray-800/30 text-gray-500 dark:text-gray-400 font-medium border-b border-gray-100 dark:border-gray-800'
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm whitespace-nowrap" aria-label={caption}>
        <thead className={theadClass}>
          <tr>
            {columns.map((col) => (
              <th
                key={col.key || col.accessorKey}
                className={`px-4 py-3 text-sm ${col.align === 'right' ? 'text-right' : ''}`}
              >
                {col.header ?? col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
          {rows.map((row, idx) => (
            <tr
              key={getRowKey ? getRowKey(row) : idx}
              onClick={() => onRowClick?.(row)}
              className={`group/row ${onRowClick ? 'cursor-pointer hover:bg-gray-50/50 dark:hover:bg-gray-800/30 transition-colors' : ''}`}
            >
              {columns.map((col) => (
                <td
                  key={col.key || col.accessorKey}
                  className={`px-4 py-3 text-sm ${col.align === 'right' ? 'text-right' : ''} ${col.cellClassName || ''}`}
                >
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
