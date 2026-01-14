import { apiClient } from './apiClient'

export interface Subject {
  id: number
  code: string
  name: string
}

class SubjectService {
  async list(): Promise<Subject[]> {
    const response = await apiClient.get<Subject[]>('/subjects')
    return response.data || []
  }
}

export const subjectService = new SubjectService()
