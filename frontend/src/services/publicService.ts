import { apiClient } from './apiClient'
import { Syllabus } from '../types'

interface Subscription {
  sub_id: number
  syllabus_id: number
  user_id: number
}

interface Feedback {
  feedback_id: number
  syllabus_id: number
  content: string
  rating?: number
}

class PublicService {
  async searchSyllabi(query?: string): Promise<Syllabus[]> {
    const url = query ? `/public/syllabi?query=${encodeURIComponent(query)}` : '/public/syllabi'
    const response = await apiClient.get<Syllabus[]>(url)
    return response.data || []
  }

  async getPublicSyllabus(syllabusId: number): Promise<(Syllabus & { ai_summary?: any }) | null> {
    const response = await apiClient.get<Syllabus & { ai_summary?: any }>(`/public/syllabi/${syllabusId}`)
    return response.data || null
  }

  async subscribe(syllabusId: number): Promise<Subscription> {
    const response = await apiClient.post<Subscription>(`/public/syllabi/${syllabusId}/subscribe`)
    if (!response.success || !response.data) {
      throw new Error(response.message || 'Failed to subscribe')
    }
    return response.data
  }

  async submitFeedback(syllabusId: number, content: string, rating?: number): Promise<Feedback> {
    const response = await apiClient.post<Feedback>(`/public/syllabi/${syllabusId}/feedback`, {
      content,
      rating,
    })
    if (!response.success || !response.data) {
      throw new Error(response.message || 'Failed to submit feedback')
    }
    return response.data
  }
}

export const publicService = new PublicService()
