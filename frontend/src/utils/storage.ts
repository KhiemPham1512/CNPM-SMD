const STORAGE_KEYS = {
  AUTH_TOKEN: 'smd_auth_token',
  USER: 'smd_user',
  SYLLABI: 'smd_syllabi',
  NOTIFICATIONS: 'smd_notifications',
  SUBSCRIPTIONS: 'smd_subscriptions',
} as const

export const storage = {
  get: <T>(key: string): T | null => {
    try {
      const item = localStorage.getItem(key)
      return item ? JSON.parse(item) : null
    } catch {
      return null
    }
  },
  set: <T>(key: string, value: T): void => {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch (error) {
      console.error('Storage set error:', error)
    }
  },
  remove: (key: string): void => {
    localStorage.removeItem(key)
  },
  clear: (): void => {
    Object.values(STORAGE_KEYS).forEach(key => localStorage.removeItem(key))
  },
}

export { STORAGE_KEYS }
