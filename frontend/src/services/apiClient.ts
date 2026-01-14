import { storage, STORAGE_KEYS } from '../utils/storage'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:9999'

// Log API URL for debugging (only in development)
if (import.meta.env.DEV) {
  console.log('[API Client] Base URL:', API_BASE_URL)
  console.log('[API Client] VITE_API_URL from env:', import.meta.env.VITE_API_URL)
}

export interface ApiResponse<T> {
  success: boolean
  data?: T
  message?: string
  errors?: any
}

class ApiClient {
  private baseURL: string

  constructor(baseURL: string) {
    this.baseURL = baseURL
    if (import.meta.env.DEV) {
      console.log('[API Client] Initialized with base URL:', this.baseURL)
    }
  }

  private getAuthToken(): string | null {
    return storage.get<string>(STORAGE_KEYS.AUTH_TOKEN)
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const token = this.getAuthToken()
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const url = `${this.baseURL}${endpoint}`

    if (import.meta.env.DEV) {
      console.log('[API Client] Requesting:', url, { method: options.method || 'GET', hasToken: !!token })
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        // Add credentials for CORS
        credentials: 'omit',
      })

      // Check if response is JSON
      const contentType = response.headers.get('content-type')
      let data: ApiResponse<T>

      if (contentType && contentType.includes('application/json')) {
        try {
          data = await response.json()
        } catch (jsonError) {
          throw new Error(`Invalid JSON response from ${url}. Status: ${response.status}`)
        }
      } else {
        // Non-JSON response (e.g., 204 No Content)
        if (response.status === 204) {
          return { success: true } as ApiResponse<T>
        }
        const text = await response.text()
        throw new Error(`Unexpected response format from ${url}. Status: ${response.status}. Response: ${text.substring(0, 100)}`)
      }

      if (!response.ok) {
        const errorMessage = data.message || `HTTP error! status: ${response.status}`
        throw new Error(errorMessage)
      }

      return data
    } catch (error) {
      // Handle network errors (CORS, connection refused, timeout, etc.)
      if (error instanceof TypeError) {
        const isNetworkError = 
          error.message.includes('fetch') ||
          error.message.includes('Failed to fetch') ||
          error.message.includes('NetworkError') ||
          error.message.includes('Network request failed')
        
        if (isNetworkError) {
          throw new Error(
            `Cannot connect to backend at ${this.baseURL}. ` +
            `Please ensure: 1) Backend server is running, ` +
            `2) Backend URL is correct (check VITE_API_URL in .env), ` +
            `3) CORS is enabled for ${window.location.origin}`
          )
        }
      }
      
      // Re-throw existing Error instances
      if (error instanceof Error) {
        throw error
      }
      
      // Handle unknown errors
      throw new Error(`Unknown error occurred while calling ${url}: ${String(error)}`)
    }
  }

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET' })
  }

  async post<T>(endpoint: string, body?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    })
  }

  async put<T>(endpoint: string, body?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    })
  }

  async patch<T>(endpoint: string, body?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    })
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' })
  }
}

export const apiClient = new ApiClient(API_BASE_URL)
