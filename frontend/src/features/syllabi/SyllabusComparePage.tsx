import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { syllabusService } from '../../services/syllabusService'
import { Syllabus } from '../../types'

export function SyllabusComparePage() {
  const { id } = useParams<{ id: string }>()
  const [syllabus, setSyllabus] = useState<Syllabus | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (id) {
      loadSyllabus(parseInt(id))
    }
  }, [id])

  const loadSyllabus = async (syllabusId: number) => {
    try {
      const data = await syllabusService.getById(syllabusId)
      setSyllabus(data)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mb-4"></div>
          <p className="text-gray-500">Loading...</p>
        </div>
      </div>
    )
  }

  if (!syllabus) {
    return (
      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg">Syllabus not found</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Compare Versions</h1>
        <p className="text-gray-600">
          Syllabus #{syllabus.syllabus_id}
        </p>
      </div>

      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        <div className="text-center py-12 text-gray-500">
          Version comparison feature - coming soon
        </div>
      </div>
    </div>
  )
}
