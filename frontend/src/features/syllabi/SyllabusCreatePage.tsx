import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { syllabusService } from '../../services/syllabusService'
import { subjectService, Subject } from '../../services/subjectService'
import { programService, Program } from '../../services/programService'
import { fileService } from '../../services/fileService'
import { Select } from '../../components/ui/Select'
import { Button } from '../../components/ui/Button'
import { useAuth } from '../../app/store/authContext'

const createSchema = z.object({
  subject_id: z.coerce.number().int().positive('Please select a subject'),
  program_id: z.coerce.number().int().positive('Please select a program'),
})

type CreateFormData = z.infer<typeof createSchema>

export function SyllabusCreatePage() {
  const navigate = useNavigate()
  const { state } = useAuth()
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  
  // Data for dropdowns
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [programs, setPrograms] = useState<Program[]>([])
  const [loadingData, setLoadingData] = useState(true)
  
  // File upload
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<CreateFormData>({
    resolver: zodResolver(createSchema),
  })

  const subjectId = watch('subject_id')
  const programId = watch('program_id')

  // Load subjects and programs on mount
  useEffect(() => {
    const loadData = async () => {
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
    loadData()
  }, [])

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) {
      setSelectedFile(null)
      return
    }

    // Validate file type
    const allowedExtensions = ['.pdf', '.docx', '.doc']
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
    
    if (!allowedExtensions.includes(fileExtension)) {
      setUploadError('Only PDF and DOCX files are allowed')
      event.target.value = ''
      setSelectedFile(null)
      return
    }

    // Validate file size (20MB)
    const maxSize = 20 * 1024 * 1024
    if (file.size > maxSize) {
      setUploadError(`File size exceeds 20MB limit. Current size: ${(file.size / 1024 / 1024).toFixed(2)}MB`)
      event.target.value = ''
      setSelectedFile(null)
      return
    }

    setSelectedFile(file)
    setUploadError(null)
  }

  const removeFile = () => {
    setSelectedFile(null)
    setUploadError(null)
    // Reset file input
    const fileInput = document.getElementById('file-upload-input') as HTMLInputElement
    if (fileInput) {
      fileInput.value = ''
    }
  }

  const onSubmit = async (data: CreateFormData) => {
    setError(null)
    setUploadError(null)
    setLoading(true)
    
    try {
      // Step 1: Create syllabus draft
      // Ensure numbers are properly typed (z.coerce.number() handles conversion, but TypeScript needs explicit typing)
      const result = await syllabusService.create({
        subject_id: Number(data.subject_id),
        program_id: Number(data.program_id),
      })
      
      // Step 2: Upload file if selected
      if (selectedFile && result.draft_version_id) {
        setLoading(false)
        setUploading(true)
        try {
          await fileService.uploadFile(result.draft_version_id, selectedFile)
        } catch (uploadErr) {
          // Log upload error but don't block redirect
          setUploadError(uploadErr instanceof Error ? uploadErr.message : 'File upload failed')
          // Continue to redirect even if upload fails
        } finally {
          setUploading(false)
        }
      }
      
      // Step 3: Redirect to detail page
      navigate(`/app/syllabi/${result.syllabus_id}?version=${result.draft_version_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create syllabus')
      setLoading(false)
    }
  }

  const isFormValid = subjectId && programId
  const isSubmitting = loading || uploading

  if (loadingData) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mb-4"></div>
          <p className="text-gray-500">Loading subjects and programs...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Create Syllabus</h1>
        <p className="text-gray-600">Create a new syllabus draft</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Subject Dropdown */}
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

          {/* Program Dropdown */}
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
              Lecturer is automatically set to the current logged-in user
            </p>
          </div>

          {/* File Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Attach File (Optional)
            </label>
            <div className="space-y-2">
              <input
                type="file"
                accept=".pdf,.docx,.doc"
                onChange={handleFileSelect}
                disabled={isSubmitting}
                className="hidden"
                id="file-upload-input"
              />
              <label
                htmlFor="file-upload-input"
                className={`
                  cursor-pointer inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors border
                  ${isSubmitting
                    ? 'bg-gray-100 text-gray-400 border-gray-300 cursor-not-allowed'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }
                `}
              >
                {selectedFile ? 'Change File' : 'Choose DOCX/PDF File'}
              </label>
              
              {selectedFile && (
                <div className="flex items-center justify-between px-4 py-2 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-blue-900">{selectedFile.name}</p>
                    <p className="text-xs text-blue-700">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={removeFile}
                    disabled={isSubmitting}
                    className="ml-4 text-red-600 hover:text-red-800 text-sm font-medium"
                  >
                    Remove
                  </button>
                </div>
              )}
              
              {uploadError && (
                <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded-lg text-sm">
                  ⚠ {uploadError}
                </div>
              )}
              
              <p className="text-xs text-gray-500">
                Supported formats: PDF, DOCX (Max 20MB)
              </p>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <div className="flex gap-3">
            <Button 
              type="submit" 
              disabled={!isFormValid || isSubmitting}
            >
              {loading && 'Creating syllabus draft...'}
              {uploading && 'Uploading attachment...'}
              {!loading && !uploading && 'Create Syllabus'}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/app/syllabi')}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
