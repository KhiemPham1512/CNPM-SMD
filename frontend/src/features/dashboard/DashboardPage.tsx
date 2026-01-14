import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { syllabusService } from '../../services/syllabusService'
import { Syllabus } from '../../types'
import { formatDate } from '../../utils/date'
import { StatusBadge } from '../../components/workflow/StatusBadge'

export function DashboardPage() {
  const [syllabi, setSyllabi] = useState<Syllabus[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const data = await syllabusService.list()
      setSyllabi(data)
    } catch (error) {
      console.error('Failed to load syllabi:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusCount = (status: string) => {
    return syllabi.filter(s => s.lifecycle_status === status).length
  }

  const recentSyllabi = [...syllabi]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5)

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mb-4"></div>
          <p className="text-gray-500">Loading dashboard data...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Dashboard</h1>
        <p className="text-gray-600">Overview of your syllabi</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Syllabi"
          value={syllabi.length}
          icon="📚"
        />
        <StatCard
          title="Draft"
          value={getStatusCount('DRAFT')}
          icon="📝"
        />
        <StatCard
          title="Pending Review"
          value={getStatusCount('PENDING_REVIEW')}
          icon="⏳"
        />
        <StatCard
          title="Published"
          value={getStatusCount('PUBLISHED')}
          icon="✅"
        />
      </div>

      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Updates</h2>
        <div className="space-y-3">
          {recentSyllabi.length === 0 ? (
            <p className="text-gray-500">No syllabi yet</p>
          ) : (
            recentSyllabi.map(syllabus => (
              <Link
                key={syllabus.syllabus_id}
                to={`/app/syllabi/${syllabus.syllabus_id}`}
                className="block p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors border border-gray-200"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900">
                      Syllabus ID: {syllabus.syllabus_id}
                    </h3>
                    <p className="text-sm text-gray-600 mt-1">
                      Created {formatDate(syllabus.created_at)}
                    </p>
                  </div>
                  <StatusBadge status={syllabus.lifecycle_status} />
                </div>
              </Link>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

interface StatCardProps {
  title: string
  value: number
  icon: string
}

function StatCard({ title, value, icon }: StatCardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-600 text-sm mb-1">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
        </div>
        <div className="text-4xl">{icon}</div>
      </div>
    </div>
  )
}
