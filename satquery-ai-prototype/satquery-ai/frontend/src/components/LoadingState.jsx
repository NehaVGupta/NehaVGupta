export default function LoadingState({ label = 'Analysing…' }) {
  return (
    <div className="flex items-center gap-3 text-sm text-mist-300" role="status" aria-live="polite">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-ink-600 border-t-signal" />
      {label}
    </div>
  )
}
