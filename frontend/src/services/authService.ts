import { User } from '../types'
import { apiClient } from './apiClient'
import { storage, STORAGE_KEYS } from '../utils/storage'

export interface LoginCredentials {
  username: string
  password: string
}

export interface RegisterData {
  username: string
  password: string
  full_name: string
  email: string
}

interface LoginResponse {
  token: string
}

interface AuthMeResponse {
  user: User
  roles: string[]
}

class AuthService {
  async register(data: RegisterData): Promise<User> {
    const response = await apiClient.post<User>('/auth/register', {
      username: data.username,
      password: data.password,
      full_name: data.full_name,
      email: data.email,
    })

    if (!response.success || !response.data) {
      throw new Error(response.message || 'Registration failed')
    }

    return response.data
  }

  async login(credentials: LoginCredentials): Promise<{ user: User; token: string; roles: string[] }> {
    const response = await apiClient.post<LoginResponse>('/auth/login', {
      username: credentials.username,
      password: credentials.password,
    })

    if (!response.success || !response.data) {
      throw new Error(response.message || 'Login failed')
    }

    const token = response.data.token
    storage.set(STORAGE_KEYS.AUTH_TOKEN, token)

    const meResponse = await this.getCurrentUser()
    if (!meResponse) {
      throw new Error('Failed to get user info')
    }

    return { user: meResponse.user, token, roles: meResponse.roles }
  }

  logout(): void {
    storage.remove(STORAGE_KEYS.AUTH_TOKEN)
    storage.remove(STORAGE_KEYS.USER)
  }

  async getCurrentUser(): Promise<AuthMeResponse | null> {
    try {
      const response = await apiClient.get<AuthMeResponse>('/auth/me')
      if (response.success && response.data) {
        storage.set(STORAGE_KEYS.USER, response.data.user)
        return response.data
      }
      return null
    } catch {
      return null
    }
  }

  getStoredUser(): User | null {
    return storage.get<User>(STORAGE_KEYS.USER)
  }

  isAuthenticated(): boolean {
    return !!storage.get<string>(STORAGE_KEYS.AUTH_TOKEN)
  }
}

export const authService = new AuthService()
