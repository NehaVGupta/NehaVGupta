export default function DatasetSelector({ datasets, active, onLoad, busy }) {
  return (
    <div className="space-y-2">
      <div className="text-sm font-medium">Demo datasets <span className="font-normal text-mist-500">(synthetic)</span></div>
      <ul className="space-y-1.5">
        {datasets.map((d) => (
          <li key={d.id}>
            <button disabled={busy} onClick={() => onLoad(d.id)} title={d.description}
              className={`w-full rounded-md border px-3 py-2 text-left text-xs transition-colors ${active === d.id ? 'border-signal/60 bg-signal/10' : 'border-ink-600 hover:bg-ink-700'}`}>
              <span className="block text-sm text-mist-100">{d.title}</span>
              <span className="text-mist-500">{d.images === 2 ? 'Image pair' : 'Single image'} · {d.category}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
