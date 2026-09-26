import { createContext, useContext, useEffect, useState } from 'react'
import { api } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [status, setStatus] = useState('loading')
  const [user, setUser] = useState(null)

  useEffect(() => {
    const expire = () => {
      setUser(null)
      setStatus('unauthenticated')
    }
    window.addEventListener('satquery:unauthorized', expire)
    api.authMe().then(({ user: currentUser }) => {
      setUser(currentUser)
      setStatus('authenticated')
    }).catch(expire)
    return () => window.removeEventListener('satquery:unauthorized', expire)
  }, [])

  const logout = async () => {
    await api.logout()
    setUser(null)
    setStatus('unauthenticated')
  }

  const authenticate = (authenticatedUser) => {
    setUser(authenticatedUser)
    setStatus('authenticated')
  }

  return <AuthContext.Provider value={{ status, user, authenticate, logout }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}