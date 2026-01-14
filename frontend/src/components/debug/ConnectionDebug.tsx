import { useState } from 'react'
import { storage, STORAGE_KEYS } from '../../utils/storage'

export function ConnectionDebug() {
  const [result, setResult] = useState<string>('')
  const [testing, setTesting] = useState(false)

  const testConnection = async () => {
    setTesting(true)
    setResult('Testing...\n')
    
    try {
      const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:9999'
      const token = storage.get<string>(STORAGE_KEYS.AUTH_TOKEN)
      
      let info = `Frontend URL: ${window.location.origin}\n`
      info += `Backend URL: ${backendUrl}\n`
      info += `Has Token: ${token ? 'Yes' : 'No'}\n`
      info += `Token Length: ${token?.length || 0}\n\n`
      
      // Test 1: Simple fetch to backend
      info += 'Test 1: Fetching backend root...\n'
      try {
        const response = await fetch(backendUrl)
        info += `✓ Backend reachable (Status: ${response.status})\n`
      } catch (e) {
        info += `✗ Cannot reach backend: ${e instanceof Error ? e.message : String(e)}\n`
      }
      
      // Test 2: Test /docs endpoint
      info += '\nTest 2: Testing /docs endpoint...\n'
      try {
        const response = await fetch(`${backendUrl}/docs`)
        info += `✓ /docs accessible (Status: ${response.status})\n`
      } catch (e) {
        info += `✗ /docs not accessible: ${e instanceof Error ? e.message : String(e)}\n`
      }
      
      // Test 3: Test API endpoint with token
      if (token) {
        info += '\nTest 3: Testing /auth/me with token...\n'
        try {
          const response = await fetch(`${backendUrl}/auth/me`, {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            credentials: 'omit', // Match apiClient behavior
          })
          const contentType = response.headers.get('content-type')
          if (contentType && contentType.includes('application/json')) {
            const data = await response.json()
            if (response.ok) {
              info += `✓ Authentication successful\n`
              info += `  User: ${data.data?.user?.full_name || data.data?.full_name || 'N/A'}\n`
              info += `  Roles: ${data.data?.roles ? JSON.stringify(data.data.roles) : 'N/A'}\n`
            } else {
              info += `✗ Auth failed: ${data.message || response.statusText} (Status: ${response.status})\n`
            }
          } else {
            const text = await response.text()
            info += `✗ Auth returned non-JSON: ${response.status}\n`
            info += `  Response: ${text.substring(0, 100)}\n`
          }
        } catch (e) {
          info += `✗ Auth request failed: ${e instanceof Error ? e.message : String(e)}\n`
        }
      } else {
        info += '\nTest 3: Skipped (no token)\n'
      }
      
      // Test 4a: Test OPTIONS preflight for /users
      info += '\nTest 4a: Testing OPTIONS preflight for /users...\n'
      try {
        const preflightResponse = await fetch(`${backendUrl}/users`, {
          method: 'OPTIONS',
          headers: {
            'Origin': window.location.origin,
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Authorization, Content-Type',
          },
        })
        if (preflightResponse.ok || preflightResponse.status === 204) {
          info += `✓ OPTIONS preflight successful (Status: ${preflightResponse.status})\n`
          const acao = preflightResponse.headers.get('Access-Control-Allow-Origin')
          const acam = preflightResponse.headers.get('Access-Control-Allow-Methods')
          info += `  CORS Headers: Origin=${acao || 'N/A'}, Methods=${acam || 'N/A'}\n`
        } else {
          info += `✗ OPTIONS preflight failed (Status: ${preflightResponse.status})\n`
        }
      } catch (e) {
        info += `✗ OPTIONS preflight error: ${e instanceof Error ? e.message : String(e)}\n`
      }

      // Test 4b: Test /users endpoint
      if (token) {
        info += '\nTest 4b: Testing /users endpoint with GET...\n'
        try {
          const response = await fetch(`${backendUrl}/users`, {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            credentials: 'omit', // Match apiClient behavior
          })
          
          // Check if response is JSON
          const contentType = response.headers.get('content-type')
          if (contentType && contentType.includes('application/json')) {
            const data = await response.json()
            if (response.ok) {
              info += `✓ /users accessible\n`
              info += `  Users count: ${Array.isArray(data.data) ? data.data.length : 'N/A'}\n`
            } else {
              info += `✗ /users failed: ${data.message || response.statusText} (Status: ${response.status})\n`
              if (data.message) {
                info += `  Error details: ${JSON.stringify(data)}\n`
              }
            }
          } else {
            const text = await response.text()
            info += `✗ /users returned non-JSON: ${response.status} ${response.statusText}\n`
            info += `  Response: ${text.substring(0, 200)}\n`
          }
        } catch (e) {
          if (e instanceof TypeError) {
            const isNetworkError = 
              e.message.includes('fetch') ||
              e.message.includes('Failed to fetch') ||
              e.message.includes('NetworkError') ||
              e.message.includes('Network request failed')
            
            if (isNetworkError) {
              info += `✗ /users network error: ${e.message}\n`
              info += `  This usually indicates:\n`
              info += `  - CORS preflight failed (check backend CORS config)\n`
              info += `  - Backend endpoint not responding\n`
              info += `  - Network connectivity issue\n`
            } else {
              info += `✗ /users request failed: ${e.message}\n`
            }
          } else {
            info += `✗ /users request failed: ${e instanceof Error ? e.message : String(e)}\n`
          }
        }
      } else {
        info += '\nTest 4b: Skipped (no token)\n'
      }
      
      setResult(info)
    } catch (error) {
      setResult(`Error: ${error instanceof Error ? error.message : String(error)}`)
    } finally {
      setTesting(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Connection Debug</h3>
        <button
          onClick={testConnection}
          disabled={testing}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
        >
          {testing ? 'Testing...' : 'Test Connection'}
        </button>
      </div>
      {result && (
        <pre className="bg-gray-50 p-4 rounded border border-gray-200 text-sm font-mono whitespace-pre-wrap overflow-auto max-h-96">
          {result}
        </pre>
      )}
    </div>
  )
}
