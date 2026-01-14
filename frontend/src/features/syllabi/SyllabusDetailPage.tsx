import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { syllabusService } from '../../services/syllabusService'
import { subjectService, Subject } from '../../services/subjectService'
import { programService, Program } from '../../services/programService'
import { Syllabus } from '../../types'
import { formatDateTime } from '../../utils/date'
import { StatusBadge } from '../../components/workflow/StatusBadge'
import { WorkflowTimeline } from '../../components/workflow/WorkflowTimeline'
import { WorkflowProgressBar } from '../../components/workflow/WorkflowProgressBar'
import { VersionAttachments } from '../../components/syllabi/VersionAttachments'
import { Tabs } from '../../components/ui/Tabs'
import { Button } from '../../components/ui/Button'
import { Modal } from '../../components/ui/Modal'
import { Select } from '../../components/ui/Select'
import { Tooltip } from '../../components/ui/Tooltip'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAuth } from '../../app/store/authContext'
import { WORKFLOW_STATUS } from '../../constants/workflow'

const editSchema = z.object({
  subject_id: z.coerce.number().int().positive('Please select a subject'),
  program_id: z.coerce.number().int().positive('Please select a program'),
})

type EditFormData = z.infer<typeof editSchema>

export function SyllabusDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { state } = useAuth()
  const [syllabus, setSyllabus] = useState<Syllabus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [updating, setUpdating] = useState(false)
  const [workflowInfo, setWorkflowInfo] = useState<{
    version_id: number
    current_status: string
    steps: Array<{ code: string; label: string; order: number }>
    current_step_index: number
  } | null>(null)
  
  // Data for dropdowns in edit modal
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [programs, setPrograms] = useState<Program[]>([])
  const [loadingDropdowns, setLoadingDropdowns] = useState(false)

  useEffect(() => {
    if (id) {
      const syllabusId = parseInt(id, 10)
      if (!isNaN(syllabusId)) {
        loadSyllabus(syllabusId)
      }
    }
  }, [id])

  useEffect(() => {
    if (isEditModalOpen) {
      loadDropdownData()
    }
  }, [isEditModalOpen])

  const loadDropdownData = async () => {
    try {
      setLoadingDropdowns(true)
      const [subjectsData, programsData] = await Promise.all([
        subjectService.list(),
        programService.list(),
      ])
      setSubjects(subjectsData)
      setPrograms(programsData)
    } catch (err) {
      console.error('Failed to load dropdown data:', err)
    } finally {
      setLoadingDropdowns(false)
    }
  }

  const loadSyllabus = async (syllabusId: number) => {
    try {
      const data = await syllabusService.getById(syllabusId)
      setSyllabus(data)
      setError(null)
      
      // Load workflow info if user is not STUDENT and syllabus has version
      if (data && data.current_version_id && !state.roles.includes('STUDENT')) {
        try {
          const workflow = await syllabusService.getVersionWorkflow(
            syllabusId,
            data.current_version_id
          )
          setWorkflowInfo(workflow)
        } catch (err) {
          // 403 means student - ignore, otherwise just don't show workflow
          if (err instanceof Error && err.message.includes('403')) {
            setWorkflowInfo(null)
          } else {
            // Log error but don't show workflow on failure
            console.warn('Failed to load workflow info:', err)
            setWorkflowInfo(null)
          }
        }
      } else {
        setWorkflowInfo(null)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load syllabus')
    } finally {
      setLoading(false)
    }
  }

  const {
    register: registerEdit,
    handleSubmit: handleEditSubmit,
    formState: { errors: editErrors },
    reset: resetEditForm,
  } = useForm<EditFormData>({
    resolver: zodResolver(editSchema),
    defaultValues: syllabus ? {
      subject_id: syllabus.subject_id,
      program_id: syllabus.program_id,
      // owner_lecturer_id is not in EditFormData schema - it cannot be changed
    } : undefined,
  })

  useEffect(() => {
    if (syllabus && isEditModalOpen) {
      resetEditForm({
        subject_id: syllabus.subject_id,
        program_id: syllabus.program_id,
      })
    }
  }, [syllabus, isEditModalOpen, resetEditForm])

  const handleEdit = async (data: EditFormData) => {
    if (!id) return
    setUpdating(true)
    setError(null)
    try {
      const editId = parseInt(id, 10)
      if (isNaN(editId)) {
        setError('Invalid syllabus ID')
        setUpdating(false)
        return
      }
      // Don't send owner_lecturer_id - it cannot be changed
      await syllabusService.update(editId, {
        subject_id: Number(data.subject_id),
        program_id: Number(data.program_id),
      })
      setIsEditModalOpen(false)
      await loadSyllabus(editId)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update syllabus')
    } finally {
      setUpdating(false)
    }
  }

  // Create submit handler for form
  const onEditFormSubmit = handleEditSubmit(handleEdit)

  const handleWorkflowAction = async (action: string) => {
    if (!syllabus || !id) return

    try {
      setError(null)
      switch (action) {
        case 'submit':
          if (!id) return
          const submitId = parseInt(id, 10)
          if (isNaN(submitId)) {
            setError('Invalid syllabus ID')
            return
          }
          await syllabusService.submitForReview(submitId)
          // After submit, syllabus becomes read-only
          await loadSyllabus(submitId)
          break
        case 'approve1':
          if (!id) return
          const approve1Id = parseInt(id, 10)
          if (isNaN(approve1Id)) {
            setError('Invalid syllabus ID')
            return
          }
          await syllabusService.hodApprove(approve1Id)
          await loadSyllabus(approve1Id)
          break
        case 'reject1':
          // Reject requires reason - should use dedicated review page
          // For now, use placeholder reason (this should be replaced with modal)
          if (!id) return
          const reject1Id = parseInt(id, 10)
          if (isNaN(reject1Id)) {
            setError('Invalid syllabus ID')
            return
          }
          await syllabusService.hodReject(reject1Id, 'Rejected from detail page')
          await loadSyllabus(reject1Id)
          break
        case 'approve2':
          if (!id) return
          const approve2Id = parseInt(id, 10)
          if (isNaN(approve2Id)) {
            setError('Invalid syllabus ID')
            return
          }
          await syllabusService.aaApprove(approve2Id)
          await loadSyllabus(approve2Id)
          break
        case 'reject2':
          // Reject requires reason - should use dedicated review page
          // For now, use placeholder reason (this should be replaced with modal)
          if (!id) return
          const reject2Id = parseInt(id, 10)
          if (isNaN(reject2Id)) {
            setError('Invalid syllabus ID')
            return
          }
          await syllabusService.aaReject(reject2Id, 'Rejected from detail page')
          await loadSyllabus(reject2Id)
          break
        case 'publish':
          if (!id) return
          const publishId = parseInt(id, 10)
          if (isNaN(publishId)) {
            setError('Invalid syllabus ID')
            return
          }
          await syllabusService.publish(publishId)
          await loadSyllabus(publishId)
          break
        case 'unpublish':
          if (!id) return
          const unpublishId = parseInt(id, 10)
          if (isNaN(unpublishId)) {
            setError('Invalid syllabus ID')
            return
          }
          await syllabusService.unpublish(unpublishId)
          await loadSyllabus(unpublishId)
          break
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Action failed')
    }
  }

  const isOwner = syllabus?.owner_lecturer_id === state.user?.user_id
  const canEdit = syllabus?.lifecycle_status === WORKFLOW_STATUS.DRAFT && 
    state.roles.includes('LECTURER') && 
    isOwner
  const canSubmit = syllabus?.lifecycle_status === WORKFLOW_STATUS.DRAFT && 
    state.roles.includes('LECTURER') && 
    isOwner
  const canApprove1 = syllabus?.lifecycle_status === 'PENDING_REVIEW' && state.roles.includes('HOD')
  const canApprove2 = syllabus?.lifecycle_status === 'PENDING_APPROVAL' && state.roles.includes('AA')
  const canPublish = syllabus?.lifecycle_status === 'APPROVED' && 
    (state.roles.includes('PRINCIPAL') || state.roles.includes('ADMIN'))
  const canUnpublish = syllabus?.lifecycle_status === 'PUBLISHED' && 
    (state.roles.includes('PRINCIPAL') || state.roles.includes('ADMIN'))

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mb-4"></div>
          <p className="text-gray-500">Loading syllabus...</p>
        </div>
      </div>
    )
  }

  if (error || !syllabus) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        {error || 'Syllabus not found'}
      </div>
    )
  }

  const tabs = [
    {
      id: 'overview',
      label: 'Overview',
      content: (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-1">Syllabus ID</h3>
              <p className="text-gray-900">{syllabus.syllabus_id}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-1">Subject ID</h3>
              <p className="text-gray-900">{syllabus.subject_id}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-1">Program ID</h3>
              <p className="text-gray-900">{syllabus.program_id}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-1">Lecturer ID</h3>
              <p className="text-gray-900">{syllabus.owner_lecturer_id}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-1">Created</h3>
              <p className="text-gray-900">{formatDateTime(syllabus.created_at)}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-1">Current Version ID</h3>
              <p className="text-gray-900">{syllabus.current_version_id || 'N/A'}</p>
            </div>
          </div>
        </div>
      ),
    },
    {
      id: 'workflow',
      label: 'Workflow',
      content: (
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Current Status</h3>
            <StatusBadge status={syllabus.lifecycle_status} />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Workflow Timeline</h3>
            <WorkflowTimeline currentStatus={syllabus.lifecycle_status} />
          </div>
          <div>
            <Tooltip content="Version comparison feature - coming soon">
              <Button
                variant="secondary"
                disabled
              >
                Compare Versions
              </Button>
            </Tooltip>
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
          <p>No version available. Please create a version first.</p>
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Syllabus #{syllabus.syllabus_id}
          </h1>
          <p className="text-gray-600">Subject ID: {syllabus.subject_id}</p>
        </div>
        <StatusBadge status={syllabus.lifecycle_status} />
      </div>

      {/* Workflow Progress Bar - Only show for non-STUDENT roles */}
      {workflowInfo && !state.roles.includes('STUDENT') && (
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Workflow Progress</h2>
          <WorkflowProgressBar
            steps={workflowInfo.steps}
            currentStatus={workflowInfo.current_status}
          />
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
            {error}
          </div>
        )}

        <div className="mb-6 flex flex-wrap gap-3">
          {canEdit && (
            <Button onClick={() => setIsEditModalOpen(true)}>
              Edit Draft
            </Button>
          )}
          {canSubmit && (
            <Button onClick={() => handleWorkflowAction('submit')}>
              Submit for Review
            </Button>
          )}
          {canApprove1 && (
            <>
              <Button onClick={() => handleWorkflowAction('approve1')}>
                Approve (HoD)
              </Button>
              <Tooltip content="Reject action does not support comments yet">
                <Button variant="danger" onClick={() => handleWorkflowAction('reject1')}>
                  Reject (HoD)
                </Button>
              </Tooltip>
            </>
          )}
          {canApprove2 && (
            <>
              <Button onClick={() => handleWorkflowAction('approve2')}>
                Approve (AA)
              </Button>
              <Tooltip content="Reject action does not support comments yet">
                <Button variant="danger" onClick={() => handleWorkflowAction('reject2')}>
                  Reject (AA)
                </Button>
              </Tooltip>
            </>
          )}
          {canPublish && (
            <Button onClick={() => handleWorkflowAction('publish')}>
              Publish
            </Button>
          )}
          {canUnpublish && (
            <Button variant="danger" onClick={() => handleWorkflowAction('unpublish')}>
              Unpublish
            </Button>
          )}
        </div>

        <Tabs tabs={tabs} />
      </div>

      {/* Edit Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="Edit Syllabus"
        footer={
          <>
            <Button
              variant="outline"
              onClick={() => setIsEditModalOpen(false)}
              disabled={updating}
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={(e) => {
                e.preventDefault()
                // Trigger form submit handler directly
                onEditFormSubmit(e as any)
              }}
              disabled={updating}
            >
              {updating ? 'Updating...' : 'Save Changes'}
            </Button>
          </>
        }
      >
        <form id="edit-syllabus-form" onSubmit={onEditFormSubmit} className="space-y-6">
          {loadingDropdowns ? (
            <div className="text-center py-4 text-gray-500">
              <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600 mb-2"></div>
              <p>Loading subjects and programs...</p>
            </div>
          ) : (
            <>
              <Select
                label="Subject"
                options={[
                  { value: '', label: '-- Select Subject --' },
                  ...subjects.map(subject => ({
                    value: subject.id.toString(),
                    label: `${subject.code} - ${subject.name}`,
                  })),
                ]}
                error={editErrors.subject_id?.message}
                {...registerEdit('subject_id')}
              />

              <Select
                label="Program"
                options={[
                  { value: '', label: '-- Select Program --' },
                  ...programs.map(program => ({
                    value: program.id.toString(),
                    label: `${program.code} - ${program.name}`,
                  })),
                ]}
                error={editErrors.program_id?.message}
                {...registerEdit('program_id')}
              />

              {/* Lecturer (Owner) - Read-only display */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Lecturer (Owner)
                </label>
                <div className="px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg text-gray-700">
                  {state.user ? (
                    <div>
                      <p className="font-medium">{state.user.full_name}</p>
                      <p className="text-sm text-gray-500">ID: {state.user.user_id}</p>
                    </div>
                  ) : (
                    <p className="text-gray-500">Not available</p>
                  )}
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  Owner cannot be changed. It is set when the syllabus is created.
                </p>
              </div>
            </>
          )}
        </form>
      </Modal>
    </div>
  )
}
