import React, { useState, useEffect } from 'react'
import { api } from '../lib/api'
import { Conversation, Message } from '../types'

interface ConversationRightSidebarProps {
  conversation: Conversation
  messages: Message[]
  apiBase: string
  conversationId: string
  isOpen: boolean
  onToggle: () => void
}

const ConversationRightSidebar: React.FC<ConversationRightSidebarProps> = ({
  conversation,
  messages,
  apiBase,
  conversationId,
  isOpen,
  onToggle
}) => {
  const [activeTab, setActiveTab] = useState<'summary' | 'changes' | 'tone' | 'tasks'>('summary')
  const [aiSummary, setAiSummary] = useState<string | null>(null)
  const [aiSummaryLoading, setAiSummaryLoading] = useState(false)
  const [aiSummaryError, setAiSummaryError] = useState<string | null>(null)

  // Fetch AI summary when summary tab is active and we don't have one
  useEffect(() => {
    if (activeTab === 'summary' && !aiSummary && !aiSummaryLoading && !aiSummaryError) {
      // Don't auto-fetch, let user trigger it via button
    }
  }, [activeTab, aiSummary, aiSummaryLoading, aiSummaryError])

  const fetchAISummary = async () => {
    setAiSummaryLoading(true)
    setAiSummaryError(null)
    try {
      const response = await api.get(
        `${apiBase}/conversations/${conversationId}/summary`
      )
      setAiSummary(response.data.summary)
    } catch (err: any) {
      setAiSummaryError(
        err.response?.data?.detail || err.message || 'Failed to generate summary'
      )
    } finally {
      setAiSummaryLoading(false)
    }
  }

  // Get latest message for "What changed"
  const latestMessage =
    messages.length > 0
      ? messages.reduce((latest, msg) =>
          new Date(msg.created_at) > new Date(latest.created_at) ? msg : latest
        )
      : null

  // Get all messages with tone
  const messagesWithTone = messages.filter(msg => msg.ai_tone)

  // Get all messages that might be tasks
  const taskMessages = messages.filter(
    msg =>
      msg.body.toLowerCase().includes('task') ||
      msg.body.toLowerCase().includes('todo') ||
      msg.body.toLowerCase().includes('action')
  )

  if (!isOpen) {
    return (
      <button
        onClick={onToggle}
        className="fixed right-0 top-1/2 -translate-y-1/2 bg-[#168AAD] text-white px-2 py-6 rounded-l-lg shadow-lg hover:bg-[#1E73BE] transition z-10 flex items-center justify-center"
        title="Open details panel"
      >
        <span className="text-xs font-semibold transform -rotate-90 whitespace-nowrap">
          Details
        </span>
      </button>
    )
  }


  return (
    <div className="w-80 bg-gray-50 border-l border-gray-200 flex flex-col h-full shadow-lg">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-800">Details</h3>
        <button
          onClick={onToggle}
          className="text-gray-400 hover:text-gray-600 transition"
          title="Close panel"
        >
          ✕
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 bg-white">
        {[
          { id: 'summary' as const, label: 'Summary', icon: '📋' },
          { id: 'changes' as const, label: 'Changes', icon: '🔄' },
          { id: 'tone' as const, label: 'Tone', icon: '💭' },
          { id: 'tasks' as const, label: 'Tasks', icon: '✓' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 px-2 py-2 text-xs font-medium transition ${
              activeTab === tab.id
                ? 'text-[#168AAD] border-b-2 border-[#168AAD] bg-[#168AAD]/5'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            }`}
          >
            <div className="flex flex-col items-center gap-0.5">
              <span>{tab.icon}</span>
              <span className="text-[10px]">{tab.label}</span>
            </div>
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'summary' && (
          <div className="space-y-3">
            <div>
              <h4 className="text-xs font-semibold text-gray-700 mb-2">Conversation Info</h4>
              <div className="space-y-2 text-xs text-gray-600">
                {conversation.subject && (
                  <div>
                    <span className="font-medium">Subject:</span> {conversation.subject}
                  </div>
                )}
                {conversation.participant_phone && (
                  <div>
                    <span className="font-medium">Phone:</span> {conversation.participant_phone}
                  </div>
                )}
                {conversation.participant_email && (
                  <div>
                    <span className="font-medium">Email:</span> {conversation.participant_email}
                  </div>
                )}
                <div>
                  <span className="font-medium">Messages:</span> {messages.length}
                </div>
                <div className="flex gap-2 mt-2">
                  {conversation.is_confidential === 'true' && (
                    <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded text-[10px] font-semibold">
                      🔐 Confidential
                    </span>
                  )}
                  {conversation.is_restricted === 'true' && (
                    <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded text-[10px] font-semibold">
                      🔒 Restricted
                    </span>
                  )}
                </div>
              </div>
            </div>
            {/* AI Summary */}
            <div className="pt-3 border-t border-gray-200">
              {!aiSummary && !aiSummaryLoading && !aiSummaryError && (
                <button
                  onClick={fetchAISummary}
                  className="w-full px-3 py-2 bg-[#168AAD] text-white rounded-lg text-xs font-medium hover:bg-[#1E73BE] transition"
                >
                  🤖 Generate AI Summary
                </button>
              )}
              {aiSummaryLoading && (
                <div className="text-center py-4">
                  <div className="animate-spin text-2xl mb-2">🤖</div>
                  <p className="text-xs text-gray-500">Generating summary...</p>
                </div>
              )}
              {aiSummaryError && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-xs">
                  <p className="font-semibold mb-1">Error</p>
                  <p>{aiSummaryError}</p>
                  <button
                    onClick={fetchAISummary}
                    className="mt-2 text-red-700 underline hover:no-underline"
                  >
                    Try again
                  </button>
                </div>
              )}
              {aiSummary && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <h5 className="text-xs font-semibold text-gray-700">AI Summary</h5>
                    <button
                      onClick={fetchAISummary}
                      className="text-xs text-blue-600 hover:text-blue-800"
                      title="Regenerate"
                    >
                      🔄
                    </button>
                  </div>
                  <p className="text-xs text-gray-700 leading-relaxed whitespace-pre-wrap">{aiSummary}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'changes' && (
          <div className="space-y-3">
            <h4 className="text-xs font-semibold text-gray-700 mb-2">What Changed</h4>
            {latestMessage && latestMessage.ai_delta_summary ? (
              <div className="text-xs text-gray-700 bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="font-medium mb-1">Latest Update:</p>
                <p>{latestMessage.ai_delta_summary}</p>
              </div>
            ) : (
              <p className="text-xs text-gray-500 italic">
                No "What changed" summary available for the latest message.
              </p>
            )}
          </div>
        )}

        {activeTab === 'tone' && (
          <div className="space-y-3">
            <h4 className="text-xs font-semibold text-gray-700 mb-2">Message Tone Analysis</h4>
            {messagesWithTone.length > 0 ? (
              <div className="space-y-2">
                {messagesWithTone.slice(0, 5).map(msg => (
                  <div key={msg.id} className="text-xs bg-gray-50 border border-gray-200 rounded-lg p-2">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-gray-700">{msg.ai_tone}</span>
                      <span className="text-gray-400 text-[10px]">
                        {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <p className="text-gray-600 line-clamp-2 text-[11px]">{msg.body.substring(0, 80)}...</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-gray-500 italic">
                No tone analysis available. Tone information appears when AI analyzes messages.
              </p>
            )}
          </div>
        )}

        {activeTab === 'tasks' && (
          <div className="space-y-3">
            <h4 className="text-xs font-semibold text-gray-700 mb-2">Potential Tasks</h4>
            {taskMessages.length > 0 ? (
              <div className="space-y-2">
                {taskMessages.slice(0, 5).map(msg => (
                  <div key={msg.id} className="text-xs bg-yellow-50 border border-yellow-200 rounded-lg p-2">
                    <p className="text-gray-700 line-clamp-2 text-[11px] mb-1">{msg.body.substring(0, 100)}...</p>
                    <span className="text-gray-400 text-[10px]">
                      {new Date(msg.created_at).toLocaleDateString()}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-gray-500 italic">
                No potential tasks identified. Create tasks from messages using the "Create Task" button.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default ConversationRightSidebar

