import React from 'react'
import { Thread } from '../types'

interface ThreadListProps {
  threads: Thread[]
  onSelect: (id: string) => void
  selectedId?: string
}

const ThreadList: React.FC<ThreadListProps> = ({ threads, onSelect, selectedId }) => {
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'open': return '#28a745'
      case 'in_progress': return '#17a2b8'
      case 'resolved': return '#6c757d'
      case 'closed': return '#dc3545'
      default: return '#666'
    }
  }

  const getPriorityColor = (priority: string): string => {
    switch (priority) {
      case 'urgent': return '#dc3545'
      case 'high': return '#fd7e14'
      case 'medium': return '#ffc107'
      case 'low': return '#28a745'
      default: return '#666'
    }
  }

  const getTypeIcon = (type: string): string => {
    switch (type) {
      case 'issue': return '🐛'
      case 'patient': return '👤'
      case 'general': return '💬'
      default: return '💬'
    }
  }

  const formatTime = (dateString: string): string => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  if (threads.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500">
        <p className="mb-1">No threads found</p>
        <p className="text-xs">Create a new thread to get started</p>
      </div>
    )
  }

  return (
    <div className="p-2 space-y-2">
      {threads.map(thread => (
        <div
          key={thread.id}
          className={`p-3 rounded-lg border-2 cursor-pointer transition-all ${
            selectedId === thread.id 
              ? 'bg-dizzaroo-dna-gradient/10 border-dizzaroo-deep-blue shadow-md' 
              : 'bg-white border-gray-200 hover:border-dizzaroo-deep-blue/50 hover:shadow-sm'
          }`}
          onClick={() => onSelect(thread.id)}
        >
          <div className="flex justify-between items-start mb-2">
            <div className="flex items-center gap-1.5 flex-1 min-w-0">
              <span className="text-base">{getTypeIcon(thread.thread_type)}</span>
              <span className="font-bold text-xs text-gray-800 flex-1 truncate">{thread.title}</span>
            </div>
            <div className="text-xs text-gray-500 flex-shrink-0 ml-1">{formatTime(thread.updated_at)}</div>
          </div>

          <div className="flex gap-1.5 flex-wrap mb-2">
            <span 
              className="px-1.5 py-0.5 rounded-full text-white text-xs font-bold"
              style={{ backgroundColor: getStatusColor(thread.status) }}
            >
              {thread.status}
            </span>
            <span 
              className="px-1.5 py-0.5 rounded-full text-white text-xs font-bold"
              style={{ backgroundColor: getPriorityColor(thread.priority) }}
            >
              {thread.priority}
            </span>
            {thread.visibility_scope === 'site' ? (
              <span className="px-1.5 py-0.5 rounded-full bg-blue-500 text-white text-xs font-bold">
                🌐 Site
              </span>
            ) : (
              <span className="px-1.5 py-0.5 rounded-full bg-gray-600 text-white text-xs font-bold">
                🔐 Private
              </span>
            )}
            {thread.thread_type && (
              <span className="px-1.5 py-0.5 rounded-full bg-gray-200 text-gray-700 text-xs font-bold">
                {thread.thread_type}
              </span>
            )}
            {thread.related_study_id && (
              <span className="px-1.5 py-0.5 rounded-full bg-dizzaroo-deep-blue text-white text-xs font-bold">
                📋 {thread.related_study_id}
              </span>
            )}
          </div>

          {thread.description && (
            <div className="text-xs text-gray-600 mb-2 line-clamp-2">
              {thread.description.length > 60 
                ? `${thread.description.substring(0, 60)}...` 
                : thread.description}
            </div>
          )}

          <div className="flex justify-between items-center text-xs text-gray-500 pt-2 border-t border-gray-100">
            <div className="flex items-center gap-1.5">
              <span className="text-sm">👥</span>
              <span>{thread.participants?.length || 0} participants</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default ThreadList

