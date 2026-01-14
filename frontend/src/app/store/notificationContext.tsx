import { createContext, useContext, useReducer, useEffect, ReactNode } from 'react'
import { Notification } from '../../types'
import { notificationService } from '../../services/notificationService'
import { AuthContext } from './authContext'

interface NotificationState {
  notifications: Notification[]
  unreadCount: number
  loading: boolean
}

type NotificationAction =
  | { type: 'LOAD_START' }
  | { type: 'LOAD_SUCCESS'; payload: Notification[] }
  | { type: 'MARK_READ'; payload: number }
  | { type: 'MARK_ALL_READ' }
  | { type: 'UPDATE_COUNT'; payload: number }

const initialState: NotificationState = {
  notifications: [],
  unreadCount: 0,
  loading: false,
}

function notificationReducer(
  state: NotificationState,
  action: NotificationAction
): NotificationState {
  switch (action.type) {
    case 'LOAD_START':
      return { ...state, loading: true }
    case 'LOAD_SUCCESS':
      return {
        ...state,
        notifications: action.payload,
        unreadCount: action.payload.filter(n => !n.read).length,
        loading: false,
      }
    case 'MARK_READ':
      return {
        ...state,
        notifications: state.notifications.map(n =>
          n.id === action.payload ? { ...n, read: true } : n
        ),
        unreadCount: Math.max(0, state.unreadCount - 1),
      }
    case 'MARK_ALL_READ':
      return {
        ...state,
        notifications: state.notifications.map(n => ({ ...n, read: true })),
        unreadCount: 0,
      }
    case 'UPDATE_COUNT':
      return { ...state, unreadCount: action.payload }
    default:
      return state
  }
}

interface NotificationContextType {
  state: NotificationState
  loadNotifications: () => Promise<void>
  markAsRead: (id: number) => Promise<void>
  markAllAsRead: () => Promise<void>
  refreshCount: () => Promise<void>
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined)

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(notificationReducer, initialState)
  const authContext = useContext(AuthContext)
  const authState = authContext?.state || { isAuthenticated: false, user: null, roles: [] }

  useEffect(() => {
    if (authState.isAuthenticated && authState.user) {
      loadNotifications()
      refreshCount()
    }
  }, [authState.isAuthenticated, authState.user?.user_id])

  const loadNotifications = async () => {
    dispatch({ type: 'LOAD_START' })
    const notifications = await notificationService.list(authState.user?.user_id)
    dispatch({ type: 'LOAD_SUCCESS', payload: notifications })
  }

  const markAsRead = async (id: number) => {
    await notificationService.markAsRead(id)
    dispatch({ type: 'MARK_READ', payload: id })
    refreshCount()
  }

  const markAllAsRead = async () => {
    await notificationService.markAllAsRead(authState.user?.user_id)
    dispatch({ type: 'MARK_ALL_READ' })
    refreshCount()
  }

  const refreshCount = async () => {
    const count = await notificationService.getUnreadCount(authState.user?.user_id)
    dispatch({ type: 'UPDATE_COUNT', payload: count })
  }

  return (
    <NotificationContext.Provider
      value={{
        state,
        loadNotifications,
        markAsRead,
        markAllAsRead,
        refreshCount,
      }}
    >
      {children}
    </NotificationContext.Provider>
  )
}

export function useNotifications() {
  const context = useContext(NotificationContext)
  if (context === undefined) {
    throw new Error('useNotifications must be used within a NotificationProvider')
  }
  return context
}
