import { useEffect, useState } from 'react'
import { adminService } from '../../services/adminService'
import { formatDate } from '../../utils/date'
import { StatusBadge } from '../../components/workflow/StatusBadge'
import { Table } from '../../components/ui/Table'
import { Button } from '../../components/ui/Button'
import { Modal } from '../../components/ui/Modal'
import { Link } from 'react-router-dom'

interface PublishedSyllabus {
  syllabus_id: number
  subject_id: number
  program_id: number
  owner_lecturer_id: number
  current_version_id: number | null
  lifecycle_status: string
  created_at: string
}

export function PublishingManagementPage() {
  const [syllabi, setSyllabi] = useState<PublishedSyllabus[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedVersionId, setSelectedVersionId] = useState<number | null>(null)
  const [isUnpublishModalOpen, setIsUnpublishModalOpen] = useState(false)
  const [isArchiveModalOpen, setIsArchiveModalOpen] = useState(false)
  const [processing, setProcessing] = useState(false)

  useEffect(() => {
    loadPublished()
  }, [])

  const loadPublished = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await adminService.listPublished()
      setSyllabi(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load published syllabi')
      console.error('Failed to load published syllabi:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleUnpublish = async () => {
    if (!selectedVersionId) return
    
    try {
      setProcessing(true)
      await adminService.unpublishVersion(selectedVersionId)
      setIsUnpublishModalOpen(false)
      setSelectedVersionId(null)
      await loadPublished()
      alert('Syllabus unpublished successfully')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to unpublish')
    } finally {
      setProcessing(false)
    }
  }

  const handleArchive = async () => {
    if (!selectedVersionId) return
    
    try {
      setProcessing(true)
      await adminService.archiveVersion(selectedVersionId)
      setIsArchiveModalOpen(false)
      setSelectedVersionId(null)
      await loadPublished()
      alert('Syllabus version archived successfully')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to archive')
    } finally {
      setProcessing(false)
    }
  }

  const columns = [
    {
      key: 'syllabus_id',
      header: 'Syllabus ID',
      accessor: (s: PublishedSyllabus) => s.syllabus_id,
    },
    {
      key: 'subject_id',
      header: 'Subject ID',
      accessor: (s: PublishedSyllabus) => s.subject_id,
    },
    {
      key: 'program_id',
      header: 'Program ID',
      accessor: (s: PublishedSyllabus) => s.program_id,
    },
    {
      key: 'owner_lecturer_id',
      header: 'Lecturer ID',
      accessor: (s: PublishedSyllabus) => s.owner_lecturer_id,
    },
    {
      key: 'status',
      header: 'Status',
      render: (s: PublishedSyllabus) => <StatusBadge status={s.lifecycle_status as 'DRAFT' | 'PENDING_REVIEW' | 'PENDING_APPROVAL' | 'APPROVED' | 'PUBLISHED'} />,
    },
    {
      key: 'created_at',
      header: 'Created',
      accessor: (s: PublishedSyllabus) => formatDate(s.created_at),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (s: PublishedSyllabus) => (
        <div className="flex gap-2">
          <Link to={`/app/syllabi/${s.syllabus_id}`}>
            <Button size="sm" variant="outline">View</Button>
          </Link>
          {s.current_version_id && (
            <>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => {
                  setSelectedVersionId(s.current_version_id!)
                  setIsUnpublishModalOpen(true)
                }}
                disabled={processing}
              >
                Unpublish
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setSelectedVersionId(s.current_version_id!)
                  setIsArchiveModalOpen(true)
                }}
                disabled={processing}
              >
                Archive
              </Button>
            </>
          )}
        </div>
      ),
    },
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mb-4"></div>
          <p className="text-gray-500">Loading published syllabi...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
        <Button onClick={loadPublished}>Retry</Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Publishing Management</h1>
          <p className="text-gray-600">Manage published syllabi</p>
        </div>
        <Button onClick={loadPublished} variant="outline">
          Refresh
        </Button>
      </div>

      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        {syllabi.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg mb-2">No published syllabi</p>
            <p className="text-sm">No syllabi have been published yet.</p>
          </div>
        ) : (
          <Table columns={columns} data={syllabi} />
        )}
      </div>

      {/* Unpublish Modal */}
      <Modal
        isOpen={isUnpublishModalOpen}
        onClose={() => {
          setIsUnpublishModalOpen(false)
          setSelectedVersionId(null)
        }}
        title="Unpublish Syllabus"
        footer={
          <>
            <Button
              variant="outline"
              onClick={() => {
                setIsUnpublishModalOpen(false)
                setSelectedVersionId(null)
              }}
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
          Are you sure you want to unpublish this syllabus? It will be moved back to APPROVED status.
        </p>
      </Modal>

      {/* Archive Modal */}
      <Modal
        isOpen={isArchiveModalOpen}
        onClose={() => {
          setIsArchiveModalOpen(false)
          setSelectedVersionId(null)
        }}
        title="Archive Syllabus Version"
        footer={
          <>
            <Button
              variant="outline"
              onClick={() => {
                setIsArchiveModalOpen(false)
                setSelectedVersionId(null)
              }}
              disabled={processing}
            >
              Cancel
            </Button>
            <Button
              variant="outline"
              onClick={handleArchive}
              disabled={processing}
            >
              {processing ? 'Archiving...' : 'Confirm Archive'}
            </Button>
          </>
        }
      >
        <p className="text-gray-700">
          Are you sure you want to archive this syllabus version? Archived versions are kept for historical reference.
        </p>
      </Modal>
    </div>
  )
}
