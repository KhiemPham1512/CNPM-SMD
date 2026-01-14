import { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../store/authContext'
import { ROLES, Role, hasRole, hasAnyRole } from '../../constants/roles'

interface RoleGuardProps {
  children: ReactNode
  allowedRoles?: Role[]
  requireAll?: boolean
  fallbackPath?: string
}

/**
 * RoleGuard component - protects routes based on user roles
 * 
 * @param allowedRoles - Array of roles that can access this route
 * @param requireAll - If true, user must have ALL roles. If false (default), user needs ANY role
 * @param fallbackPath - Path to redirect if access denied (default: /app/dashboard)
 */
export function RoleGuard({ 
  children, 
  allowedRoles = [], 
  requireAll = false,
  fallbackPath = '/app/dashboard'
}: RoleGuardProps) {
  const { state } = useAuth()

  // If not authenticated, ProtectedRoute will handle redirect
  if (!state.isAuthenticated) {
    return null
  }

  // If no roles specified, allow all authenticated users
  if (allowedRoles.length === 0) {
    return <>{children}</>
  }

  // Check role access
  const hasAccess = requireAll
    ? allowedRoles.every(role => hasRole(state.roles, role))
    : hasAnyRole(state.roles, allowedRoles)

  if (!hasAccess) {
    // Redirect to fallback path (usually dashboard)
    return <Navigate to={fallbackPath} replace />
  }

  return <>{children}</>
}

/**
 * Pre-configured role guards for common use cases
 */
export const AdminGuard = ({ children }: { children: ReactNode }) => (
  <RoleGuard allowedRoles={[ROLES.ADMIN]}>{children}</RoleGuard>
)

export const LecturerGuard = ({ children }: { children: ReactNode }) => (
  <RoleGuard allowedRoles={[ROLES.LECTURER]}>{children}</RoleGuard>
)

export const HodGuard = ({ children }: { children: ReactNode }) => (
  <RoleGuard allowedRoles={[ROLES.HOD]}>{children}</RoleGuard>
)

export const AAGuard = ({ children }: { children: ReactNode }) => (
  <RoleGuard allowedRoles={[ROLES.AA]}>{children}</RoleGuard>
)

export const PrincipalGuard = ({ children }: { children: ReactNode }) => (
  <RoleGuard allowedRoles={[ROLES.PRINCIPAL]}>{children}</RoleGuard>
)

export const StaffGuard = ({ children }: { children: ReactNode }) => (
  <RoleGuard allowedRoles={[ROLES.ADMIN, ROLES.LECTURER, ROLES.HOD, ROLES.AA, ROLES.PRINCIPAL]}>
    {children}
  </RoleGuard>
)

export const StudentGuard = ({ children }: { children: ReactNode }) => (
  <RoleGuard allowedRoles={[ROLES.STUDENT]}>{children}</RoleGuard>
)
