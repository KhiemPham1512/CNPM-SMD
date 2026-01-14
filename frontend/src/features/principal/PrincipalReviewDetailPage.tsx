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

export function PrincipalReviewDetailPage() {
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
  
  // Publish/Unpublish modals
  const [isPublishModalOpen, setIsPublishModalOpen] = useState(false)
  const [isUnpublishModalOpen, setIsUnpublishModalOpen] = useState(false)
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

  const handlePublish = async () => {
    if (!syllabusId) return
    
    try {
      setProcessing(true)
      const id = parseInt(syllabusId, 10)
      if (isNaN(id)) {
        setError('Invalid syllabus ID')
        return
      }
      await syllabusService.publish(id)
      setIsPublishModalOpen(false)
      // Reload data to show updated status
      await loadData(id)
      // Show success message
      alert('Syllabus published successfully')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to publish syllabus')
    } finally {
      setProcessing(false)
    }
  }

  const handleUnpublish = async () => {
    if (!syllabusId) return
    
    try {
      setProcessing(true)
      const id = parseInt(syllabusId, 10)
      if (isNaN(id)) {
        setError('Invalid syllabus ID')
        return
      }
      await syllabusService.unpublish(id)
      setIsUnpublishModalOpen(false)
      // Reload data to show updated status
      await loadData(id)
      // Show success message
      alert('Syllabus unpublished successfully')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to unpublish syllabus')
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
        <Button variant="outline" onClick={() => navigate('/app/principal/reviews')}>
          Back to Queue
        </Button>
      </div>
    )
  }

  const canPublish = syllabus.lifecycle_status === 'APPROVED' && 
    (state.roles.includes('PRINCIPAL') || state.roles.includes('ADMIN'))
  const canUnpublish = syllabus.lifecycle_status === 'PUBLISHED' && 
    (state.roles.includes('PRINCIPAL') || state.roles.includes('ADMIN'))

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
                  <label className="text-sm font-medium text-gray-700">Approved At</label>
                  <p className="mt-1 text-gray-900">
                    {version.approved_at ? formatDateTime(version.approved_at) : 'N/A'}
                  </p>
                </div>
                {version.published_at && (
                  <div>
                    <label className="text-sm font-medium text-gray-700">Published At</label>
                    <p className="mt-1 text-gray-900">{formatDateTime(version.published_at)}</p>
                  </div>
                )}
              </div>
            </div>
          )}
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
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Principal Review</h1>
          <p className="text-gray-600">Syllabus ID: {syllabus.syllabus_id}</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" onClick={() => navigate('/app/principal/reviews')}>
            Back to Queue
          </Button>
          {canPublish && (
            <Button onClick={() => setIsPublishModalOpen(true)}>
              Publish
            </Button>
          )}
          {canUnpublish && (
            <Button variant="secondary" onClick={() => setIsUnpublishModalOpen(true)}>
              Unpublish
            </Button>
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

      {/* Publish Modal */}
      <Modal
        isOpen={isPublishModalOpen}
        onClose={() => setIsPublishModalOpen(false)}
        title="Publish Syllabus"
        footer={
          <>
            <Button
              variant="outline"
              onClick={() => setIsPublishModalOpen(false)}
              disabled={processing}
            >
              Cancel
            </Button>
            <Button onClick={handlePublish} disabled={processing}>
              {processing ? 'Publishing...' : 'Confirm Publish'}
            </Button>
          </>
        }
      >
        <p className="text-gray-700">
          Are you sure you want to publish this syllabus? It will be moved to PUBLISHED status and will be visible to students and the public.
        </p>
      </Modal>

      {/* Unpublish Modal */}
      <Modal
        isOpen={isUnpublishModalOpen}
        onClose={() => setIsUnpublishModalOpen(false)}
        title="Unpublish Syllabus"
        footer={
          <>
            <Button
              variant="outline"
              onClick={() => setIsUnpublishModalOpen(false)}
              disabled={processing}
            >
              Cancel
            </Button>
            <Button
              variant="secondary"
              onClick={handleUnpublish}
              disabled={processing}
            >
              {processing ? 'Unpublishing...' : 'Confirm Unpublish'}
            </Button>
          </>
        }
      >
        <p className="text-gray-700">
          Are you sure you want to unpublish this syllabus? It will be moved back to APPROVED status and will no longer be visible to students and the public.
        </p>
      </Modal>
    </div>
  )
}
