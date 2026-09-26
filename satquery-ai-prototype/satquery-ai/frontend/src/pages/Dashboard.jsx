import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../services/api'
import AnalysisHistory from '../components/AnalysisHistory'
import LoadingState from '../components/LoadingState'

const Stat = ({ label, value }) => (<div className="panel p-4"><div className="text-xs text-mist-500">{label}</div><div className="mt-1 font-display text-3xl">{value ?? '—'}</div></div>)

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [history, setHistory] = useState(null)

  useEffect(() => {
    api.stats(false).then(setStats).catch(() => setStats({}))
    api.history(false).then(setHistory).catch(() => setHistory([]))
  }, [])

  return (
    <div className="mx-auto max-w-[1200px] space-y-8 px-4 py-10">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div><h1 className="font-display text-3xl">Dashboard</h1><p className="text-sm text-mist-400">Recent activity across every analysis run in this environment.</p></div>
        <div className="flex flex-wrap gap-2">
          <Link to="/analysis" className="btn-ghost">Upload image</Link>
          <Link to="/analysis?compare=1" className="btn-ghost">Compare images</Link>
          <Link to="/demo" className="btn-primary">Open demo workspace</Link>
        </div>
      </div>
      {!stats ? <LoadingState label="Loading stats…" /> : (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <Stat label="Images analysed" value={stats.images_analyzed} /><Stat label="Queries executed" value={stats.queries_executed} />
          <Stat label="Objects detected" value={stats.objects_detected} /><Stat label="Changes detected" value={stats.changes_detected} />
          <Stat label="Avg. confidence" value={stats.avg_confidence != null ? `${Math.round(stats.avg_confidence * 100)}%` : '—'} />
          <Stat label="User uploads" value={stats.uploads} />
        </div>
      )}
      <div className="panel overflow-hidden"><div className="border-b border-ink-600 px-4 py-3 text-sm font-medium">Analysis history</div>{!history ? <LoadingState label="Loading history…" /> : <AnalysisHistory items={history} />}</div>
    </div>
  )
}
