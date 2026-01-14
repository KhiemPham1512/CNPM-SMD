import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { publicService } from '../../services/publicService'
import { Syllabus } from '../../types'
import { formatDate } from '../../utils/date'
import { StatusBadge } from '../../components/workflow/StatusBadge'
import { Button } from '../../components/ui/Button'
import { Modal } from '../../components/ui/Modal'
import { Tooltip } from '../../components/ui/Tooltip'
import { useAuth } from '../../app/store/authContext'

export function PublicSyllabusPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { state } = useAuth()
  const [syllabus, setSyllabus] = useState<Syllabus | null>(null)
  const [loading, setLoading] = useState(true)
  const isStudent = state.roles.includes('STUDENT')
  const isAuthenticated = !!state.user
  
  // Subscribe state (currently unused - buttons are disabled with "not implemented" tooltip)
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  // Note: success and isSubscribed are set in handlers but not displayed yet
  // They will be used when subscribe/feedback features are fully implemented
  const [, setSuccess] = useState<string | null>(null)
  const [, setIsSubscribed] = useState(false)
  
  // Feedback state
  const [isFeedbackModalOpen, setIsFeedbackModalOpen] = useState(false)
  const [feedbackContent, setFeedbackContent] = useState('')
  const [feedbackRating, setFeedbackRating] = useState(0)

  useEffect(() => {
    if (id) {
      loadSyllabus(parseInt(id))
    }
  }, [id])

  const loadSyllabus = async (syllabusId: number) => {
    try {
      const data = await publicService.getPublicSyllabus(syllabusId)
      if (data && data.lifecycle_status === 'PUBLISHED') {
        setSyllabus(data)
      }
    } catch (err) {
      console.error('Failed to load syllabus:', err)
    } finally {
      setLoading(false)
    }
  }

  // Subscribe handler - currently not called because Subscribe button is disabled with tooltip
  // TODO: Enable button and implement full subscribe functionality
  // This function will be used when the Subscribe button is enabled
  const handleSubscribe = async () => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }

    if (!id) return

    try {
      setProcessing(true)
      setError(null)
      await publicService.subscribe(parseInt(id))
      setIsSubscribed(true)
      setSuccess('Subscribed successfully! You will receive notifications when this syllabus is updated.')
      setTimeout(() => setSuccess(null), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to subscribe')
    } finally {
      setProcessing(false)
    }
  }
  // Suppress unused variable warning - function kept for future implementation
  void handleSubscribe

  const handleSubmitFeedback = async () => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }

    if (!id || !feedbackContent.trim()) {
      setError('Feedback content is required')
      return
    }

    try {
      setProcessing(true)
      setError(null)
      await publicService.submitFeedback(parseInt(id), feedbackContent.trim(), feedbackRating || undefined)
      setSuccess('Feedback submitted successfully!')
      setIsFeedbackModalOpen(false)
      setFeedbackContent('')
      setFeedbackRating(0)
      setTimeout(() => setSuccess(null), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit feedback')
    } finally {
      setProcessing(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mb-4"></div>
          <p className="text-gray-500">Loading syllabus...</p>
        </div>
      </div>
    )
  }

  if (!syllabus) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <div className="bg-white rounded-lg shadow p-8 border border-gray-200 text-center max-w-md">
          <p className="text-gray-500 text-lg mb-2">Syllabus not found</p>
          <p className="text-gray-600 text-sm">This syllabus may not be published or does not exist.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow p-8 border border-gray-200">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Syllabus #{syllabus.syllabus_id}
              </h1>
              <p className="text-gray-600">Subject ID: {syllabus.subject_id}</p>
            </div>
            <StatusBadge status={syllabus.lifecycle_status} />
          </div>

          <div className="grid grid-cols-2 gap-6 mb-6">
            <div>
              <p className="text-sm text-gray-600 mb-1">Program ID</p>
              <p className="text-gray-900">{syllabus.program_id}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Lecturer ID</p>
              <p className="text-gray-900">{syllabus.owner_lecturer_id}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Created</p>
              <p className="text-gray-900">{formatDate(syllabus.created_at)}</p>
            </div>
          </div>

          {isStudent && (
            <div className="border-t border-gray-200 pt-6 mb-6">
              <div className="flex gap-3">
                <Tooltip content="Subscription feature not implemented yet">
                  <Button disabled>
                    Subscribe
                  </Button>
                </Tooltip>
                <Tooltip content="Feedback feature not implemented yet">
                  <Button variant="outline" disabled>
                    Send Feedback
                  </Button>
                </Tooltip>
              </div>
            </div>
          )}

          {/* AI Summary Section */}
          {syllabus.ai_summary && (
            <div className="border-t border-gray-200 pt-6 mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">AI Summary</h2>
              <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
                <p className="text-gray-700 whitespace-pre-wrap">{syllabus.ai_summary.summary_text}</p>
                {syllabus.ai_summary.generated_at && (
                  <p className="text-xs text-gray-500 mt-3">
                    Generated: {formatDate(syllabus.ai_summary.generated_at)}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Relationship Tree Placeholder */}
          <div className="border-t border-gray-200 pt-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Subject Relationships</h2>
            <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
              <p className="text-gray-600 italic">
                Relationship tree/map visualization will be displayed here (placeholder).
              </p>
              <p className="text-sm text-gray-500 mt-2">
                This feature shows prerequisite and related subjects.
              </p>
            </div>
          </div>

          {/* Syllabus Content */}
          <div className="border-t border-gray-200 pt-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Syllabus Content</h2>
            <div className="bg-gray-50 rounded-lg p-6 min-h-[300px] border border-gray-200">
              <p className="text-gray-600">Syllabus content would be displayed here...</p>
            </div>
          </div>
        </div>
      </div>

      {/* Feedback Modal */}
      <Modal
        isOpen={isFeedbackModalOpen}
        onClose={() => {
          setIsFeedbackModalOpen(false)
          setFeedbackContent('')
          setFeedbackRating(0)
          setError(null)
        }}
        title="Send Feedback"
        footer={
          <>
            <Button
              variant="outline"
              onClick={() => {
                setIsFeedbackModalOpen(false)
                setFeedbackContent('')
                setFeedbackRating(0)
                setError(null)
              }}
              disabled={processing}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmitFeedback}
              disabled={processing || !feedbackContent.trim()}
            >
              {processing ? 'Submitting...' : 'Submit Feedback'}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Rating (Optional)
            </label>
            <select
              value={feedbackRating}
              onChange={(e) => setFeedbackRating(parseInt(e.target.value))}
              className="w-full px-4 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value={0}>No rating</option>
              <option value={1}>1 - Poor</option>
              <option value={2}>2 - Fair</option>
              <option value={3}>3 - Good</option>
              <option value={4}>4 - Very Good</option>
              <option value={5}>5 - Excellent</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Feedback / Report Issue <span className="text-red-500">*</span>
            </label>
            <textarea
              value={feedbackContent}
              onChange={(e) => setFeedbackContent(e.target.value)}
              placeholder="Describe the issue or provide feedback..."
              rows={6}
              className="w-full px-4 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
            />
            <p className="mt-1 text-sm text-gray-500">
              Please describe any errors or issues you found in this syllabus.
            </p>
          </div>
        </div>
      </Modal>
    </div>
  )
}
