import { WorkflowStatus } from '../../types'

interface WorkflowTimelineProps {
  currentStatus: WorkflowStatus
}

const workflowSteps: WorkflowStatus[] = [
  'DRAFT',
  'PENDING_REVIEW',
  'PENDING_APPROVAL',
  'APPROVED',
  'PUBLISHED',
]

export function WorkflowTimeline({ currentStatus }: WorkflowTimelineProps) {
  const currentIndex = workflowSteps.indexOf(currentStatus)

  return (
    <div className="relative">
      <div className="flex items-center justify-between">
        {workflowSteps.map((step, index) => {
          const isCompleted = index <= currentIndex
          const isCurrent = index === currentIndex

          return (
            <div key={step} className="flex flex-col items-center flex-1">
              <div className="flex items-center w-full">
                <div
                  className={`
                    flex items-center justify-center w-10 h-10 rounded-full border-2 transition-colors
                    ${
                      isCompleted
                        ? 'bg-primary-600 border-primary-600 text-white'
                        : 'bg-white border-gray-300 text-gray-400'
                    }
                    ${isCurrent ? 'ring-2 ring-primary-400 ring-offset-2' : ''}
                  `}
                >
                  {index + 1}
                </div>
                {index < workflowSteps.length - 1 && (
                  <div
                    className={`
                      flex-1 h-0.5 mx-2
                      ${isCompleted ? 'bg-primary-600' : 'bg-gray-300'}
                    `}
                  />
                )}
              </div>
              <div className="mt-2 text-center">
                <p
                  className={`
                    text-xs font-medium
                    ${isCompleted ? 'text-gray-900' : 'text-gray-500'}
                  `}
                >
                  {step.replace(/_/g, ' ')}
                </p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
