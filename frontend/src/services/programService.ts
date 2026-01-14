import { apiClient } from './apiClient'

export interface Program {
  id: number
  code: string
  name: string
}

class ProgramService {
  async list(): Promise<Program[]> {
    const response = await apiClient.get<Program[]>('/programs')
    return response.data || []
  }
}

export const programService = new ProgramService()
