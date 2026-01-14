/**
 * Workflow Status Constants for SMD System
 * 
 * Matches backend domain/constants.py
 * Workflow: DRAFT → PENDING_REVIEW → PENDING_APPROVAL → APPROVED → PUBLISHED
 */
export const WORKFLOW_STATUS = {
  DRAFT: 'DRAFT',
  PENDING_REVIEW: 'PENDING_REVIEW',
  PENDING_APPROVAL: 'PENDING_APPROVAL',
  APPROVED: 'APPROVED',
  PUBLISHED: 'PUBLISHED',
} as const

export type WorkflowStatus = typeof WORKFLOW_STATUS[keyof typeof WORKFLOW_STATUS]

export const WORKFLOW_STATUS_LABELS: Record<WorkflowStatus, string> = {
  [WORKFLOW_STATUS.DRAFT]: 'Draft',
  [WORKFLOW_STATUS.PENDING_REVIEW]: 'Pending Review',
  [WORKFLOW_STATUS.PENDING_APPROVAL]: 'Pending Approval',
  [WORKFLOW_STATUS.APPROVED]: 'Approved',
  [WORKFLOW_STATUS.PUBLISHED]: 'Published',
}

/**
 * Workflow order (for progress tracking)
 */
export const WORKFLOW_ORDER: WorkflowStatus[] = [
  WORKFLOW_STATUS.DRAFT,
  WORKFLOW_STATUS.PENDING_REVIEW,
  WORKFLOW_STATUS.PENDING_APPROVAL,
  WORKFLOW_STATUS.APPROVED,
  WORKFLOW_STATUS.PUBLISHED,
]

/**
 * Get workflow step index (0-based)
 */
export function getWorkflowStepIndex(status: WorkflowStatus): number {
  return WORKFLOW_ORDER.indexOf(status)
}

/**
 * Check if status is before another status in workflow
 */
export function isBeforeInWorkflow(status: WorkflowStatus, compareTo: WorkflowStatus): boolean {
  return getWorkflowStepIndex(status) < getWorkflowStepIndex(compareTo)
}

/**
 * Check if status is after another status in workflow
 */
export function isAfterInWorkflow(status: WorkflowStatus, compareTo: WorkflowStatus): boolean {
  return getWorkflowStepIndex(status) > getWorkflowStepIndex(compareTo)
}
