import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { syllabusService } from '../../services/syllabusService'
import { subjectService, Subject } from '../../services/subjectService'
import { programService, Program } from '../../services/programService'
import { Syllabus } from '../../types'
import { Select } from '../../components/ui/Select'
import { Button } from '../../components/ui/Button'
import { useAuth } from '../../app/store/authContext'
import { WORKFLOW_STATUS } from '../../constants/workflow'

const editSchema = z.object({
  subject_id: z.coerce.number().int().positive('Please select a subject'),
  program_id: z.coerce.number().int().positive('Please select a program'),
})

type EditFormData = z.infer<typeof editSchema>

export function SyllabusEditPage() {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const { state } = useAuth()
  const [syllabus, setSyllabus] = useState<Syllabus | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [loadingData, setLoadingData] = useState(true)
  
  // Data for dropdowns
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [programs, setPrograms] = useState<Program[]>([])

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm<EditFormData>({
    resolver: zodResolver(editSchema),
  })

  const subjectId = watch('subject_id')
  const programId = watch('program_id')

  useEffect(() => {
    if (id) {
      loadSyllabus(parseInt(id))
    }
  }, [id])

  useEffect(() => {
    loadDropdownData()
  }, [])

  const loadDropdownData = async () => {
    try {
      setLoadingData(true)
      const [subjectsData, programsData] = await Promise.all([
        subjectService.list(),
        programService.list(),
      ])
      setSubjects(subjectsData)
      setPrograms(programsData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setLoadingData(false)
    }
  }

  const loadSyllabus = async (syllabusId: number) => {
    setLoading(true)
    setError(null)
    try {
      const data = await syllabusService.getById(syllabusId)
      if (!data) {
        setError('Syllabus not found')
        return
      }

      // Check ownership and status
      const isOwner = data.owner_lecturer_id === state.user?.user_id
      const canEdit = data.lifecycle_status === WORKFLOW_STATUS.DRAFT && 
        state.roles.includes('LECTURER') && 
        isOwner

      if (!canEdit) {
        setError('You can only edit syllabi in DRAFT status that you own')
        return
      }

      setSyllabus(data)
      reset({
        subject_id: data.subject_id,
        program_id: data.program_id,
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load syllabus')
    } finally {
      setLoading(false)
    }
  }

  const onSubmit = async (data: EditFormData) => {
    if (!id) return
    setError(null)
    setSaving(true)
    try {
      // Don't send owner_lecturer_id - it's fixed and cannot be changed
      await syllabusService.update(parseInt(id), {
        subject_id: data.subject_id,
        program_id: data.program_id,
      })
      navigate(`/app/syllabi/${id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update syllabus')
    } finally {
      setSaving(false)
    }
  }

  if (loading || loadingData) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mb-4"></div>
          <p className="text-gray-500">Loading...</p>
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
        <Button variant="outline" onClick={() => navigate('/app/syllabi')}>
          Back to List
        </Button>
      </div>
    )
  }

  const isFormValid = subjectId && programId

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Edit Syllabus</h1>
        <p className="text-gray-600">Syllabus ID: {syllabus.syllabus_id}</p>
        <p className="text-sm text-gray-500 mt-1">
          Status: {syllabus.lifecycle_status} | Owner: {syllabus.owner_lecturer_id} (cannot be changed)
        </p>
      </div>

      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <Select
            label="Subject"
            options={[
              { value: '', label: '-- Select Subject --' },
              ...subjects.map(subject => ({
                value: subject.id.toString(),
                label: `${subject.code} - ${subject.name}`,
              })),
            ]}
            error={errors.subject_id?.message}
            {...register('subject_id')}
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
            error={errors.program_id?.message}
            {...register('program_id')}
          />

          {/* Lecturer (Owner) - Read-only */}
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

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <div className="flex gap-3">
            <Button type="submit" disabled={!isFormValid || saving}>
              {saving ? 'Saving...' : 'Save Changes'}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate(`/app/syllabi/${id}`)}
            >
              Cancel
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
