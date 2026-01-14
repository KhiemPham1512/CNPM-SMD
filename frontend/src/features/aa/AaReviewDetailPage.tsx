import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { syllabusService } from '../../services/syllabusService'
import { Syllabus } from '../../types'
import { formatDateTime } from '../../utils/date'
import { StatusBadge } from '../../components/workflow/StatusBadge'
import { WorkflowProgressBar } from '../../components/workflow/WorkflowProgressBar'
import { VersionAttachments } from '../../components/syllabi/VersionAttachments'
import { Tabs } from '../../components/ui/Tabs'
import { Button } from '../../components/ui/Button'
import { Modal } from '../../components/ui/Modal'
import { Input } from '../../components/ui/Input'
import { useAuth } from '../../app/store/authContext'

interface VersionDetail {
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
}

export function AaReviewDetailPage() {
  const { syllabusId } = useParams<{ syllabusId: string }>()
  const navigate = useNavigate()
  const { state } = useAuth()
  const [syllabus, setSyllabus] = useState<Syllabus | null>(null)
  const [version, setVersion] = useState<VersionDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [workflowInfo, setWorkflowInfo] = useState<{
    version_id: number
    current_status: string
    steps: Array<{ code: string; label: string; order: number }>
    current_step_index: number
  } | null>(null)
  
  // Approve/Reject modals
  const [isApproveModalOpen, setIsApproveModalOpen] = useState(false)
  const [isRejectModalOpen, setIsRejectModalOpen] = useState(false)
  const [rejectReason, setRejectReason] = useState('')
  const [processing, setProcessing] = useState(false)

  useEffect(() => {
    if (syllabusId) {
      const id = parseInt(syllabusId, 10)
      if (!isNaN(id)) {
        loadData(id)
      }
    }
  }, [syllabusId])

  const loadData = async (id: number) => {
    try {
      setLoading(true)
      setError(null)
      
      // Load syllabus
      const syllabusData = await syllabusService.getById(id)
      if (!syllabusData) {
        setError('Syllabus not found')
        return
      }
      setSyllabus(syllabusData)

      // Load version detail if available
      if (syllabusData.current_version_id) {
        const versionData = await syllabusService.getSyllabusVersion(syllabusData.current_version_id)
        setVersion(versionData)

        // Load workflow info
        if (versionData) {
          try {
            const workflow = await syllabusService.getVersionWorkflow(id, versionData.version_id)
            setWorkflowInfo(workflow)
          } catch (err) {
            console.warn('Failed to load workflow info:', err)
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async () => {
    if (!syllabusId) return
    
    try {
      setProcessing(true)
      const id = parseInt(syllabusId, 10)
      if (isNaN(id)) {
        setError('Invalid syllabus ID')
        return
      }
      await syllabusService.aaApprove(id)
      setIsApproveModalOpen(false)
      // Reload data to show updated status
      await loadData(id)
      // Show success message
      alert('Syllabus approved successfully')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve syllabus')
    } finally {
      setProcessing(false)
    }
  }

  const handleReject = async () => {
    if (!syllabusId) return
    
    const trimmedReason = rejectReason.trim()
    if (!trimmedReason) {
      alert('Please provide a rejection reason')
      return
    }
    
    try {
      setProcessing(true)
      const id = parseInt(syllabusId, 10)
      if (isNaN(id)) {
        setError('Invalid syllabus ID')
        return
      }
      await syllabusService.aaReject(id, trimmedReason)
      setIsRejectModalOpen(false)
      setRejectReason('')
      // Reload data to show updated status
      await loadData(id)
      // Show success message
      alert('Syllabus rejected successfully')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reject syllabus')
    } finally {
      setProcessing(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mb-4"></div>
          <p className="text-gray-500">Loading review details...</p>
        </div>
      </div>
    )
  }

  if (error || !syllabus) {
    return (
      <div className="space-y-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error || 'Syllabus not found'}
        </div>
        <Button variant="outline" onClick={() => navigate('/app/aa/reviews')}>
          Back to Queue
        </Button>
      </div>
    )
  }

  const canReview = syllabus.lifecycle_status === 'PENDING_APPROVAL' && state.roles.includes('AA')

  const tabs = [
    {
      id: 'overview',
      label: 'Overview',
      content: (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-700">Syllabus ID</label>
              <p className="mt-1 text-gray-900">{syllabus.syllabus_id}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Status</label>
              <p className="mt-1">
                <StatusBadge status={syllabus.lifecycle_status} />
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Subject ID</label>
              <p className="mt-1 text-gray-900">{syllabus.subject_id}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Program ID</label>
              <p className="mt-1 text-gray-900">{syllabus.program_id}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Lecturer (Owner)</label>
              <p className="mt-1 text-gray-900">ID: {syllabus.owner_lecturer_id}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Created</label>
              <p className="mt-1 text-gray-900">{formatDateTime(syllabus.created_at)}</p>
            </div>
          </div>

          {version && version.creator && (
            <div className="border-t pt-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Version Information</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-700">Version No</label>
                  <p className="mt-1 text-gray-900">{version.version_no}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">Academic Year</label>
                  <p className="mt-1 text-gray-900">{version.academic_year}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">Created By</label>
                  <p className="mt-1 text-gray-900">
                    {version.creator.full_name} ({version.creator.email})
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">Submitted At</label>
                  <p className="mt-1 text-gray-900">
                    {version.submitted_at ? formatDateTime(version.submitted_at) : 'N/A'}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      ),
    },
    {
      id: 'clo-plo',
      label: 'CLO/PLO Mapping',
      content: (
        <div className="space-y-4">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-yellow-800">
            <p className="font-medium mb-2">CLO/PLO Mapping Feature</p>
            <p className="text-sm">
              CLO/PLO mapping interface is under development. This section will display the mapping between Course Learning Outcomes (CLO) and Program Learning Outcomes (PLO).
            </p>
          </div>
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">Expected Data Structure:</h4>
            <pre className="text-xs text-gray-600 overflow-x-auto">
{`{
  "clo_plo_mappings": [
    {
      "clo_id": 1,
      "clo_code": "CLO1",
      "clo_description": "Describe...",
      "mapped_plos": [
        {
          "plo_id": 1,
          "plo_code": "PLO1",
          "plo_description": "Demonstrate...",
          "mapping_level": "high" // high, medium, low
        }
      ]
    }
  ]
}`}
            </pre>
          </div>
        </div>
      ),
    },
    {
      id: 'attachments',
      label: 'Attachments',
      content: syllabus.current_version_id ? (
        <VersionAttachments 
          versionId={syllabus.current_version_id}
          syllabusStatus={syllabus.lifecycle_status}
          syllabusOwnerId={syllabus.owner_lecturer_id}
        />
      ) : (
        <div className="text-center py-8 text-gray-500">
          <p>No version available.</p>
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">AA Review</h1>
          <p className="text-gray-600">Syllabus ID: {syllabus.syllabus_id}</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" onClick={() => navigate('/app/aa/reviews')}>
            Back to Queue
          </Button>
          {canReview && (
            <>
              <Button onClick={() => setIsApproveModalOpen(true)}>
                Approve
              </Button>
              <Button variant="danger" onClick={() => setIsRejectModalOpen(true)}>
                Reject
              </Button>
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Workflow Progress Bar */}
      {workflowInfo && (
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Workflow Progress</h2>
          <WorkflowProgressBar
            steps={workflowInfo.steps}
            currentStatus={workflowInfo.current_status}
          />
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        <Tabs tabs={tabs} />
      </div>

      {/* Approve Modal */}
      <Modal
        isOpen={isApproveModalOpen}
        onClose={() => setIsApproveModalOpen(false)}
        title="Approve Syllabus"
        footer={
          <>
            <Button
              variant="outline"
              onClick={() => setIsApproveModalOpen(false)}
              disabled={processing}
            >
              Cancel
            </Button>
            <Button onClick={handleApprove} disabled={processing}>
              {processing ? 'Approving...' : 'Confirm Approve'}
            </Button>
          </>
        }
      >
        <p className="text-gray-700">
          Are you sure you want to approve this syllabus? It will be moved to APPROVED status.
        </p>
      </Modal>

      {/* Reject Modal */}
      <Modal
        isOpen={isRejectModalOpen}
        onClose={() => {
          setIsRejectModalOpen(false)
          setRejectReason('')
        }}
        title="Reject Syllabus"
        footer={
          <>
            <Button
              variant="outline"
              onClick={() => {
                setIsRejectModalOpen(false)
                setRejectReason('')
              }}
              disabled={processing}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={handleReject}
              disabled={processing || !rejectReason.trim()}
            >
              {processing ? 'Rejecting...' : 'Confirm Reject'}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <p className="text-gray-700">
            Please provide a reason for rejecting this syllabus. The syllabus will be returned to DRAFT status for the lecturer to revise.
          </p>
          <Input
            label="Rejection Reason *"
            placeholder="Enter reason for rejection..."
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            multiline
            rows={4}
            required
          />
        </div>
      </Modal>
    </div>
  )
}
