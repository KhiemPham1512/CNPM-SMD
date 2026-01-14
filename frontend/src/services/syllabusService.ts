import { Syllabus } from '../types'
import { apiClient } from './apiClient'

class SyllabusService {
  async list(mine?: boolean): Promise<Syllabus[]> {
    const url = mine ? '/syllabi?mine=true' : '/syllabi'
    const response = await apiClient.get<Syllabus[]>(url)
    return response.data || []
  }

  async getById(id: number): Promise<Syllabus | null> {
    const response = await apiClient.get<Syllabus>(`/syllabi/${id}`)
    return response.data || null
  }

  async create(data: {
    subject_id: number
    program_id: number
  }): Promise<{
    syllabus_id: number
    draft_version_id: number
  }> {
    const response = await apiClient.post<{
      syllabus_id: number
      draft_version_id: number
    }>('/syllabi', data)
    if (!response.success || !response.data) {
      // Include error details if available
      const errorMessage = response.message || 'Failed to create syllabus'
      const errorDetails = response.errors ? ` Details: ${JSON.stringify(response.errors)}` : ''
      throw new Error(errorMessage + errorDetails)
    }
    return response.data
  }

  async update(id: number, data: Partial<{
    subject_id: number
    program_id: number
    owner_lecturer_id: number
  }>): Promise<Syllabus> {
    const response = await apiClient.put<Syllabus>(`/syllabi/${id}`, data)
    if (!response.success || !response.data) {
      throw new Error(response.message || 'Failed to update syllabus')
    }
    return response.data
  }

  async submitForReview(id: number): Promise<Syllabus> {
    const response = await apiClient.post<Syllabus>(`/syllabi/${id}/submit`)
    if (!response.success || !response.data) {
      throw new Error(response.message || 'Failed to submit for review')
    }
    return response.data
  }

  async hodApprove(id: number): Promise<Syllabus> {
    const response = await apiClient.post<Syllabus>(`/syllabi/${id}/hod/approve`)
    if (!response.success || !response.data) {
      throw new Error(response.message || 'Failed to approve')
    }
    return response.data
  }

  async aaApprove(id: number): Promise<Syllabus> {
    const response = await apiClient.post<Syllabus>(`/syllabi/${id}/aa/approve`)
    if (!response.success || !response.data) {
      throw new Error(response.message || 'Failed to approve')
    }
    return response.data
  }

  async getAaPendingReviews(): Promise<Syllabus[]> {
    const response = await apiClient.get<Syllabus[]>('/syllabi/reviews/aa/pending')
    return response.data || []
  }

  async getPrincipalPendingReviews(): Promise<Syllabus[]> {
    const response = await apiClient.get<Syllabus[]>('/syllabi/reviews/principal/pending')
    return response.data || []
  }

  async aaReject(id: number, reason: string): Promise<Syllabus> {
    const response = await apiClient.post<Syllabus>(`/syllabi/${id}/aa/reject`, { reason })
    if (!response.success || !response.data) {
      throw new Error(response.message || 'Failed to reject')
    }
    return response.data
  }

  async publish(id: number): Promise<Syllabus> {
    const response = await apiClient.post<Syllabus>(`/syllabi/${id}/publish`)
    if (!response.success || !response.data) {
      throw new Error(response.message || 'Failed to publish')
    }
    return response.data
  }

  async unpublish(id: number): Promise<Syllabus> {
    const response = await apiClient.post<Syllabus>(`/syllabi/${id}/unpublish`)
    if (!response.success || !response.data) {
      throw new Error(response.message || 'Failed to unpublish')
    }
    return response.data
  }

  async listPublished(search?: string): Promise<Syllabus[]> {
    const url = search ? `/syllabi/public?search=${encodeURIComponent(search)}` : '/syllabi/public'
    const response = await apiClient.get<Syllabus[]>(url)
    return response.data || []
  }

  async getPublishedById(id: number): Promise<Syllabus | null> {
    const response = await apiClient.get<Syllabus>(`/syllabi/public/${id}`)
    return response.data || null
  }

  async getVersionWorkflow(syllabusId: number, versionId: number): Promise<{
    version_id: number
    current_status: string
    steps: Array<{ code: string; label: string; order: number }>
    current_step_index: number
  } | null> {
    const response = await apiClient.get<{
      version_id: number
      current_status: string
      steps: Array<{ code: string; label: string; order: number }>
      current_step_index: number
    }>(`/syllabi/${syllabusId}/versions/${versionId}/workflow`)
    return response.data || null
  }

  async getHodPendingReviews(): Promise<Syllabus[]> {
    const response = await apiClient.get<Syllabus[]>('/syllabi/reviews/hod/pending')
    return response.data || []
  }

  async getSyllabusVersion(versionId: number): Promise<{
    version_id: number
    syllabus_id: number
    academic_year: string
    version_no: number
    workflow_status: string
    submitted_at: string | null
    approved_at: string | null
    published_at: string | null
    created_at: string
    created_by: number
    creator: {
      user_id: number
      full_name: string
      email: string
    } | null
    syllabus: {
      syllabus_id: number
      subject_id: number
      program_id: number
      owner_lecturer_id: number
      lifecycle_status: string
      created_at: string | null
    } | null
  } | null> {
    const response = await apiClient.get<{
      version_id: number
      syllabus_id: number
      academic_year: string
      version_no: number
      workflow_status: string
      submitted_at: string | null
      approved_at: string | null
      published_at: string | null
      created_at: string
      created_by: number
      creator: {
        user_id: number
        full_name: string
        email: string
      } | null
      syllabus: {
        syllabus_id: number
        subject_id: number
        program_id: number
        owner_lecturer_id: number
        lifecycle_status: string
        created_at: string | null
      } | null
    }>(`/syllabi/syllabus-versions/${versionId}`)
    return response.data || null
  }

  async hodReject(syllabusId: number, reason: string): Promise<Syllabus> {
    const response = await apiClient.post<Syllabus>(`/syllabi/${syllabusId}/hod/reject`, { reason })
    if (!response.success || !response.data) {
      throw new Error(response.message || 'Failed to reject')
    }
    return response.data
  }
}

export const syllabusService = new SyllabusService()
