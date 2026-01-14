import { User } from '../types'
import { apiClient } from './apiClient'

class UserService {
  async list(): Promise<User[]> {
    const response = await apiClient.get<User[]>('/users')
    return response.data || []
  }

  async getById(id: number): Promise<User | null> {
    const response = await apiClient.get<User>(`/users/${id}`)
    return response.data || null
  }

  async create(data: {
    username: string
    password: string
    full_name: string
    email: string
    status?: string
  }): Promise<User> {
    const response = await apiClient.post<User>('/users', data)
    if (!response.success || !response.data) {
      throw new Error(response.message || 'Failed to create user')
    }
    return response.data
  }

  async updateStatus(id: number, status: string): Promise<User> {
    const response = await apiClient.put<User>(`/users/${id}/status`, { status })
    if (!response.success || !response.data) {
      throw new Error(response.message || 'Failed to update user status')
    }
    return response.data
  }

  async delete(id: number): Promise<void> {
    const response = await apiClient.delete(`/users/${id}`)
    if (!response.success) {
      throw new Error(response.message || 'Failed to delete user')
    }
  }

  async assignRole(id: number, roleName: string): Promise<User> {
    const response = await apiClient.post<User>(`/users/${id}/roles`, { role_name: roleName })
    if (!response.success || !response.data) {
      throw new Error(response.message || 'Failed to assign role')
    }
    return response.data
  }

  async removeRole(id: number, roleName: string): Promise<User> {
    const response = await apiClient.delete<User>(`/users/${id}/roles/${roleName}`)
    if (!response.success || !response.data) {
      throw new Error(response.message || 'Failed to remove role')
    }
    return response.data
  }

  async getUserRoles(id: number): Promise<string[]> {
    const response = await apiClient.get<string[]>(`/users/${id}/roles`)
    return response.data || []
  }
}

export const userService = new UserService()
