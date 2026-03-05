import React, { useState, FormEvent, ChangeEvent, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { TaskLinks, TaskStatus } from '../types'
import { getAiTaskSuggestion, AiTaskSuggestionInput } from '../services/aiService'

interface TaskFormModalProps {
  isOpen: boolean
  onClose: () => void
  onTaskCreated?: (task: any) => void
  initialTitle?: string
  initialDescription?: string
  defaultLinks?: TaskLinks
  // For AI
  aiInput?: AiTaskSuggestionInput
  enableAiAssist?: boolean
  apiBase: string
}

const TaskFormModal: React.FC<TaskFormModalProps> = ({
  isOpen,
  onClose,
  onTaskCreated,
  initialTitle = '',
  initialDescription = '',
  defaultLinks,
  aiInput,
  enableAiAssist = false,
  apiBase
}) => {
  const { user, token } = useAuth()
  const [title, setTitle] = useState(initialTitle)
  const [description, setDescription] = useState(initialDescription)
  const [status, setStatus] = useState<TaskStatus>('open')
  const [dueDate, setDueDate] = useState<string>('')
  const [isAiLoading, setIsAiLoading] = useState(false)
  const [aiError, setAiError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Reset form when modal opens/closes or initial values change
  useEffect(() => {
    if (isOpen) {
      setTitle(initialTitle)
      setDescription(initialDescription)
      setStatus('open')
      setDueDate('')
      setAiError(null)
    }
  }, [isOpen, initialTitle, initialDescription])

  const handleAiSuggest = async () => {
    if (!aiInput || !enableAiAssist) return

    setIsAiLoading(true)
    setAiError(null)

    try {
      const result = await getAiTaskSuggestion(apiBase, token, aiInput)
      
      // Only update if fields are empty or very short
      if (!title || title.trim().length < 10) {
        setTitle(result.title || title)
      }
      
      if (!description || description.trim().length < 20) {
        setDescription(result.description || description)
      }
      
      if (result.suggestedDueDate && !dueDate) {
        setDueDate(result.suggestedDueDate)
      }
      
      if (result.suggestedStatus) {
        setStatus(result.suggestedStatus as TaskStatus)
      }
    } catch (error: any) {
      console.error('AI suggestion error:', error)
      setAiError(error.message || 'Failed to get AI suggestion')
    } finally {
      setIsAiLoading(false)
    }
  }

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    
    if (!title.trim()) {
      alert('Title is required')
      return
    }

    setIsSubmitting(true)

    try {
      const taskData = {
        title: title.trim(),
        description: description.trim() || undefined,
        status,
        dueDate: dueDate || undefined,
        createdByUserId: user?.user_id,
        links: defaultLinks || undefined,
        // Legacy fields for backward compatibility
        siteId: defaultLinks?.siteId,
        monitoringVisitId: defaultLinks?.monitoringVisitId,
        monitoringReportId: defaultLinks?.monitoringReportId,
        sourceConversationId: defaultLinks?.conversationId,
      }

      const response = await fetch(`${apiBase}/tasks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify(taskData)
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to create task' }))
        throw new Error(errorData.detail || 'Failed to create task')
      }

      const createdTask = await response.json()
      
      if (onTaskCreated) {
        onTaskCreated(createdTask)
      }

      onClose()
    } catch (error: any) {
      console.error('Error creating task:', error)
      alert(error.message || 'Failed to create task')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!isOpen) return null

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" 
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto" 
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Create Task</h2>
          <button 
            className="text-2xl text-gray-500 hover:text-gray-700"
            onClick={onClose}
            disabled={isSubmitting}
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Title field with AI assist button */}
          <div className="flex flex-col gap-1">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">Title *</label>
              {enableAiAssist && aiInput && (
                <button
                  type="button"
                  onClick={handleAiSuggest}
                  disabled={isAiLoading || isSubmitting}
                  className="text-xs px-2 py-1 bg-dizzaroo-deep-blue text-white rounded-lg hover:bg-dizzaroo-blue-green disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center gap-1"
                >
                  {isAiLoading ? (
                    <>
                      <span className="animate-spin">🤖</span>
                      <span>AI Generating...</span>
                    </>
                  ) : (
                    <>
                      <span>🤖</span>
                      <span>AI Suggest</span>
                    </>
                  )}
                </button>
              )}
            </div>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              placeholder="Task title"
              className="px-3 py-2 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue"
              disabled={isSubmitting}
            />
          </div>

          {/* Description field */}
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-gray-700">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Task description..."
              rows={4}
              className="px-3 py-2 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue resize-y"
              disabled={isSubmitting}
            />
          </div>

          {/* AI Error Message */}
          {aiError && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-sm">
              <p className="font-semibold mb-1">AI Suggestion Error</p>
              <p>{aiError}</p>
            </div>
          )}

          {/* Status and Due Date */}
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Status</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as TaskStatus)}
                className="px-3 py-2 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue"
                disabled={isSubmitting}
              >
                <option value="open">Open</option>
                <option value="in-progress">In Progress</option>
                <option value="done">Done</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Due Date</label>
              <input
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue"
                disabled={isSubmitting}
              />
            </div>
          </div>

          {/* Links info (read-only) */}
          {defaultLinks && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-sm">
              <p className="font-semibold text-gray-700 mb-1">Linked to:</p>
              {defaultLinks.conversationId && (
                <p className="text-gray-600">Conversation: {defaultLinks.conversationId.substring(0, 8)}...</p>
              )}
              {defaultLinks.monitoringVisitId && (
                <p className="text-gray-600">Monitoring Visit: {defaultLinks.monitoringVisitId.substring(0, 8)}...</p>
              )}
              {defaultLinks.siteId && (
                <p className="text-gray-600">Site: {defaultLinks.siteId}</p>
              )}
            </div>
          )}

          {/* Form Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300 disabled:opacity-50 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !title.trim()}
              className="px-4 py-2 bg-dizzaroo-deep-blue text-white rounded-xl font-semibold hover:bg-dizzaroo-blue-green disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {isSubmitting ? 'Creating...' : 'Create Task'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default TaskFormModal

