import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { syllabusService } from '../../services/syllabusService'
import { Syllabus } from '../../types'
import { formatDate } from '../../utils/date'
import { StatusBadge } from '../../components/workflow/StatusBadge'
import { Table } from '../../components/ui/Table'
import { Button } from '../../components/ui/Button'

export function PrincipalReviewQueuePage() {
  const [syllabi, setSyllabi] = useState<Syllabus[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadPendingReviews()
  }, [])

  const loadPendingReviews = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await syllabusService.getPrincipalPendingReviews()
      setSyllabi(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load pending reviews')
      console.error('Failed to load pending reviews:', err)
    } finally {
      setLoading(false)
    }
  }

  const columns = [
    {
      key: 'syllabus_id',
      header: 'Syllabus ID',
      accessor: (s: Syllabus) => s.syllabus_id,
    },
    {
      key: 'subject_id',
      header: 'Subject ID',
      accessor: (s: Syllabus) => s.subject_id,
    },
    {
      key: 'program_id',
      header: 'Program ID',
      accessor: (s: Syllabus) => s.program_id,
    },
    {
      key: 'owner_lecturer_id',
      header: 'Lecturer ID',
      accessor: (s: Syllabus) => s.owner_lecturer_id,
    },
    {
      key: 'status',
      header: 'Status',
      render: (s: Syllabus) => <StatusBadge status={s.lifecycle_status} />,
    },
    {
      key: 'created_at',
      header: 'Created',
      accessor: (s: Syllabus) => formatDate(s.created_at),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (s: Syllabus) => (
        <Link to={`/app/principal/reviews/${s.syllabus_id}`}>
          <Button size="sm">Review</Button>
        </Link>
      ),
    },
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mb-4"></div>
          <p className="text-gray-500">Loading pending reviews...</p>
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
        <Button onClick={loadPendingReviews}>Retry</Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Principal Review Queue</h1>
          <p className="text-gray-600">Syllabi approved and ready to publish</p>
        </div>
        <Button onClick={loadPendingReviews} variant="outline">
          Refresh
        </Button>
      </div>

      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        {syllabi.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg mb-2">No pending reviews</p>
            <p className="text-sm">All syllabi have been published or are in other stages.</p>
          </div>
        ) : (
          <Table columns={columns} data={syllabi} />
        )}
      </div>
    </div>
  )
}
