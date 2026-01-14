import { useState, useEffect } from 'react'
import { fileService, FileAsset } from '../../services/fileService'
import { Button } from '../ui/Button'
import { useAuth } from '../../app/store/authContext'
import { formatDateTime } from '../../utils/date'
import { Input } from '../ui/Input'

interface VersionAttachmentsProps {
  versionId: number
  syllabusStatus: string
  syllabusOwnerId: number
}

export function VersionAttachments({ 
  versionId, 
  syllabusStatus, 
  syllabusOwnerId 
}: VersionAttachmentsProps) {
  const { state } = useAuth()
  const [files, setFiles] = useState<FileAsset[]>([])
  const [loading, setLoading] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [storageDisabled, setStorageDisabled] = useState(false)
  const [storageNotConfigured, setStorageNotConfigured] = useState(false)
  const [healthChecked, setHealthChecked] = useState(false)
  
  // Edit states
  const [editingFileId, setEditingFileId] = useState<number | null>(null)
  const [editingDisplayName, setEditingDisplayName] = useState('')
  const [replacingFileId, setReplacingFileId] = useState<number | null>(null)
  const [deletingFileId, setDeletingFileId] = useState<number | null>(null)

  // Check if user has LECTURER role
  const isLecturer = state.roles.some(role => role.toUpperCase() === 'LECTURER')
  
  // Check if user can edit attachments (LECTURER + owner + DRAFT)
  const canEditAttachments = 
    isLecturer && 
    state.user?.user_id === syllabusOwnerId && 
    syllabusStatus === 'DRAFT'

  // Check storage health on mount (once per component)
  useEffect(() => {
    checkStorageHealth()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // Only run once on mount

  // Load files when health check passes
  useEffect(() => {
    if (healthChecked && !storageDisabled && !storageNotConfigured) {
      loadFiles()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [versionId, healthChecked, storageDisabled, storageNotConfigured])

  const checkStorageHealth = async () => {
    try {
      const health = await fileService.checkHealth()
      setHealthChecked(true)
      
      if (!health.enabled) {
        setStorageDisabled(true)
        setError('File storage is disabled. Please contact administrator.')
      } else if (!health.configured) {
        setStorageNotConfigured(true)
        setError('Storage enabled but not configured. Please contact administrator.')
      } else {
        // Storage is enabled and configured - ready to load files
        setStorageDisabled(false)
        setStorageNotConfigured(false)
        setError(null)
      }
    } catch (err) {
      // If health check fails, assume disabled
      setHealthChecked(true)
      setStorageDisabled(true)
      setError('File storage is disabled. Please contact administrator.')
    }
  }

  const loadFiles = async () => {
    try {
      setLoading(true)
      setError(null)
      const fileList = await fileService.getFilesByVersion(versionId)
      setFiles(fileList)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load files'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Validate file type
    const allowedExtensions = ['.pdf', '.docx', '.doc']
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
    
    if (!allowedExtensions.includes(fileExtension)) {
      setUploadError('Only PDF and DOCX files are allowed')
      event.target.value = ''
      return
    }

    // Validate file size (20MB)
    const maxSize = 20 * 1024 * 1024
    if (file.size > maxSize) {
      setUploadError(`File size exceeds 20MB limit. Current size: ${(file.size / 1024 / 1024).toFixed(2)}MB`)
      event.target.value = ''
      return
    }

    // Upload file
    setIsUploading(true)
    setUploadError(null)
    try {
      await fileService.uploadFile(versionId, file)
      await loadFiles()
      event.target.value = ''
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setIsUploading(false)
    }
  }

  const handleDownload = async (fileId: number) => {
    try {
      await fileService.downloadFile(fileId)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download file')
    }
  }

  const handleRenameStart = (file: FileAsset) => {
    setEditingFileId(file.file_id)
    setEditingDisplayName(file.display_name || file.original_filename)
  }

  const handleRenameCancel = () => {
    setEditingFileId(null)
    setEditingDisplayName('')
  }

  const handleRenameSubmit = async (fileId: number) => {
    if (!editingDisplayName.trim()) {
      setError('Display name cannot be empty')
      return
    }

    try {
      await fileService.renameFile(fileId, editingDisplayName.trim())
      setEditingFileId(null)
      setEditingDisplayName('')
      await loadFiles()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to rename file')
    }
  }

  const handleReplaceFile = async (event: React.ChangeEvent<HTMLInputElement>, fileId: number) => {
    const file = event.target.files?.[0]
    if (!file) {
      setReplacingFileId(null)
      return
    }

    // Validate file type
    const allowedExtensions = ['.pdf', '.docx', '.doc']
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
    
    if (!allowedExtensions.includes(fileExtension)) {
      setError('Only PDF and DOCX files are allowed')
      event.target.value = ''
      setReplacingFileId(null)
      return
    }

    // Validate file size
    const maxSize = 20 * 1024 * 1024
    if (file.size > maxSize) {
      setError(`File size exceeds 20MB limit`)
      event.target.value = ''
      setReplacingFileId(null)
      return
    }

    try {
      await fileService.replaceFile(fileId, file)
      setReplacingFileId(null)
      await loadFiles()
      event.target.value = ''
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to replace file')
      setReplacingFileId(null)
    }
  }

  const handleDelete = async (fileId: number) => {
    if (!confirm('Are you sure you want to delete this file? This action cannot be undone.')) {
      return
    }

    setDeletingFileId(fileId)
    try {
      await fileService.deleteFile(fileId)
      setDeletingFileId(null)
      await loadFiles()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete file')
      setDeletingFileId(null)
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`
  }

  const getFileTypeLabel = (mimeType: string): string => {
    if (mimeType === 'application/pdf') return 'PDF'
    if (mimeType.includes('wordprocessingml')) return 'DOCX'
    if (mimeType === 'application/msword') return 'DOC'
    return mimeType.split('/')[1]?.toUpperCase() || 'FILE'
  }

  const getDisplayName = (file: FileAsset): string => {
    return file.display_name || file.original_filename
  }

  if (!healthChecked) {
    return (
      <div className="text-center py-8 text-gray-500">
        <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600 mb-2"></div>
        <p>Checking storage status...</p>
      </div>
    )
  }

  if (storageDisabled) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded-lg text-sm">
        File storage is disabled. Please contact administrator.
      </div>
    )
  }

  if (storageNotConfigured) {
    return (
      <div className="bg-orange-50 border border-orange-200 text-orange-700 px-4 py-3 rounded-lg text-sm">
        Storage enabled but not configured. Please contact administrator.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Attachments</h3>
        {canEditAttachments && (
          <div className="flex items-center gap-3">
            <input
              type="file"
              accept=".pdf,.docx,.doc"
              onChange={handleFileSelect}
              disabled={isUploading}
              className="hidden"
              id="file-upload-input"
            />
            <label
              htmlFor="file-upload-input"
              className={`
                cursor-pointer inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors
                ${isUploading
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-primary-600 text-white hover:bg-primary-700'
                }
              `}
            >
              {isUploading ? 'Uploading...' : 'Upload DOCX/PDF'}
            </label>
          </div>
        )}
      </div>

      {uploadError && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {uploadError}
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-8 text-gray-500">
          <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600 mb-2"></div>
          <p>Loading attachments...</p>
        </div>
      ) : files.length === 0 ? (
        <div className="text-center py-8 text-gray-500 border border-gray-200 rounded-lg bg-gray-50">
          <p>No attachments yet</p>
          {canEditAttachments && (
            <p className="text-sm mt-2">Click "Upload DOCX/PDF" to add files</p>
          )}
        </div>
      ) : (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Filename
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Size
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Uploaded
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {files.map((file) => (
                <tr key={file.file_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    {editingFileId === file.file_id ? (
                      <div className="flex items-center gap-2">
                        <Input
                          value={editingDisplayName}
                          onChange={(e) => setEditingDisplayName(e.target.value)}
                          className="flex-1"
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              handleRenameSubmit(file.file_id)
                            } else if (e.key === 'Escape') {
                              handleRenameCancel()
                            }
                          }}
                          autoFocus
                        />
                        <Button
                          size="sm"
                          onClick={() => handleRenameSubmit(file.file_id)}
                        >
                          Save
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={handleRenameCancel}
                        >
                          Cancel
                        </Button>
                      </div>
                    ) : (
                      <div className="text-sm font-medium text-gray-900">
                        {getDisplayName(file)}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 text-xs font-medium rounded bg-blue-100 text-blue-800">
                      {getFileTypeLabel(file.mime_type)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatFileSize(file.size_bytes)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDateTime(file.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDownload(file.file_id)}
                        className="text-primary-600 hover:text-primary-900"
                      >
                        Download
                      </Button>
                      
                      {canEditAttachments && editingFileId !== file.file_id && (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleRenameStart(file)}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            Rename
                          </Button>
                          
                          <>
                            <input
                              type="file"
                              accept=".pdf,.docx,.doc"
                              onChange={(e) => handleReplaceFile(e, file.file_id)}
                              className="hidden"
                              id={`replace-file-${file.file_id}`}
                            />
                            <label
                              htmlFor={`replace-file-${file.file_id}`}
                              className="cursor-pointer inline-flex items-center px-3 py-1 rounded text-xs font-medium text-orange-600 hover:text-orange-900 border border-orange-300 hover:border-orange-400"
                            >
                              {replacingFileId === file.file_id ? 'Selecting...' : 'Replace'}
                            </label>
                          </>
                          
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDelete(file.file_id)}
                            disabled={deletingFileId === file.file_id}
                            className="text-red-600 hover:text-red-900"
                          >
                            {deletingFileId === file.file_id ? 'Deleting...' : 'Delete'}
                          </Button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
