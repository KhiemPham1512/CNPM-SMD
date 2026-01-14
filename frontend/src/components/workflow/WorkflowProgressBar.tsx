interface WorkflowStep {
  code: string
  label: string
  order: number
}

interface WorkflowProgressBarProps {
  steps: WorkflowStep[]
  currentStatus: string
}

export function WorkflowProgressBar({ steps, currentStatus }: WorkflowProgressBarProps) {
  // Find current step index
  const currentStepIndex = steps.findIndex(step => step.code === currentStatus)
  
  // Sort steps by order to ensure correct display
  const sortedSteps = [...steps].sort((a, b) => a.order - b.order)

  return (
    <div className="w-full py-6">
      <div className="relative">
        {/* Progress line */}
        <div className="absolute top-5 left-0 right-0 h-0.5 bg-gray-200">
          <div
            className="h-full bg-primary-600 transition-all duration-300"
            style={{
              width: currentStepIndex >= 0 
                ? `${(currentStepIndex / (sortedSteps.length - 1)) * 100}%` 
                : '0%'
            }}
          />
        </div>

        {/* Steps */}
        <div className="relative flex justify-between">
          {sortedSteps.map((step, index) => {
            const isCompleted = currentStepIndex >= 0 && index < currentStepIndex
            const isCurrent = index === currentStepIndex

            return (
              <div key={step.code} className="flex flex-col items-center flex-1">
                {/* Step circle */}
                <div
                  className={`
                    relative z-10 flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all duration-300
                    ${
                      isCompleted
                        ? 'bg-primary-600 border-primary-600 text-white'
                        : isCurrent
                        ? 'bg-white border-primary-600 text-primary-600 ring-2 ring-primary-400 ring-offset-2'
                        : 'bg-white border-gray-300 text-gray-400'
                    }
                  `}
                >
                  {isCompleted ? (
                    <svg
                      className="w-6 h-6"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  ) : (
                    <span className="text-sm font-semibold">{index + 1}</span>
                  )}
                </div>

                {/* Step label */}
                <div className="mt-3 text-center">
                  <p
                    className={`
                      text-xs font-medium
                      ${
                        isCompleted || isCurrent
                          ? 'text-gray-900'
                          : 'text-gray-500'
                      }
                    `}
                  >
                    {step.label}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
