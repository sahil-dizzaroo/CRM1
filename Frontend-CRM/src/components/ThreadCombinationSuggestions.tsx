import React, { useState, useEffect, useMemo } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useStudySite } from '../contexts/StudySiteContext'
import { api } from '../lib/api'

interface ThreadCombinationSuggestion {
  thread1_id: string
  thread2_id: string
  thread1_title: string
  thread2_title: string
  should_combine: boolean
  similarity_score: number
  reasoning: string
  factors: string[]
  recommendation: 'strong' | 'moderate' | 'weak' | 'no'
}

interface ThreadCombinationSuggestionsProps {
  apiBase: string
  onCombined?: () => void
}

const ThreadCombinationSuggestions: React.FC<ThreadCombinationSuggestionsProps> = ({
  apiBase,
  onCombined
}) => {
  const { selectedStudyId, selectedSiteId } = useStudySite()
  const { token } = useAuth()

  const [suggestions, setSuggestions] = useState<ThreadCombinationSuggestion[]>([])
  const [loading, setLoading] = useState(false)
  const [combining, setCombining] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selectedSuggestion, setSelectedSuggestion] =
    useState<ThreadCombinationSuggestion | null>(null)

  const loadSuggestions = async () => {
    if (!selectedStudyId || !selectedSiteId) return

    setLoading(true)
    setError(null)

    try {
      const response = await api.get('/threads/suggest-combinations', {
        params: {
          study_id: selectedStudyId,
          site_id: selectedSiteId,
          limit: 10
        }
      })

      const suggestionsData = response.data || []

      const validSuggestions: ThreadCombinationSuggestion[] = []
      for (const suggestion of suggestionsData) {
        try {
          await api.get(`/threads/${suggestion.thread1_id}?limit=1`)
          validSuggestions.push(suggestion)
        } catch {
          console.log(
            `Skipping suggestion - thread ${suggestion.thread1_id} no longer exists`
          )
        }
      }

      setSuggestions(validSuggestions)
    } catch (err: any) {
      if (err.response?.status === 404) {
        setSuggestions([])
      } else {
        setError(
          err.response?.data?.detail ||
            err.message ||
            'Failed to load suggestions'
        )
        console.error('Error loading suggestions:', err)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSuggestions()
  }, [selectedStudyId, selectedSiteId, token])

  const handleCombine = async (suggestion: ThreadCombinationSuggestion) => {
    if (
      !confirm(
        `Are you sure you want to combine these threads?\n\n"${suggestion.thread1_title}"\nand\n"${suggestion.thread2_title}"\n\nThis will merge all messages, participants, and attachments.`
      )
    ) {
      return
    }

    setCombining(`${suggestion.thread1_id}-${suggestion.thread2_id}`)
    setError(null)

    try {
      await api.post('/threads/combine', {
        thread1_id: suggestion.thread1_id,
        thread2_id: suggestion.thread2_id,
        target_thread_id: suggestion.thread1_id
      })

      setTimeout(async () => {
        await loadSuggestions()
        setSelectedSuggestion(null)
      }, 800)

      if (onCombined) onCombined()
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          'Failed to combine threads'
      )
      console.error('Error combining threads:', err)
    } finally {
      setCombining(null)
    }
  }



  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation) {
      case 'strong':
        return 'bg-green-100 text-green-800 border-green-300'
      case 'moderate':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'weak':
        return 'bg-orange-100 text-orange-800 border-orange-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  if (!selectedStudyId || !selectedSiteId) {
    return null
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-2 mb-2">
        <div className="flex items-center justify-center py-4">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-dizzaroo-deep-blue"></div>
          <span className="ml-2 text-xs text-gray-600">Analyzing threads...</span>
        </div>
      </div>
    )
  }

  if (suggestions.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-2 mb-2">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-xs font-semibold text-gray-800">🤖 AI Suggestions</h3>
          <button
            onClick={loadSuggestions}
            className="text-xs text-dizzaroo-deep-blue hover:underline"
          >
            🔄
          </button>
        </div>
        <p className="text-gray-500 text-xs">No similar threads found.</p>
      </div>
    )
  }

  return (
    <>
      <div className="bg-white rounded-lg shadow p-2 mb-2">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-xs font-semibold text-gray-800">🤖 AI Suggestions</h3>
          <button
            onClick={loadSuggestions}
            className="text-xs text-dizzaroo-deep-blue hover:underline"
            disabled={loading}
            title="Refresh suggestions"
          >
            🔄
          </button>
        </div>

        {error && (
          <div className="mb-2 p-1.5 bg-red-50 border border-red-200 rounded text-red-700 text-xs">
            {error.length > 60 ? `${error.substring(0, 60)}...` : error}
          </div>
        )}

        <div className="space-y-2 max-h-80 overflow-y-auto">
          {suggestions.map((suggestion, index) => {
            const combineKey = `${suggestion.thread1_id}-${suggestion.thread2_id}`
            const isCombining = combining === combineKey

            return (
              <div
                key={index}
                className="border rounded-lg p-2 hover:shadow-md transition-all bg-white cursor-pointer"
                onClick={() => setSelectedSuggestion(suggestion)}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 mb-1">
                      <span className={`px-1.5 py-0.5 rounded text-xs font-medium border ${getRecommendationColor(suggestion.recommendation)}`}>
                        {suggestion.recommendation.toUpperCase()}
                      </span>
                      <span className="text-xs font-semibold text-gray-700">
                        {suggestion.similarity_score.toFixed(0)}%
                      </span>
                    </div>
                    <div className="space-y-0.5 mb-1">
                      <div className="text-xs font-medium text-gray-800 truncate" title={suggestion.thread1_title}>
                        T1: {suggestion.thread1_title.length > 20 ? `${suggestion.thread1_title.substring(0, 20)}...` : suggestion.thread1_title}
                      </div>
                      <div className="text-xs font-medium text-gray-800 truncate" title={suggestion.thread2_title}>
                        T2: {suggestion.thread2_title.length > 20 ? `${suggestion.thread2_title.substring(0, 20)}...` : suggestion.thread2_title}
                      </div>
                    </div>
                    <div className="text-xs text-gray-600 line-clamp-2 mb-1">
                      {suggestion.reasoning.length > 70 
                        ? `${suggestion.reasoning.substring(0, 70)}...` 
                        : suggestion.reasoning}
                    </div>
                    {suggestion.factors && suggestion.factors.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {suggestion.factors.slice(0, 2).map((factor, idx) => (
                          <span
                            key={idx}
                            className="px-1.5 py-0.5 bg-blue-50 text-blue-700 rounded text-xs"
                          >
                            {factor.length > 10 ? `${factor.substring(0, 10)}...` : factor}
                          </span>
                        ))}
                        {suggestion.factors.length > 2 && (
                          <span className="px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                            +{suggestion.factors.length - 2}
                          </span>
                        )}
                      </div>
                    )}
                    <div className="text-xs text-dizzaroo-deep-blue mt-1 font-medium">
                      Click to view details →
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleCombine(suggestion)
                    }}
                    disabled={isCombining}
                    className="ml-2 px-2 py-1 bg-dizzaroo-deep-blue text-white rounded-lg hover:bg-dizzaroo-blue-green disabled:opacity-50 disabled:cursor-not-allowed transition text-xs font-medium whitespace-nowrap flex-shrink-0"
                    title="Combine these threads"
                  >
                    {isCombining ? '...' : 'Combine'}
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Detail Modal/Card */}
      {selectedSuggestion && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedSuggestion(null)}
        >
          <div 
            className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between rounded-t-xl z-10">
              <h3 className="text-lg font-bold text-gray-800">Thread Combination Details</h3>
              <button
                onClick={() => setSelectedSuggestion(null)}
                className="text-gray-500 hover:text-gray-700 text-2xl font-bold w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 transition"
              >
                ×
              </button>
            </div>

            <div className="p-6 space-y-4">
              {/* Recommendation Badge */}
              <div className="flex items-center gap-3">
                <span className={`px-3 py-1.5 rounded-lg text-sm font-semibold border ${getRecommendationColor(selectedSuggestion.recommendation)}`}>
                  {selectedSuggestion.recommendation.toUpperCase()} MATCH
                </span>
                <span className="text-lg font-bold text-gray-700">
                  {selectedSuggestion.similarity_score.toFixed(1)}% Similar
                </span>
              </div>

              {/* Thread Titles */}
              <div className="space-y-3">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-1">Thread 1</div>
                  <div className="text-base font-medium text-gray-800">{selectedSuggestion.thread1_title}</div>
                </div>
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="text-xs font-semibold text-green-600 uppercase tracking-wide mb-1">Thread 2</div>
                  <div className="text-base font-medium text-gray-800">{selectedSuggestion.thread2_title}</div>
                </div>
              </div>

              {/* Reasoning */}
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <div className="text-sm font-semibold text-gray-700 mb-2">Reasoning</div>
                <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {selectedSuggestion.reasoning}
                </div>
              </div>

              {/* Factors */}
              {selectedSuggestion.factors && selectedSuggestion.factors.length > 0 && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <div className="text-sm font-semibold text-gray-700 mb-3">Similarity Factors</div>
                  <div className="flex flex-wrap gap-2">
                    {selectedSuggestion.factors.map((factor, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1.5 bg-blue-100 text-blue-800 rounded-lg text-sm font-medium"
                      >
                        {factor}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Action Button */}
              <div className="flex gap-3 pt-4 border-t border-gray-200">
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setSelectedSuggestion(null)
                    handleCombine(selectedSuggestion)
                  }}
                  disabled={combining === `${selectedSuggestion.thread1_id}-${selectedSuggestion.thread2_id}`}
                  className="flex-1 px-4 py-2.5 bg-dizzaroo-deep-blue text-white rounded-lg hover:bg-dizzaroo-blue-green disabled:opacity-50 disabled:cursor-not-allowed transition font-medium"
                >
                  {combining === `${selectedSuggestion.thread1_id}-${selectedSuggestion.thread2_id}` 
                    ? 'Combining...' 
                    : 'Combine These Threads'}
                </button>
                <button
                  onClick={() => setSelectedSuggestion(null)}
                  className="px-4 py-2.5 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition font-medium"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default ThreadCombinationSuggestions
