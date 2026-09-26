import { useState } from 'react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { Logo } from '../components/Navbar'
import { useAuth } from '../context/AuthContext'
import { api } from '../services/api'
import { passwordRequirements } from '../services/auth'

function PasswordField({ id, label, value, onChange, autoComplete, showRequirements = false }) {
  const [visible, setVisible] = useState(false)
  const requirements = passwordRequirements(value)

  return (
    <div>
      <label htmlFor={id} className="mb-2 block text-sm text-mist-300">{label}</label>
      <div className="flex rounded-md border border-ink-600 bg-ink-900 focus-within:border-signal focus-within:ring-1 focus-within:ring-signal">
        <input id={id} type={visible ? 'text' : 'password'} value={value} onChange={onChange} autoComplete={autoComplete}
          required minLength={showRequirements ? 8 : 1} maxLength={128}
          className="min-w-0 flex-1 rounded-l-md bg-transparent px-3 py-2.5 text-mist-100 outline-none" />
        <button type="button" onClick={() => setVisible((shown) => !shown)} aria-label={`${visible ? 'Hide' : 'Show'} ${label.toLowerCase()}`}
          className="flex w-12 shrink-0 items-center justify-center text-mist-400 hover:text-mist-100">
          <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true">
            <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z" />
            <circle cx="12" cy="12" r="3" />
            {visible && <path d="m4 4 16 16" />}
          </svg>
        </button>
      </div>
      {showRequirements && (
        <ul className="mt-3 grid gap-1 text-xs sm:grid-cols-2">
          {requirements.map(([text, met]) => (
            <li key={text} className={met ? 'text-signal' : 'text-mist-500'}><span aria-hidden="true">{met ? '✓' : '○'}</span> {text}</li>
          ))}
        </ul>
      )}
    </div>
  )
}

function TextField({ id, label, type = 'text', value, onChange, autoComplete }) {
  return (
    <label htmlFor={id} className="block text-sm text-mist-300">
      <span className="mb-2 block">{label}</span>
      <input id={id} type={type} value={value} onChange={onChange} autoComplete={autoComplete} required maxLength={254}
        className="w-full rounded-md border border-ink-600 bg-ink-900 px-3 py-2.5 text-mist-100 outline-none focus:border-signal focus:ring-1 focus:ring-signal" />
    </label>
  )
}

