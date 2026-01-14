import { createContext, useContext, useReducer, useEffect, ReactNode } from 'react'
import { User } from '../../types'
import { authService } from '../../services/authService'

interface AuthState {
  user: User | null
  roles: string[]
  isAuthenticated: boolean
  loading: boolean
}

type AuthAction =
  | { type: 'LOGIN_START' }
  | { type: 'LOGIN_SUCCESS'; payload: { user: User; roles: string[] } }
  | { type: 'LOGIN_FAILURE' }
  | { type: 'LOGOUT' }
  | { type: 'CHECK_AUTH_START' }
  | { type: 'CHECK_AUTH_SUCCESS'; payload: { user: User; roles: string[] } }
  | { type: 'CHECK_AUTH_FAILURE' }

const initialState: AuthState = {
  user: null,
  roles: [],
  isAuthenticated: false,
  loading: true,
}

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'LOGIN_START':
    case 'CHECK_AUTH_START':
      return { ...state, loading: true }
    case 'LOGIN_SUCCESS':
    case 'CHECK_AUTH_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        roles: action.payload.roles,
        isAuthenticated: true,
        loading: false,
      }
    case 'LOGIN_FAILURE':
    case 'CHECK_AUTH_FAILURE':
      return {
        ...state,
        user: null,
        roles: [],
        isAuthenticated: false,
        loading: false,
      }
    case 'LOGOUT':
      return {
        ...state,
        user: null,
        roles: [],
        isAuthenticated: false,
        loading: false,
      }
    default:
      return state
  }
}

interface AuthContextType {
  state: AuthState
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(authReducer, initialState)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    dispatch({ type: 'CHECK_AUTH_START' })
    try {
      const result = await authService.getCurrentUser()
      if (result) {
        dispatch({ type: 'CHECK_AUTH_SUCCESS', payload: { user: result.user, roles: result.roles } })
      } else {
        dispatch({ type: 'CHECK_AUTH_FAILURE' })
      }
    } catch {
      dispatch({ type: 'CHECK_AUTH_FAILURE' })
    }
  }

  const login = async (username: string, password: string) => {
    dispatch({ type: 'LOGIN_START' })
    try {
      const { user, roles } = await authService.login({ username, password })
      dispatch({ type: 'LOGIN_SUCCESS', payload: { user, roles } })
    } catch (error) {
      dispatch({ type: 'LOGIN_FAILURE' })
      throw error
    }
  }

  const logout = () => {
    authService.logout()
    dispatch({ type: 'LOGOUT' })
  }

  return (
    <AuthContext.Provider value={{ state, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
