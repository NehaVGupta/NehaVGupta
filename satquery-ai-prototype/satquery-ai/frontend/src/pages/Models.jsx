import { useEffect, useState } from 'react'
import { api } from '../services/api'
import LoadingState from '../components/LoadingState'

export default function Models() {
  const [data, setData] = useState(null)
  useEffect(() => { api.models().then(setData).catch(() => setData({ models: [] })) }, [])
  if (!data) return <div className="p-10"><LoadingState label="Loading model registry…" /></div>
  const active = data.models.filter((m) => m.status === 'active')
  const planned = data.models.filter((m) => m.status === 'planned')
  return (
    <div className="mx-auto max-w-[1000px] space-y-8 px-4 py-12">
      <div><h1 className="font-display text-3xl">Model monitoring</h1><p className="mt-2 text-sm text-mist-400">Admin view of available models and their live call performance in this session. Cache: <span className="font-mono">{data.cache}</span> · Storage: <span className="font-mono">{data.storage}</span></p></div>
      <div className="overflow-hidden rounded-lg border border-ink-600">
        <table className="w-full text-left text-sm">
          <thead className="bg-ink-700 text-xs text-mist-300"><tr><th className="px-3 py-2">Model</th><th>Kind</th><th>Type</th><th>Calls</th><th>Errors</th><th>Avg latency</th></tr></thead>
          <tbody>
            {active.map((m) => (
              <tr key={m.kind} className="border-t border-ink-600">
                <td className="px-3 py-2"><div>{m.name}</div><div className="text-xs text-mist-500">{m.label}</div></td>
                <td>{m.kind.replace(/_/g, ' ')}</td><td>{m.is_demo ? <span className="chip">Prototype</span> : <span className="chip !border-signal/50 !text-signal">Trained model</span>}</td>
                <td className="font-mono">{m.calls}</td><td className="font-mono">{m.errors}</td><td className="font-mono">{m.avg_latency_ms != null ? `${m.avg_latency_ms} ms` : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div><h2 className="font-display text-lg">Planned real-model adapters</h2>
        <ul className="mt-3 grid gap-2 sm:grid-cols-2">{planned.map((m) => (<li key={m.name} className="panel p-3 text-sm"><div>{m.name}</div><div className="text-xs text-mist-500">{m.label}</div></li>))}</ul>
      </div>
    </div>
  )
}
