export const DEMO_STEPS = [
  { dataset: 'urban', q: 'How many buildings are visible?', note: 'Object detection → boxes + confidence' },
  { dataset: 'urban', q: 'Which detected regions have low confidence?', note: 'Follow-up using conversation context' },
  { dataset: 'urban', q: 'What percentage of the image is vegetation?', note: 'Segmentation mask + area' },
  { dataset: 'urban', q: 'Show me the water bodies.', note: 'Segmentation overlay' },
  { dataset: 'before-after', q: 'What changed between these two images?', note: 'Change detection (before / after / change map)' },
  { dataset: 'before-after', q: 'How many buildings changed?', note: 'Two models cross-checked' },
  { dataset: 'before-after', q: 'Which ones are new?', note: 'Follow-up' },
  { dataset: 'before-after', q: 'Show them.', note: 'Highlights the 3 new regions' },
  { dataset: 'before-after', q: 'What evidence supports this answer?', note: 'Explainability' },
  { dataset: 'urban', q: 'Are there any aircraft?', note: 'Insufficient evidence is a feature' },
]

export default function DemoGuide({ current, onRun, onClose, busy }) {
  return (
    <div className="rounded-lg border border-signal/30 bg-signal/5 p-3">
      <div className="mb-2 flex items-center justify-between"><h3 className="text-sm font-medium">Judge demo · ~4 min</h3><button onClick={onClose} className="text-xs text-mist-500 hover:text-mist-100">Hide</button></div>
      <ol className="space-y-1">
        {DEMO_STEPS.map((s, i) => (
          <li key={i}>
            <button disabled={busy} onClick={() => onRun(i)} className={`w-full rounded-md px-2 py-1.5 text-left text-xs hover:bg-ink-700 disabled:opacity-50 ${current === i ? 'bg-ink-700 text-mist-100' : 'text-mist-300'}`}>
              <span className="text-mist-100">{i + 1}. {s.q}</span><span className="block text-mist-500">{s.note}</span>
            </button>
          </li>
        ))}
      </ol>
    </div>
  )
}
