import { apiClient } from './apiClient'

interface SystemSetting {
  [key: string]: string
}

interface PublishedSyllabus {
  syllabus_id: number
  subject_id: number
  program_id: number
  owner_lecturer_id: number
  current_version_id: number | null
  lifecycle_status: string
  created_at: string
}

class AdminService {
  async listUsers(): Promise<any[]> {
    const response = await apiClient.get<any[]>('/admin/users')
    return response.data || []
  }

  async createUser(data: {
    username: string
    password: string
    full_name: string
    email: string
    status?: string
  }): Promise<any> {
    const response = await apiClient.post<any>('/users', data)
    if (!response.success || !response.data) {
      throw new Error(response.message || 'Failed to create user')
    }
    return response.data
  }

  async updateUserStatus(userId: number, status: string): Promise<any> {
    const response = await apiClient.put<any>(`/users/${userId}/status`, { status })
    if (!response.success || !response.data) {
      throw new Error(response.message || 'Failed to update user status')
    }
    return response.data
  }

  async assignRoles(userId: number, roles: string[]): Promise<any> {
    const response = await apiClient.put<any>(`/admin/users/${userId}/roles`, { roles })
    if (!response.success || !response.data) {
      throw new Error(response.message || 'Failed to assign roles')
    }
    return response.data
  }

  async getSystemSettings(): Promise<SystemSetting> {
    const response = await apiClient.get<SystemSetting>('/admin/system-settings')
    return response.data || {}
  }

  async updateSystemSettings(settings: SystemSetting): Promise<SystemSetting> {
    const response = await apiClient.put<SystemSetting>('/admin/system-settings', settings)
    if (!response.success || !response.data) {
      throw new Error(response.message || 'Failed to update system settings')
    }
    return response.data
  }

  async listPublished(): Promise<PublishedSyllabus[]> {
    const response = await apiClient.get<PublishedSyllabus[]>('/admin/publishing')
    return response.data || []
  }

  async unpublishVersion(versionId: number): Promise<any> {
    const response = await apiClient.post<any>(`/admin/publishing/${versionId}/unpublish`)
    if (!response.success || !response.data) {
      throw new Error(response.message || 'Failed to unpublish')
    }
    return response.data
  }

  async archiveVersion(versionId: number): Promise<any> {
    const response = await apiClient.post<any>(`/admin/publishing/${versionId}/archive`)
    if (!response.success || !response.data) {
      throw new Error(response.message || 'Failed to archive')
    }
    return response.data
  }
}

export const adminService = new AdminService()
