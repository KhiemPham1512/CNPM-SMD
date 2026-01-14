import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { publicService } from '../../services/publicService'
import { Syllabus } from '../../types'
import { formatDate } from '../../utils/date'
import { StatusBadge } from '../../components/workflow/StatusBadge'
import { Input } from '../../components/ui/Input'

export function PublicSearchPage() {
  const [filteredSyllabi, setFilteredSyllabi] = useState<Syllabus[]>([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      loadPublishedSyllabi(searchQuery)
    }, 400)
    return () => clearTimeout(timeoutId)
  }, [searchQuery])

  const loadPublishedSyllabi = async (search?: string) => {
    setLoading(true)
    try {
      const query = search?.trim() || undefined
      const data = await publicService.searchSyllabi(query)
      setFilteredSyllabi(data)
    } catch (error) {
      console.error('Failed to load published syllabi:', error)
      setFilteredSyllabi([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Syllabus Search</h1>
          <p className="text-gray-600">Search and view published syllabi</p>
        </div>

        <div className="mb-6">
          <Input
            placeholder="Search by subject code, name, or keyword..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <p className="mt-2 text-sm text-gray-500">
            Search by subject code, name, syllabus ID, subject ID, or program ID
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mb-4"></div>
              <p className="text-gray-500">Loading published syllabi...</p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredSyllabi.length === 0 ? (
              <div className="col-span-full text-center text-gray-500 py-12">
                {searchQuery ? 'No syllabi match your search' : 'No published syllabi available'}
              </div>
            ) : (
              filteredSyllabi.map(syllabus => (
                <Link
                  key={syllabus.syllabus_id}
                  to={`/public/syllabi/${syllabus.syllabus_id}`}
                  className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow border border-gray-200"
                >
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="font-semibold text-gray-900">Syllabus #{syllabus.syllabus_id}</h3>
                    <StatusBadge status={syllabus.lifecycle_status} />
                  </div>
                  <p className="text-sm text-gray-600">Subject ID: {syllabus.subject_id}</p>
                  <p className="text-sm text-gray-600">Program ID: {syllabus.program_id}</p>
                  <p className="text-xs text-gray-500 mt-2">Created {formatDate(syllabus.created_at)}</p>
                </Link>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  )
}
