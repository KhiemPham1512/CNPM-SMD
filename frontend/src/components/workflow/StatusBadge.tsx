import { WorkflowStatus } from '../../types'
import { Badge } from '../ui/Badge'

interface StatusBadgeProps {
  status: WorkflowStatus
}

const statusConfig: Record<WorkflowStatus, { label: string; variant: 'default' | 'success' | 'warning' | 'danger' | 'info' }> = {
  DRAFT: { label: 'Draft', variant: 'default' },
  PENDING_REVIEW: { label: 'Pending Review', variant: 'warning' },
  PENDING_APPROVAL: { label: 'Pending Approval', variant: 'warning' },
  APPROVED: { label: 'Approved', variant: 'success' },
  PUBLISHED: { label: 'Published', variant: 'info' },
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = statusConfig[status]
  return <Badge variant={config.variant}>{config.label}</Badge>
}
