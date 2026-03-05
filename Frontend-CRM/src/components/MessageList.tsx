import React, { useEffect, useState } from 'react'
import { api } from '../lib/api'
import { Message, Attachment } from '../types'
import AttachmentDisplay from './AttachmentDisplay'
import { useIsMessageLikelyTask } from '../hooks/useIsMessageLikelyTask'

interface MessageListProps {
  messages: Message[]
  onMessageSelect?: (messageId: string, selected: boolean) => void
  selectedMessageIds?: string[]
  selectionMode?: boolean
  apiBase?: string
  conversationId?: string
  onCreateTask?: (message: Message, recentMessages?: Message[]) => void
}

const MessageList: React.FC<MessageListProps> = ({ 
  messages, 
  onMessageSelect, 
  selectedMessageIds = [], 
  selectionMode = false,
  apiBase = '',
  conversationId,
  onCreateTask
}) => {
  const [attachmentsMap, setAttachmentsMap] = useState<Record<string, Attachment[]>>({})
  const mentionEmailRegex = /@([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g

  const extractMentionedEmails = (message: Message): string[] => {
    const fromField = (message.mentioned_emails || [])
      .map((e) => String(e).trim().toLowerCase())
      .filter(Boolean)

    const fromBodyMatches = Array.from(message.body.matchAll(mentionEmailRegex))
      .map((m) => (m[1] || '').trim().toLowerCase())
      .filter(Boolean)

    const merged = [...fromField, ...fromBodyMatches]
    return Array.from(new Set(merged))
  }

  const getDisplayBody = (message: Message): string => {
    const cleaned = (message.body || '')
      .replace(mentionEmailRegex, '')
      .replace(/[ \t]{2,}/g, ' ')
      .replace(/\n{3,}/g, '\n\n')
      .trim()
    return cleaned || 'Message sent'
  }

  // Fetch attachments for all messages
  useEffect(() => {
    if (!conversationId) return

    const fetchAttachments = async () => {
      try {
        const response = await api.get(`/conversations/${conversationId}/attachments`)

        const attachments: Attachment[] = response.data || []

        // Group attachments by message_id
        const grouped: Record<string, Attachment[]> = {}
        attachments.forEach(att => {
          if (att.message_id) {
            if (!grouped[att.message_id]) {
              grouped[att.message_id] = []
            }
            grouped[att.message_id].push(att)
          }
        })

        setAttachmentsMap(grouped)
      } catch (error) {
        // Public notice board may have no attachment permission for some users; keep message UI usable.
        if ((error as any)?.response?.status !== 403) {
          console.error('Failed to fetch attachments:', error)
        }
      }
    }

    fetchAttachments()
  }, [conversationId, messages.length])

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
      case 'sms': return '#1E73BE'
      case 'whatsapp': return '#25D366'
      case 'email': return '#168AAD'
      default: return '#1E73BE'
    }
  }

  const formatTime = (dateString: string): string => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString)
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)

    if (date.toDateString() === today.toDateString()) {
      return 'Today'
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday'
    } else {
      return date.toLocaleDateString([], {
        month: 'long',
        day: 'numeric',
        year: 'numeric'
      })
    }
  }

  // Debug logging
  console.log('[MessageList] Rendering with', messages?.length || 0, 'messages')
  if (messages && messages.length > 0) {
    console.log('[MessageList] Sample messages:', messages.slice(0, 3).map(m => ({
      id: m.id,
      direction: m.direction,
      body: m.body?.substring(0, 50),
      created_at: m.created_at
    })))
  }

  if (!messages || messages.length === 0) {
    return (
      <div className="flex items-center justify-center h-full min-h-[500px]">
        <div className="text-center">
          <div className="text-8xl mb-6">💬</div>
          <p className="text-2xl font-bold text-gray-700 mb-2">
            No messages yet
          </p>
          <p className="text-base text-gray-500">
            Start the conversation by sending a message
          </p>
        </div>
      </div>
    )
  }

  // Sort messages by created_at (oldest first for display)
  const sortedMessages = [...messages].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  )

  // Group messages by date
  const groupedMessages: Record<string, Message[]> = {}
  sortedMessages.forEach(msg => {
    const dateKey = new Date(msg.created_at).toDateString()
    if (!groupedMessages[dateKey]) {
      groupedMessages[dateKey] = []
    }
    groupedMessages[dateKey].push(msg)
  })
  
  // Sort date groups (oldest first)
  const sortedDateKeys = Object.keys(groupedMessages).sort(
    (a, b) => new Date(a).getTime() - new Date(b).getTime()
  )

  // Determine latest message
  const latestMessage = messages.reduce<Message | null>((acc, msg) => {
    if (!acc) return msg
    return new Date(msg.created_at) > new Date(acc.created_at) ? msg : acc
  }, null)

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'queued': return 'bg-yellow-500'
      case 'sent': return 'bg-blue-500'
      case 'delivered': return 'bg-green-500'
      case 'failed': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const getUserColor = (authorId: string | undefined): string => {
    if (!authorId) return '#667eea'

    let hash = 0
    for (let i = 0; i < authorId.length; i++) {
      hash = authorId.charCodeAt(i) + ((hash << 5) - hash)
    }

    const colors = [
      '#667eea', '#f093fb', '#4facfe', '#43e97b', '#fa709a',
      '#f6a523', '#30cfd0', '#00cec9', '#ff6b6b', '#feca57',
      '#c471ed', '#12c2e9', '#ffd93d', '#4ecdc4', '#a1c4fd',
      '#ff8a80', '#84fab0', '#a8caba', '#ff6b9d', '#c44569',
      '#6c5ce7', '#00b894', '#e17055', '#0984e3', '#2d3436'
    ]

    return colors[Math.abs(hash) % colors.length]
  }

  const getDarkerColor = (color: string): string => {
    const hex = color.replace('#', '')
    if (hex.length !== 6) return color

    const r = Math.floor(parseInt(hex.substring(0, 2), 16) * 0.75)
    const g = Math.floor(parseInt(hex.substring(2, 4), 16) * 0.75)
    const b = Math.floor(parseInt(hex.substring(4, 6), 16) * 0.75)

    return `#${r.toString(16).padStart(2, '0')}${g
      .toString(16)
      .padStart(2, '0')}${b.toString(16).padStart(2, '0')}`
  }

  const getNoticeAttachment = (message: Message): { url: string; name: string; type: string } | null => {
    const md = message.metadata || {}
    const attachmentUrl = typeof md.attachment_url === 'string' ? md.attachment_url : ''
    if (!attachmentUrl) return null

    const attachmentName =
      (typeof md.attachment_name === 'string' && md.attachment_name.trim()) ||
      'Document'
    const attachmentType =
      (typeof md.attachment_type === 'string' && md.attachment_type.trim()) ||
      'document'

    let resolvedUrl = attachmentUrl
    if (!/^https?:\/\//i.test(attachmentUrl)) {
      if (attachmentUrl.startsWith('/api')) {
        resolvedUrl = attachmentUrl
      } else {
        resolvedUrl = `${apiBase}${attachmentUrl.startsWith('/') ? '' : '/'}${attachmentUrl}`
      }
    }

    return {
      url: resolvedUrl,
      name: attachmentName,
      type: attachmentType,
    }
  }

  const openNoticeAttachment = async (attachmentUrl: string) => {
    try {
      // If absolute URL, open directly.
      if (/^https?:\/\//i.test(attachmentUrl)) {
        window.open(attachmentUrl, '_blank', 'noopener,noreferrer')
        return
      }

      // Route through axios so dev/proxy/auth handling works for signed CDA links.
      let requestPath = attachmentUrl
      if (requestPath.startsWith('/api/')) {
        requestPath = requestPath.replace(/^\/api/, '')
      }
      if (!requestPath.startsWith('/')) {
        requestPath = `/${requestPath}`
      }

      const response = await api.get(requestPath, { responseType: 'blob' })
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const blobUrl = URL.createObjectURL(blob)
      window.open(blobUrl, '_blank', 'noopener,noreferrer')
      setTimeout(() => URL.revokeObjectURL(blobUrl), 30000)
    } catch (error) {
      console.error('Failed to open notice attachment:', error)
      // Last-resort fallback
      window.open(attachmentUrl, '_blank', 'noopener,noreferrer')
    }
  }


  return (
    <div className="space-y-6">
      {sortedDateKeys.map((dateKey) => {
        const dateMessages = groupedMessages[dateKey]
        return (
        <div key={dateKey} className="space-y-3">
          <div className="text-center py-2">
            <span className="px-4 py-1.5 bg-white border-2 border-gray-300 text-gray-600 text-xs font-bold uppercase tracking-wider rounded-full shadow-sm">
              {formatDate(dateMessages[0].created_at)}
            </span>
          </div>
          {dateMessages.map((message, idx) => {
            const isOutbound = message.direction === 'outbound'
            const showChannel = idx === 0 || dateMessages[idx - 1].channel !== message.channel || dateMessages[idx - 1].direction !== message.direction
            const noticeAttachment = getNoticeAttachment(message)
            
            const isSelected = selectedMessageIds.includes(message.id)
            
            return (
              <div 
                key={message.id} 
                className={`flex gap-3 ${isOutbound ? 'flex-row-reverse' : 'flex-row'} ${
                  selectionMode ? 'cursor-pointer' : ''
                } ${isSelected ? 'ring-2 ring-dizzaroo-deep-blue rounded-xl p-1' : ''}`}
                onClick={() => selectionMode && onMessageSelect && onMessageSelect(message.id, !isSelected)}
              >
                {/* Channel Icon / Avatar */}
                {showChannel && (
                  <div 
                    className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-lg shadow-md"
                    style={{ backgroundColor: isOutbound ? getUserColor(message.author_id) : getChannelColor(message.channel) }}
                  >
                    {isOutbound 
                      ? (message.author_name?.[0]?.toUpperCase() || message.author_id?.[0]?.toUpperCase() || '👤')
                      : getChannelIcon(message.channel)}
                  </div>
                )}
                {!showChannel && <div className="w-10 flex-shrink-0"></div>}
                
                {/* Message Bubble */}
                <div className={`flex-1 ${isOutbound ? 'items-end' : 'items-start'} flex flex-col`} style={{ maxWidth: '70%' }}>
                  {showChannel && (
                    <div className={`text-xs font-medium mb-1.5 px-1 ${isOutbound ? 'text-right' : 'text-left'} text-gray-600`}>
                      {isOutbound 
                        ? (message.author_name || message.author_id || 'You')
                        : `${getChannelIcon(message.channel)} ${message.author_name || message.author_id || message.channel.toUpperCase()}`}
                    </div>
                  )}
                  <div 
                    className={`rounded-2xl px-4 py-2.5 relative ${
                      isOutbound 
                        ? 'text-white rounded-br-md' 
                        : 'bg-white text-gray-900 rounded-bl-md shadow-sm'
                    }`}
                    style={isOutbound ? {
                      background: `linear-gradient(135deg, ${getUserColor(message.author_id)} 0%, ${getDarkerColor(getUserColor(message.author_id))} 100%)`
                    } : {}}
                  >
                    {/* Show author name inside message bubble if not shown above */}
                    {!showChannel && message.author_name && (
                      <div className={`text-xs font-medium mb-1 ${isOutbound ? 'text-white/90' : 'text-gray-600'}`}>
                        {message.author_name}
                      </div>
                    )}
                    {selectionMode && (
                      <div className="absolute top-2 right-2">
                        <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                          isSelected 
                            ? 'bg-[#168AAD] border-[#168AAD]' 
                            : 'border-gray-300 bg-white'
                        }`}>
                          {isSelected && <span className="text-white text-[10px]">✓</span>}
                        </div>
                      </div>
                    )}
                    <div className={`text-sm leading-relaxed whitespace-pre-wrap break-words ${
                      isOutbound ? 'text-white' : 'text-gray-900'
                    }`}>
                      {getDisplayBody(message)}
                    </div>
                    {extractMentionedEmails(message).length > 0 && (
                      <div className={`mt-1 text-xs ${isOutbound ? 'text-white/80' : 'text-gray-600'}`}>
                        Sent to: {extractMentionedEmails(message).join(', ')}
                      </div>
                    )}
                    {/* Display attachments */}
                    {attachmentsMap[message.id] && attachmentsMap[message.id].length > 0 && (
                      <div className="mt-2 space-y-2">
                        {attachmentsMap[message.id].map((att) => (
                          <AttachmentDisplay
                            key={att.id}
                            attachment={att}
                            apiBase={apiBase}
                            isOutbound={isOutbound}
                          />
                        ))}
                      </div>
                    )}
                    {/* Also check message.attachments if available from API */}
                    {message.attachments && message.attachments.length > 0 && (
                      <div className="mt-2 space-y-2">
                        {message.attachments.map((att) => (
                          <AttachmentDisplay
                            key={att.id}
                            attachment={att}
                            apiBase={apiBase}
                            isOutbound={isOutbound}
                          />
                        ))}
                      </div>
                    )}
                    {noticeAttachment && (
                      <div className="mt-2">
                        <button
                          type="button"
                          onClick={() => openNoticeAttachment(noticeAttachment.url)}
                          className={`inline-flex items-center gap-2 px-2 py-1 rounded border text-xs ${
                            isOutbound
                              ? 'border-white/40 text-white/95 hover:bg-white/10'
                              : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                          }`}
                        >
                          <span>📄</span>
                          <span>{noticeAttachment.name}</span>
                        </button>
                      </div>
                    )}
                    {/* Timestamp and Status - Subtle */}
                    <div className="flex items-center gap-2 mt-1.5 pt-1">
                      <span className={`text-[10px] ${isOutbound ? 'text-white/60' : 'text-gray-400'}`}>
                        {formatTime(message.created_at)}
                      </span>
                      <span className={`w-1 h-1 rounded-full ${
                        message.status === 'queued' ? 'bg-yellow-400' :
                        message.status === 'sent' ? 'bg-blue-400' :
                        message.status === 'delivered' ? 'bg-green-400' :
                        'bg-red-400'
                      }`} title={message.status}></span>
                    </div>
                  </div>
                  
                  {/* Task creation UI - only show when not in selection mode */}
                  {!selectionMode && onCreateTask && (
                    <div className={`mt-1.5 flex flex-col gap-1 ${isOutbound ? 'items-end' : 'items-start'}`}>
                      {/* Create Task Button - Smaller, less dominant */}
                      <button
                        onClick={() => {
                          // Get recent messages (3-5 before this one) for context
                          const currentIndex = dateMessages.findIndex(m => m.id === message.id)
                          const recentMessages = dateMessages.slice(Math.max(0, currentIndex - 5), currentIndex)
                          onCreateTask(message, recentMessages)
                        }}
                        className="px-2 py-0.5 text-[10px] text-[#168AAD] hover:text-[#1E73BE] hover:bg-[#168AAD]/5 rounded transition flex items-center gap-1"
                        title="Create task from this message"
                      >
                        <span>✓</span>
                        <span>Create Task</span>
                      </button>
                      
                      {/* AI Suggestion Banner */}
                      <MessageTaskSuggestion 
                        message={message}
                        onCreateTask={onCreateTask}
                        dateMessages={dateMessages}
                        isOutbound={isOutbound}
                      />
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
        )
      })}
    </div>
  )
}

// Component for AI task suggestion banner
const MessageTaskSuggestion: React.FC<{
  message: Message
  onCreateTask: (message: Message, recentMessages?: Message[]) => void
  dateMessages: Message[]
  isOutbound: boolean
}> = ({ message, onCreateTask, dateMessages, isOutbound }) => {
  const isLikelyTask = useIsMessageLikelyTask(message.body)
  
  const handleCreateTaskWithAI = () => {
    const currentIndex = dateMessages.findIndex(m => m.id === message.id)
    const recentMessages = dateMessages.slice(Math.max(0, currentIndex - 5), currentIndex)
    onCreateTask(message, recentMessages)
  }
  
  // Always show AI option, but highlight if it looks like a task
  return (
    <div className={`text-xs px-2 py-1 rounded-lg border ${
      isOutbound 
        ? isLikelyTask
        ? 'bg-blue-50 border-blue-300 text-blue-700'
        : 'bg-white border-gray-300 text-gray-700 shadow-sm'
        : isLikelyTask
        ? 'bg-blue-50 border-blue-300 text-blue-700'
        : 'bg-gray-50 border-gray-200 text-gray-600'
    }`}>
      <div className="flex items-center gap-1">
        <span>🤖</span>
        {isLikelyTask ? (
          <>
            <span>This message looks like an action item.</span>
            <button
              onClick={handleCreateTaskWithAI}
              className="underline font-semibold hover:no-underline"
            >
              Use AI to create task
            </button>
          </>
        ) : (
          <>
            <span>Create task with AI assistance</span>
            <button
              onClick={handleCreateTaskWithAI}
              className="underline font-semibold hover:no-underline"
            >
              Use AI
            </button>
          </>
        )}
      </div>
    </div>
  )
}

export default MessageList
