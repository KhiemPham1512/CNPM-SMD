import { apiClient } from './apiClient'
import { storage, STORAGE_KEYS } from '../utils/storage'

export interface FileAsset {
  file_id: number
  syllabus_version_id: number
  original_filename: string
  display_name?: string | null
  bucket: string
  object_path: string
  mime_type: string
  size_bytes: number
  uploaded_by: number
  created_at: string
}

export interface SignedUrlResponse {
  file_id: number
  signed_url: string
  expires_in: number
  object_path: string
}

class FileService {
  /**
   * Check file storage health/status.
   */
  async checkHealth(): Promise<{
    enabled: boolean
    configured: boolean
    provider: string | null
    bucket: string | null
  }> {
    const response = await apiClient.get<{
      enabled: boolean
      configured: boolean
      provider: string | null
      bucket: string | null
    }>('/files/health')
    if (!response.success || !response.data) {
      // If health check fails, assume disabled
      return {
        enabled: false,
        configured: false,
        provider: null,
        bucket: null
      }
    }
    return response.data
  }

  /**
   * Upload a file (PDF/DOCX) for a syllabus version.
   * Only LECTURER role can upload.
   */
  async uploadFile(versionId: number, file: File): Promise<FileAsset> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('syllabus_version_id', versionId.toString())

    const token = storage.get<string>(STORAGE_KEYS.AUTH_TOKEN)
    if (!token) {
      throw new Error('Authentication required')
    }

    const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:9999'
    const url = `${API_BASE_URL}/files/upload`

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        // Don't set Content-Type - browser will set it with boundary for FormData
      },
      body: formData,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'Upload failed' }))
      throw new Error(errorData.message || `Upload failed: ${response.status}`)
    }

    const data = await response.json()
    if (!data.success || !data.data) {
      throw new Error(data.message || 'Upload failed')
    }

    return data.data
  }

  /**
   * Get all files for a syllabus version.
   */
  async getFilesByVersion(versionId: number): Promise<FileAsset[]> {
    const response = await apiClient.get<FileAsset[]>(`/files/version/${versionId}`)
    return response.data || []
  }

  /**
   * Get signed URL for downloading a file.
   */
  async getSignedUrl(fileId: number, expiresIn: number = 3600): Promise<string> {
    const response = await apiClient.get<SignedUrlResponse>(
      `/files/${fileId}/signed-url?expires_in=${expiresIn}`
    )
    if (!response.success || !response.data) {
      throw new Error(response.message || 'Failed to get signed URL')
    }
    return response.data.signed_url
  }

  /**
   * Download file by opening signed URL in new tab.
   */
  async downloadFile(fileId: number): Promise<void> {
    const signedUrl = await this.getSignedUrl(fileId)
    window.open(signedUrl, '_blank')
  }

  /**
   * Rename display_name of a file.
   */
  async renameFile(fileId: number, displayName: string): Promise<FileAsset> {
    const response = await apiClient.patch<FileAsset>(`/files/${fileId}`, {
      display_name: displayName,
    })
    if (!response.success || !response.data) {
      throw new Error(response.message || 'Failed to rename file')
    }
    return response.data
  }

  /**
   * Replace file content.
   */
  async replaceFile(fileId: number, file: File): Promise<FileAsset> {
    const formData = new FormData()
    formData.append('file', file)

    const token = storage.get<string>(STORAGE_KEYS.AUTH_TOKEN)
    if (!token) {
      throw new Error('Authentication required')
    }

    const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:9999'
    const url = `${API_BASE_URL}/files/${fileId}/replace`

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'Replace failed' }))
      throw new Error(errorData.message || `Replace failed: ${response.status}`)
    }

    const data = await response.json()
    if (!data.success || !data.data) {
      throw new Error(data.message || 'Replace failed')
    }

    return data.data
  }

  /**
   * Delete a file.
   */
  async deleteFile(fileId: number): Promise<void> {
    const response = await apiClient.delete(`/files/${fileId}`)
    if (!response.success) {
      throw new Error(response.message || 'Failed to delete file')
    }
  }
}

export const fileService = new FileService()
