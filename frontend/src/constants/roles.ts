/**
 * Role Constants for SMD System
 * 
 * Matches backend domain/constants.py
 * Exactly 6 roles as per SMD requirements
 */
export const ROLES = {
  ADMIN: 'ADMIN',
  LECTURER: 'LECTURER',
  HOD: 'HOD',
  AA: 'AA',
  PRINCIPAL: 'PRINCIPAL',
  STUDENT: 'STUDENT',
} as const

export type Role = typeof ROLES[keyof typeof ROLES]

export const ROLE_LABELS: Record<Role, string> = {
  [ROLES.ADMIN]: 'System Administrator',
  [ROLES.LECTURER]: 'Lecturer',
  [ROLES.HOD]: 'Head of Department',
  [ROLES.AA]: 'Academic Affairs',
  [ROLES.PRINCIPAL]: 'Principal',
  [ROLES.STUDENT]: 'Student',
}

/**
 * Check if user has a specific role
 */
export function hasRole(userRoles: string[], role: Role): boolean {
  return userRoles.includes(role)
}

/**
 * Check if user has any of the specified roles
 */
export function hasAnyRole(userRoles: string[], roles: Role[]): boolean {
  return roles.some(role => userRoles.includes(role))
}

/**
 * Check if user has all of the specified roles
 */
export function hasAllRoles(userRoles: string[], roles: Role[]): boolean {
  return roles.every(role => userRoles.includes(role))
}
