import { Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Dashboard from './pages/Dashboard'
import Analysis from './pages/Analysis'
import Demo from './pages/Demo'
import About from './pages/About'
import Models from './pages/Models'
import AuthPage from './pages/Auth'
import LoadingState from './components/LoadingState'
import { useAuth } from './context/AuthContext'

function ProtectedWorkspace() {
  const { status } = useAuth()
  const location = useLocation()
  if (status === 'loading') return <LoadingState label="Checking your session…" />
  if (status !== 'authenticated') return <Navigate to="/login" state={{ from: location }} replace />
  return <div className="flex min-h-screen flex-col md:flex-row"><Navbar /><main className="min-w-0 flex-1"><Outlet /></main></div>
}

function AuthRoute() {
  const { status } = useAuth()
  const location = useLocation()
  if (status === 'loading') return <LoadingState label="Checking your session…" />
  if (status === 'authenticated') return <Navigate to="/dashboard" replace />
  return <AuthPage key={location.pathname} />
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/about" element={<About />} />
      <Route path="/login" element={<AuthRoute />} />
      <Route path="/register" element={<AuthRoute />} />
      <Route path="/forgot-password" element={<AuthRoute />} />
      <Route path="/reset-password" element={<AuthRoute />} />
      <Route element={<ProtectedWorkspace />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/analysis" element={<Analysis />} />
        <Route path="/demo" element={<Demo />} />
        <Route path="/models" element={<Models />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
