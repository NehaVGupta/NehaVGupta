import { Link, NavLink, useNavigate } from 'react-router-dom'

const links = [['/', 'Home'], ['/dashboard', 'Dashboard'], ['/analysis', 'Analysis'], ['/architecture', 'Architecture'], ['/models', 'Model monitoring']]

export function Logo() {
  return (
    <span className="flex items-center gap-2 font-display text-lg font-semibold tracking-tight">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#3dc9b0" strokeWidth="1.6" aria-hidden="true">
        <circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18" /><rect x="8" y="8" width="8" height="8" strokeDasharray="2 2" />
      </svg>
      SatQuery AI
    </span>
  )
}

export default function Navbar() {
  const nav = useNavigate()
  return (
    <header className="sticky top-0 z-[1000] border-b border-ink-600 bg-ink-950/90 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-[1600px] items-center justify-between gap-4 px-4">
        <Link to="/" aria-label="SatQuery AI home"><Logo /></Link>
        <nav className="hidden items-center gap-1 md:flex" aria-label="Main">
          {links.map(([to, label]) => (
            <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => `rounded-md px-3 py-1.5 text-sm ${isActive ? 'bg-ink-700 text-mist-100' : 'text-mist-300 hover:text-mist-100'}`}>{label}</NavLink>
          ))}
        </nav>
        <button className="btn-primary !py-1.5" onClick={() => nav('/analysis')}>Open analysis</button>
      </div>
    </header>
  )
}
