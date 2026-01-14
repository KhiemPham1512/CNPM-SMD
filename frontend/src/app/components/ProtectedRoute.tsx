import { Outlet, Navigate } from 'react-router-dom'
import { useAuth } from '../store/authContext'
import { AppShell } from '../../components/layout/AppShell'

export function ProtectedRoute() {
  const { state } = useAuth()

  if (state.loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mb-4"></div>
          <p className="text-gray-500">Loading...</p>
        </div>
      </div>
    )
  }

  if (!state.isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return (
    <AppShell>
      <Outlet />
    </AppShell>
  )
}
