import React, { useState } from 'react'

interface WelcomeOnboardingProps {
  onComplete: () => void
}

// Developer utility: Expose reset function to window for testing
// Usage in console: window.resetOnboarding()
if (typeof window !== 'undefined') {
  (window as any).resetOnboarding = () => {
    try {
      window.localStorage.removeItem('dizzaroo_onboarding_seen')
      console.log('✅ Onboarding reset. Refresh the page to see it again.')
    } catch (error) {
      console.error('Failed to reset onboarding:', error)
    }
  }
}

const WelcomeOnboarding: React.FC<WelcomeOnboardingProps> = ({ onComplete }) => {
  const [step, setStep] = useState<0 | 1>(0)

  const goNext = () => {
    setStep(1)
  }

  const handleGetStarted = () => {
    onComplete()
  }

  const handleSkip = () => {
    onComplete()
  }

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-dizzaroo-deep-blue/90 via-dizzaroo-blue-green/80 to-dizzaroo-soft-green/90 backdrop-blur-md flex items-center justify-center z-[9999] p-4 animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col transform transition-all duration-300 animate-slideUp">
        {/* Skip button */}
        <div className="flex justify-end p-6 pb-2">
          <button
            onClick={handleSkip}
            className="text-sm text-gray-500 hover:text-gray-700 transition-colors font-medium px-3 py-1 rounded-lg hover:bg-gray-100"
          >
            Skip
          </button>
        </div>

        {/* Card Content */}
        <div className="flex-1 flex flex-col items-center justify-center px-12 py-8">
          {step === 0 ? (
            <>
              {/* Slide 1 */}
              <div className="text-center max-w-2xl space-y-6">
                {/* Icon/Illustration */}
                <div className="flex justify-center mb-6">
                  <div className="relative">
                    <div className="absolute inset-0 bg-gradient-to-br from-dizzaroo-deep-blue to-dizzaroo-blue-green rounded-full blur-2xl opacity-30 animate-pulse"></div>
                    <div className="relative bg-gradient-to-br from-dizzaroo-deep-blue to-dizzaroo-blue-green rounded-full p-8 shadow-xl">
                      <svg className="w-16 h-16 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                    </div>
                  </div>
                </div>
                
                <h2 className="text-4xl font-bold bg-gradient-to-r from-dizzaroo-deep-blue via-dizzaroo-blue-green to-dizzaroo-soft-green bg-clip-text text-transparent mb-4">
                  Welcome to Dizzaroo CRM
                </h2>
                <p className="text-lg text-gray-600 leading-relaxed max-w-xl mx-auto">
                  It's the ultimate tool to up your team's collaboration and productivity. Here are a few tips to keep in your back pocket as you build your workspace.
                </p>
                
                {/* Decorative elements */}
                <div className="flex justify-center gap-2 mt-8">
                  <div className="w-2 h-2 rounded-full bg-dizzaroo-deep-blue animate-bounce" style={{ animationDelay: '0s' }}></div>
                  <div className="w-2 h-2 rounded-full bg-dizzaroo-blue-green animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  <div className="w-2 h-2 rounded-full bg-dizzaroo-soft-green animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                </div>
              </div>
            </>
          ) : (
            <>
              {/* Slide 2 */}
              <div className="text-center max-w-2xl space-y-6">
                {/* Icon/Illustration */}
                <div className="flex justify-center mb-6">
                  <div className="relative">
                    <div className="absolute inset-0 bg-gradient-to-br from-dizzaroo-blue-green to-dizzaroo-soft-green rounded-full blur-2xl opacity-30 animate-pulse"></div>
                    <div className="relative bg-gradient-to-br from-dizzaroo-blue-green to-dizzaroo-soft-green rounded-full p-8 shadow-xl">
                      <svg className="w-16 h-16 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                  </div>
                </div>
                
                <h2 className="text-4xl font-bold bg-gradient-to-r from-dizzaroo-blue-green via-dizzaroo-soft-green to-dizzaroo-deep-blue bg-clip-text text-transparent mb-4">
                  Focus on one topic at a time
                </h2>
                <p className="text-lg text-gray-600 leading-relaxed max-w-xl mx-auto">
                  In Dizzaroo CRM, channels keep your work focused by giving each topic, project, or team its own space.
                </p>
                
                {/* Feature highlights */}
                <div className="grid grid-cols-3 gap-4 mt-8 max-w-md mx-auto">
                  <div className="flex flex-col items-center p-4 rounded-xl bg-gradient-to-br from-blue-50 to-green-50 border border-blue-100">
                    <div className="text-2xl mb-2">🎯</div>
                    <div className="text-xs font-semibold text-gray-700">Organized</div>
                  </div>
                  <div className="flex flex-col items-center p-4 rounded-xl bg-gradient-to-br from-blue-50 to-green-50 border border-blue-100">
                    <div className="text-2xl mb-2">⚡</div>
                    <div className="text-xs font-semibold text-gray-700">Fast</div>
                  </div>
                  <div className="flex flex-col items-center p-4 rounded-xl bg-gradient-to-br from-blue-50 to-green-50 border border-blue-100">
                    <div className="text-2xl mb-2">🤝</div>
                    <div className="text-xs font-semibold text-gray-700">Collaborative</div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Bottom: Dots + Button */}
        <div className="border-t border-gray-200 bg-gradient-to-r from-gray-50 to-white px-8 py-6 flex items-center justify-between">
          {/* Dot indicators */}
          <div className="flex items-center gap-3">
            <Dot active={step === 0} />
            <Dot active={step === 1} />
          </div>

          {/* Action Button */}
          <div className="flex-1 flex justify-end">
            {step === 0 ? (
              <button
                onClick={goNext}
                className="px-8 py-3 bg-gradient-to-r from-dizzaroo-deep-blue to-dizzaroo-blue-green text-white rounded-xl font-semibold hover:from-dizzaroo-blue-green hover:to-dizzaroo-soft-green transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105 flex items-center gap-2"
              >
                <span>Next</span>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            ) : (
              <button
                onClick={handleGetStarted}
                className="px-8 py-3 bg-gradient-to-r from-dizzaroo-deep-blue via-dizzaroo-blue-green to-dizzaroo-soft-green text-white rounded-xl font-semibold hover:shadow-xl transition-all duration-300 shadow-lg transform hover:scale-105 flex items-center gap-2"
              >
                <span>Get Started</span>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// Dot component for step indicator
const Dot: React.FC<{ active: boolean }> = ({ active }) => {
  return (
    <div
      className={`h-2.5 rounded-full transition-all duration-300 ${
        active
          ? 'bg-gradient-to-r from-dizzaroo-deep-blue to-dizzaroo-blue-green w-10 shadow-md'
          : 'bg-gray-300 w-2.5 hover:bg-gray-400'
      }`}
    />
  )
}

export default WelcomeOnboarding

