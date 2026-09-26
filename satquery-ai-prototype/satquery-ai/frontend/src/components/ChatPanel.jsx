import { useEffect, useRef, useState } from 'react'
import ConfidenceBadge from './ConfidenceBadge'
import LoadingState from './LoadingState'

function Message({ m, active, onOpen }) {
  if (m.role === 'user') return <div className="ml-8 rounded-lg bg-ink-700 px-3 py-2 text-sm">{m.text}</div>
  const r = m.record
  const flag = r && (r.status === 'insufficient' || r.status === 'unsupported' || r.status === 'needs_input')
  return (
    <div className={`mr-4 rounded-lg border px-3 py-2 text-sm ${active ? 'border-signal/50 bg-signal/5' : 'border-ink-600 bg-ink-900'} ${m.error ? 'border-red-400/40' : ''}`}>
      <p className={flag ? 'text-amber-flag' : ''}>{m.text}</p>
      {r && (
        <div className="mt-2 flex flex-wrap items-center gap-2">
          {r.confidence != null && <ConfidenceBadge value={r.confidence} tier={r.confidence_tier} compact />}
          {r.evidence?.count > 0 && <span className="chip">{r.evidence.count} evidence item{r.evidence.count > 1 ? 's' : ''}</span>}
          <span className="chip" title={r.engine_label}>{r.is_demo ? 'Prototype inference' : 'Model inference'}</span>
          <button className="ml-auto text-xs text-signal hover:underline" onClick={() => onOpen(r)}>View evidence</button>
        </div>
      )}
    </div>
  )
}

export default function ChatPanel({ messages, onSend, loading, suggestions = [], selectedId, onOpen, disabled }) {
  const [text, setText] = useState('')
  const end = useRef()
  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [messages, loading])
  const submit = (e) => { e.preventDefault(); if (text.trim() && !loading) { onSend(text); setText('') } }
  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-ink-600 px-4 py-3"><h2 className="font-display text-lg">Ask about this imagery</h2><p className="text-xs text-mist-500">Answers come only from measured evidence.</p></div>
      <div className="flex-1 space-y-3 overflow-y-auto p-4" aria-live="polite">
        {messages.length === 0 && <p className="text-sm text-mist-500">Try a suggested question below, or ask in your own words — e.g. “How many buildings are visible?”</p>}
        {messages.map((m, i) => <Message key={i} m={m} active={m.record?.id === selectedId} onOpen={onOpen} />)}
        {loading && <LoadingState label="Routing query to specialist model…" />}
        <div ref={end} />
      </div>
      {suggestions.length > 0 && (
        <div className="flex max-h-28 flex-wrap gap-1.5 overflow-y-auto border-t border-ink-600 px-4 py-2">
          {suggestions.map((s) => <button key={s} disabled={loading || disabled} onClick={() => onSend(s)} className="chip hover:border-signal hover:text-mist-100 disabled:opacity-40">{s}</button>)}
        </div>
      )}
      <form onSubmit={submit} className="flex gap-2 border-t border-ink-600 p-3">
        <input value={text} onChange={(e) => setText(e.target.value)} maxLength={500} placeholder="Ask a question about the imagery…" aria-label="Question"
          className="min-w-0 flex-1 rounded-md border border-ink-600 bg-ink-900 px-3 py-2 text-sm outline-none focus:border-signal" />
        <button className="btn-primary" disabled={loading || !text.trim()}>Ask</button>
      </form>
    </div>
  )
}
