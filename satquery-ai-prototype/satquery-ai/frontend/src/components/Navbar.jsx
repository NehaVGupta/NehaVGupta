import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const links = [['/', 'Home'], ['/dashboard', 'Dashboard'], ['/analysis', 'Analysis'], ['/demo', 'Demo'], ['/models', 'Model monitoring']]

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
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [logoutError, setLogoutError] = useState('')
  const signOut = async () => {
    setLogoutError('')
    try {
      await logout()
      navigate('/login', { replace: true })
    } catch {
      setLogoutError('Could not sign out. Check your connection and try again.')
    }
  }

  return (
    <aside className="sticky top-0 z-[1000] flex w-full shrink-0 flex-col border-b border-ink-600 bg-ink-950 md:h-screen md:w-60 md:border-b-0 md:border-r">
      <div className="flex items-center justify-between gap-3 px-4 py-3 md:block md:px-5 md:py-6">
        <Link to="/" aria-label="SatQuery AI home"><Logo /></Link>
        <button type="button" onClick={signOut} className="text-sm text-mist-300 hover:text-mist-100 md:hidden">Sign out</button>
      </div>
      <nav className="flex gap-1 overflow-x-auto px-3 pb-3 md:flex-col md:px-3 md:pb-0" aria-label="Main">
        {links.map(([to, label]) => (
          <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => `shrink-0 rounded-md px-3 py-2 text-sm ${isActive ? 'bg-ink-700 text-mist-100' : 'text-mist-300 hover:bg-ink-800 hover:text-mist-100'}`}>{label}</NavLink>
        ))}
      </nav>
      <div className="mt-auto hidden border-t border-ink-600 p-4 md:block">
        <Link to="/analysis" className="btn-primary w-full">Open analysis</Link>
        <div className="mt-4 border-t border-ink-600 pt-4">
          <p className="truncate text-sm font-medium text-mist-100">{user?.name}</p>
          <p className="mt-1 truncate text-xs text-mist-500">{user?.email}</p>
        </div>
        <button type="button" onClick={signOut} className="btn-ghost mt-3 w-full">Sign out</button>
        {logoutError && <p role="alert" className="mt-2 text-xs text-amber-flag">{logoutError}</p>}
        <p className="mt-5 font-mono text-[10px] uppercase tracking-wider text-mist-700">Prototype workspace</p>
      </div>
    </aside>
  )
}