export default function AuthPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { authenticate } = useAuth()
  const mode = location.pathname === '/register' ? 'register'
    : location.pathname === '/forgot-password' ? 'forgot'
      : location.pathname === '/reset-password' ? 'reset' : 'login'
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [rememberMe, setRememberMe] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState(location.state?.message || '')
  const resetToken = searchParams.get('token') || ''

  const title = mode === 'register' ? 'Create your account'
    : mode === 'forgot' ? 'Reset your password'
      : mode === 'reset' ? 'Choose a new password' : 'Welcome back'

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setMessage('')
    if ((mode === 'register' || mode === 'reset') && password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    if ((mode === 'register' || mode === 'reset') && passwordRequirements(password).some(([, met]) => !met)) {
      setError('Please meet all password requirements.')
      return
    }
    setLoading(true)
    try {
      if (mode === 'login') {
        const result = await api.login({ email, password, remember_me: rememberMe })
        authenticate(result.user)
        const from = location.state?.from
        navigate(from ? `${from.pathname}${from.search || ''}${from.hash || ''}` : '/dashboard', { replace: true })
      } else if (mode === 'register') {
        await api.register({ full_name: name, email, password, confirm_password: confirmPassword })
        navigate('/login', { replace: true, state: { message: 'Account created. Sign in with your new credentials.' } })
      } else if (mode === 'forgot') {
        const result = await api.forgotPassword({ email })
        setMessage(result.message)
      } else {
        const result = await api.resetPassword({ token: resetToken, new_password: password, confirm_password: confirmPassword })
        setMessage(result.message)
      }
    } catch (requestError) {
      setError(requestError.message || 'We could not complete your request. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="grid min-h-screen bg-ink-950 lg:grid-cols-2">
      <section className="relative hidden min-h-screen overflow-hidden border-r border-ink-600 lg:block">
        <img src="/samples/urban.png" alt="Illustrative urban sample imagery" className="absolute inset-0 h-full w-full object-cover opacity-55" />
        <div className="absolute inset-0 bg-gradient-to-t from-ink-950 via-ink-950/40 to-ink-950/10" />
        <div className="absolute inset-x-0 bottom-0 p-12">
          <Link to="/" aria-label="SatQuery AI home"><Logo /></Link>
          <p className="mt-16 max-w-xl font-display text-4xl leading-tight">A clearer view of our changing world.</p>
          <p className="mt-4 max-w-md text-sm leading-6 text-mist-300">Explore satellite imagery with focused analysis and evidence you can inspect.</p>
          <p className="mt-8 font-mono text-[10px] uppercase tracking-wider text-mist-500">Illustrative sample scene · prototype environment</p>
        </div>
      </section>

      <section className="flex min-h-screen items-center justify-center px-5 py-10 sm:px-10">
        <div className="w-full max-w-md">
          <div className="mb-10 flex items-center justify-between lg:hidden">
            <Link to="/" aria-label="SatQuery AI home"><Logo /></Link>
            <Link to="/" className="text-sm text-mist-400 hover:text-mist-100">Home</Link>
          </div>
          <p className="font-mono text-xs uppercase tracking-[0.16em] text-signal">SatQuery AI workspace</p>
          <h1 className="mt-3 font-display text-3xl font-medium">{title}</h1>
          <p className="mt-2 text-sm leading-6 text-mist-400">
            {mode === 'register' ? 'Create an account to access your analysis workspace.'
              : mode === 'forgot' ? 'Enter your email and we will send a reset link if an account exists.'
                : mode === 'reset' ? 'Use a strong password you have not used elsewhere.'
                  : 'Sign in to continue to your geospatial workspace.'}
          </p>

          {mode === 'reset' && !resetToken ? (
            <div className="mt-8 rounded-md border border-amber-flag/30 bg-amber-flag/5 p-4 text-sm text-amber-flag">
              This reset link is missing or invalid. Request a new one from the forgot-password page.
            </div>
          ) : message && mode === 'reset' ? (
            <div className="mt-8 rounded-md border border-signal/30 bg-signal/5 p-4 text-sm text-signal" role="status">
              {message} <Link to="/login" className="underline">Back to Login</Link>
            </div>
          ) : (
            <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
              {mode === 'register' && <TextField id="full-name" label="Full name" value={name} onChange={(event) => setName(event.target.value)} autoComplete="name" />}
              <TextField id="email" label="Email address" type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" />
              {mode !== 'forgot' && <PasswordField id="password" label={mode === 'reset' ? 'New password' : 'Password'} value={password} onChange={(event) => setPassword(event.target.value)} autoComplete={mode === 'login' ? 'current-password' : 'new-password'} showRequirements={mode === 'register' || mode === 'reset'} />}
              {(mode === 'register' || mode === 'reset') && <PasswordField id="confirm-password" label={mode === 'reset' ? 'Confirm new password' : 'Confirm password'} value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} autoComplete="new-password" />}
              {mode === 'login' && (
                <div className="flex items-center justify-between gap-3 text-sm">
                  <label className="flex items-center gap-2 text-mist-300">
                    <input type="checkbox" checked={rememberMe} onChange={(event) => setRememberMe(event.target.checked)} className="h-4 w-4 accent-signal" />
                    Remember me
                  </label>
                  <Link to="/forgot-password" className="text-signal hover:underline">Forgot password?</Link>
                </div>
              )}
              {error && <p role="alert" className="rounded-md border border-red-400/30 bg-red-400/5 px-3 py-2.5 text-sm text-red-200">{error}</p>}
              {message && <p role="status" className="rounded-md border border-signal/30 bg-signal/5 px-3 py-2.5 text-sm text-signal">{message}</p>}
              <button type="submit" disabled={loading || (mode === 'reset' && !resetToken)} className="btn-primary w-full disabled:cursor-not-allowed disabled:opacity-50">
                {loading ? 'Please wait…' : mode === 'register' ? 'Create account' : mode === 'forgot' ? 'Send reset link' : mode === 'reset' ? 'Reset password' : 'Sign in'}
              </button>
            </form>
          )}

          <p className="mt-6 text-center text-sm text-mist-400">
            {mode === 'login' ? <>New to SatQuery AI? <Link to="/register" className="text-signal hover:underline">Create an account</Link></>
              : mode === 'register' ? <>Already have an account? <Link to="/login" className="text-signal hover:underline">Sign in</Link></>
                : mode === 'forgot' ? <Link to="/login" className="text-signal hover:underline">Back to Login</Link>
                  : mode === 'reset' && !message ? <Link to="/forgot-password" className="text-signal hover:underline">Request another reset link</Link> : null}
          </p>
          <p className="mt-8 border-t border-ink-600 pt-5 text-xs leading-5 text-mist-500">SatQuery AI prototype. Accounts are stored by this backend; password reset emails require SMTP configuration.</p>
        </div>
      </section>
    </main>
  )
}