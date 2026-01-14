import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { syllabusService } from '../../services/syllabusService'
import { Syllabus } from '../../types'
import { formatDate } from '../../utils/date'
import { StatusBadge } from '../../components/workflow/StatusBadge'
import { Input } from '../../components/ui/Input'
import { Select } from '../../components/ui/Select'
import { Table } from '../../components/ui/Table'
import { Button } from '../../components/ui/Button'
import { Tooltip } from '../../components/ui/Tooltip'
import { useAuth } from '../../app/store/authContext'

export function SyllabusListPage() {
  const { state } = useAuth()
  const [syllabi, setSyllabi] = useState<Syllabus[]>([])
  const [filteredSyllabi, setFilteredSyllabi] = useState<Syllabus[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [showMineOnly, setShowMineOnly] = useState(false)
  
  const isLecturer = state.roles.includes('LECTURER')
  const isOwner = (syllabus: Syllabus) => syllabus.owner_lecturer_id === state.user?.user_id
  const canEditSyllabus = (syllabus: Syllabus) => 
    syllabus.lifecycle_status === 'DRAFT' && 
    isLecturer && 
    isOwner(syllabus)

  useEffect(() => {
    loadSyllabi()
  }, [showMineOnly])

  useEffect(() => {
    filterSyllabi()
  }, [syllabi, searchQuery, statusFilter])

  const loadSyllabi = async () => {
    try {
      setLoading(true)
      // If lecturer and showMineOnly is true, use mine=true filter
      const data = await syllabusService.list(isLecturer && showMineOnly)
      setSyllabi(data)
    } catch (error) {
      console.error('Failed to load syllabi:', error)
    } finally {
      setLoading(false)
    }
  }

  const filterSyllabi = () => {
    let filtered = [...syllabi]

    // Filter by status
    if (statusFilter !== 'all') {
      filtered = filtered.filter(s => s.lifecycle_status === statusFilter)
    }

    // Filter by search query (search in syllabus_id, subject_id, program_id)
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(s => 
        s.syllabus_id.toString().includes(query) ||
        s.subject_id.toString().includes(query) ||
        s.program_id.toString().includes(query)
      )
    }

    // Sort by created date (newest first)
    filtered.sort((a, b) => 
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )

    setFilteredSyllabi(filtered)
  }

  const canCreate = state.roles.includes('LECTURER') || state.roles.includes('ADMIN')

  const columns = [
    {
      key: 'syllabus_id',
      header: 'ID',
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
        <div className="flex space-x-2">
          <Link to={`/app/syllabi/${s.syllabus_id}`}>
            <Button variant="outline" size="sm">View</Button>
          </Link>
          {canEditSyllabus(s) && (
            <Link to={`/app/syllabi/${s.syllabus_id}/edit`}>
              <Button size="sm">Edit</Button>
            </Link>
          )}
          <Tooltip content="Version comparison feature - coming soon">
            <Button
              size="sm"
              variant="secondary"
              disabled
            >
              Compare
            </Button>
          </Tooltip>
        </div>
      ),
    },
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mb-4"></div>
          <p className="text-gray-500">Loading syllabi...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Syllabi</h1>
          <p className="text-gray-600">Manage your syllabi</p>
        </div>
        {canCreate && (
          <Link to="/app/syllabi/new">
            <Button>Create Syllabus</Button>
          </Link>
        )}
      </div>

      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <Input
            placeholder="Search by ID, Subject ID, or Program ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <Select
            options={[
              { value: 'all', label: 'All Statuses' },
              { value: 'DRAFT', label: 'Draft' },
              { value: 'PENDING_REVIEW', label: 'Pending Review' },
              { value: 'PENDING_APPROVAL', label: 'Pending Approval' },
              { value: 'APPROVED', label: 'Approved' },
              { value: 'PUBLISHED', label: 'Published' },
            ]}
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          />
          {isLecturer && (
            <div className="flex items-center">
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={showMineOnly}
                  onChange={(e) => setShowMineOnly(e.target.checked)}
                  className="mr-2 h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="text-sm text-gray-700">My Syllabi Only</span>
              </label>
            </div>
          )}
        </div>

        <Table columns={columns} data={filteredSyllabi} />
      </div>
    </div>
  )
}
