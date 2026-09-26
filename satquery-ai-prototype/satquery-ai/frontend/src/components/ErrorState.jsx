export default function ErrorState({ message, onRetry, onDismiss }) {
  if (!message) return null
  return (
    <div className="flex items-start justify-between gap-3 rounded-md border border-red-400/30 bg-red-400/10 px-3 py-2 text-sm text-red-200" role="alert">
      <span>{message}</span>
      <span className="flex shrink-0 gap-2">
        {onRetry && <button className="underline" onClick={onRetry}>Retry</button>}
        {onDismiss && <button aria-label="Dismiss" onClick={onDismiss}>✕</button>}
      </span>
    </div>
  )
}
