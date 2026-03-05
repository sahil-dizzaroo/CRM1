import React, { useState, useEffect } from 'react'
import { api } from '../lib/api'
import { Conversation, Message } from '../types'


interface ConversationListProps {
  conversations: Conversation[]
  onSelect: (id: string) => void
  selectedId?: string
  apiBase: string
  currentUserId?: string
}

const ConversationList: React.FC<ConversationListProps> = ({ conversations, onSelect, selectedId, apiBase, currentUserId = 'current_user' }) => {
  const [messageCounts, setMessageCounts] = useState<Record<string, number>>({})
  const [lastMessages, setLastMessages] = useState<Record<string, Message>>({})

      useEffect(() => {
      // Load last message for each conversation
      const loadLastMessages = async () => {
        const counts: Record<string, number> = {}
        const lastMsgs: Record<string, Message> = {}

        for (const conv of conversations) {
          try {
            const response = await api.get(
              `${apiBase}/conversations/${conv.id}?limit=1`
            )

            const messages = response.data.messages || []
            counts[conv.id] = messages.length
            if (messages.length > 0) {
              lastMsgs[conv.id] = messages[0]
            }
          } catch (err: any) {
            if (err.response?.status !== 403) {
              console.error(`Failed to load messages for ${conv.id}:`, err)
            }
          }
        }

        setMessageCounts(counts)
        setLastMessages(lastMsgs)
      }

      if (conversations.length > 0) {
        loadLastMessages()
      }
    }, [conversations, apiBase])


  const getChannelIcon = (channel: string): string => {
    switch (channel) {
      case 'sms': return '📱'
      case 'whatsapp': return '💬'
      case 'email': return '📧'
      default: return '💬'
    }
  }

  const getChannelColor = (channel: string): string => {
    switch (channel) {
      case 'sms': return '#1E73BE' // Dizzaroo Deep Blue
      case 'whatsapp': return '#25D366'
      case 'email': return '#168AAD' // Dizzaroo Blue Green
      default: return '#1E73BE' // Dizzaroo Deep Blue
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

  if (conversations.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500">
        <p className="mb-1">No conversations found</p>
        <p className="text-xs">Create a new conversation to get started</p>
      </div>
    )
  }

  return (
    <div className="p-2 space-y-1">
      {conversations.map(conv => {
        const lastMsg = lastMessages[conv.id]
        const msgCount = messageCounts[conv.id] || 0
        const isSelected = selectedId === conv.id
        
        return (
          <div
            key={conv.id}
            className={`group relative px-3 py-2.5 rounded-lg cursor-pointer transition-all ${
              isSelected 
                ? 'bg-[#168AAD]/10 border-l-3 border-[#168AAD] shadow-sm' 
                : 'hover:bg-gray-50'
            }`}
            style={isSelected ? { borderLeftWidth: '3px' } : {}}
            onClick={() => onSelect(conv.id)}
          >
            {/* Title Row */}
            <div className="flex items-start justify-between gap-2 mb-1.5">
              <div className="flex items-center gap-1.5 flex-1 min-w-0">
                {lastMsg && (
                  <span 
                    className="text-sm flex-shrink-0"
                    style={{ color: getChannelColor(lastMsg.channel) }}
                    title={lastMsg.channel.toUpperCase()}
                  >
                    {getChannelIcon(lastMsg.channel)}
                  </span>
                )}
                {conv.is_confidential === 'true' && (
                  <span className="text-xs flex-shrink-0" title="Confidential">🔐</span>
                )}
                {conv.is_restricted === 'true' && conv.is_confidential !== 'true' && (
                  <span className="text-xs flex-shrink-0" title="Restricted">🔒</span>
                )}
                {conv.subject && (
                  <h3 className={`font-semibold text-sm truncate flex-1 ${
                    isSelected ? 'text-[#168AAD]' : 'text-gray-900'
                  }`}>
                    {conv.subject}
                  </h3>
                )}
              </div>
              <div className="text-xs text-gray-400 flex-shrink-0">
                {formatTime(conv.updated_at)}
              </div>
            </div>
            
            {/* Preview Line */}
            {lastMsg && (
              <div className="text-xs text-gray-600 line-clamp-1 mb-1.5">
                {lastMsg.body.length > 60 ? `${lastMsg.body.substring(0, 60)}...` : lastMsg.body}
              </div>
            )}
            
            {/* Footer - Participant info and status */}
            <div className="flex items-center justify-between gap-2 mt-1.5">
              <div className="flex items-center gap-2 flex-1 min-w-0">
                {conv.participant_phone && (
                  <span className="text-xs text-gray-500 truncate">📞 {conv.participant_phone}</span>
                )}
                {conv.participant_email && !conv.participant_phone && (
                  <span className="text-xs text-gray-500 truncate">✉️ {conv.participant_email}</span>
                )}
              </div>
              {lastMsg && (
                <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                  lastMsg.status === 'queued' ? 'bg-yellow-400' :
                  lastMsg.status === 'sent' ? 'bg-blue-400' :
                  lastMsg.status === 'delivered' ? 'bg-green-400' :
                  'bg-red-400'
                }`} title={lastMsg.status}></span>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default ConversationList

