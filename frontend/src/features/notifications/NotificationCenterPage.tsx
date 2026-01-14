import { useEffect } from 'react'
import { useNotifications } from '../../app/store/notificationContext'
import { formatRelativeTime } from '../../utils/date'
import { Button } from '../../components/ui/Button'

export function NotificationCenterPage() {
  const { state, loadNotifications, markAsRead, markAllAsRead } = useNotifications()

  useEffect(() => {
    loadNotifications()
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Notifications</h1>
          <p className="text-gray-600">Manage your notifications</p>
        </div>
        {state.unreadCount > 0 && (
          <Button onClick={markAllAsRead}>Mark all as read</Button>
        )}
      </div>

      <div className="bg-white rounded-lg shadow divide-y divide-gray-200 border border-gray-200">
        {state.notifications.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No notifications</div>
        ) : (
          state.notifications.map(notification => (
            <div
              key={notification.id}
              className={`p-6 hover:bg-gray-50 transition-colors ${
                !notification.read ? 'bg-blue-50' : ''
              }`}
            >
              <div className="flex items-start space-x-4">
                <div className={`flex-shrink-0 w-2 h-2 rounded-full mt-2 ${
                  notification.read ? 'bg-gray-300' : 'bg-primary-500'
                }`} />
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium text-gray-900">{notification.title}</h3>
                    <span className="text-xs text-gray-500">
                      {formatRelativeTime(notification.createdAt)}
                    </span>
                  </div>
                  <p className="text-gray-600 mt-2">{notification.content}</p>
                  {!notification.read && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="mt-3"
                      onClick={() => markAsRead(notification.id)}
                    >
                      Mark as read
                    </Button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
