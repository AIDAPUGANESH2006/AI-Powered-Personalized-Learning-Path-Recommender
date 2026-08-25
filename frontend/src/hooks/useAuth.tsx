import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { login as apiLogin, register as apiRegister } from '../services/api'

interface AuthState {
  token: string | null
  isAuthenticated: boolean
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem('pathwise_token'),
  )

  useEffect(() => {
    if (token) {
      localStorage.setItem('pathwise_token', token)
    } else {
      localStorage.removeItem('pathwise_token')
    }
  }, [token])

  const login = useCallback(async (email: string, password: string) => {
    const data = await apiLogin(email, password)
    setToken(data.access_token)
  }, [])

  const register = useCallback(async (email: string, password: string) => {
    await apiRegister(email, password)
    // auto-login after registration
    const data = await apiLogin(email, password)
    setToken(data.access_token)
  }, [])

  const logout = useCallback(() => {
    setToken(null)
  }, [])

  return (
    <AuthContext.Provider
      value={{ token, isAuthenticated: !!token, login, register, logout }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
