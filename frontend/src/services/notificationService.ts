import { Notification } from '../types'
import { storage, STORAGE_KEYS } from '../utils/storage'

class NotificationService {
  private notifications: Notification[] = []

  constructor() {
    const stored = storage.get<Notification[]>(STORAGE_KEYS.NOTIFICATIONS)
    if (stored) {
      this.notifications = stored
    }
  }

  private save(): void {
    storage.set(STORAGE_KEYS.NOTIFICATIONS, this.notifications)
  }

  async list(userId?: number): Promise<Notification[]> {
    let results = [...this.notifications]
    if (userId) {
      results = results.filter(n => !n.userId || n.userId === userId)
    }
    return Promise.resolve(results.sort((a, b) => 
      new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    ))
  }

  async markAsRead(id: number): Promise<void> {
    const notification = this.notifications.find(n => n.id === id)
    if (notification) {
      notification.read = true
      this.save()
    }
    return Promise.resolve()
  }

  async markAllAsRead(userId?: number): Promise<void> {
    this.notifications.forEach(n => {
      if (!userId || !n.userId || n.userId === userId) {
        n.read = true
      }
    })
    this.save()
    return Promise.resolve()
  }

  async getUnreadCount(userId?: number): Promise<number> {
    let notifications = this.notifications
    if (userId) {
      notifications = notifications.filter(n => !n.userId || n.userId === userId)
    }
    const count = notifications.filter(n => !n.read).length
    return Promise.resolve(count)
  }
}

export const notificationService = new NotificationService()
