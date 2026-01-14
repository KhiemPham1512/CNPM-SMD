export type UserRole = 
  | 'ADMIN'
  | 'LECTURER'
  | 'HOD'
  | 'AA'
  | 'PRINCIPAL'
  | 'STUDENT'

export type WorkflowStatus = 
  | 'DRAFT'
  | 'PENDING_REVIEW'
  | 'PENDING_APPROVAL'
  | 'APPROVED'
  | 'PUBLISHED'

export interface User {
  user_id: number
  username: string
  full_name: string
  email: string
  status: string
  created_at: string
}

export interface AISummary {
  summary_id: number
  summary_text: string
  generated_at: string | null
}

export interface Syllabus {
  syllabus_id: number
  subject_id: number
  program_id: number
  owner_lecturer_id: number
  current_version_id: number | null
  lifecycle_status: WorkflowStatus
  created_at: string
  ai_summary?: AISummary | null
}

export interface Notification {
  id: number
  title: string
  content: string
  type: 'info' | 'warning' | 'success' | 'error'
  read: boolean
  createdAt: string
  userId?: number
}
