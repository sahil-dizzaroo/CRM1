import React, { useState, useEffect, useRef } from 'react'
import { api } from '../lib//api'
import { useAuth } from '../contexts/AuthContext'
import MessageList from './MessageList'
import SendMessageForm from './SendMessageForm'
import CreateThreadFromConversation from './CreateThreadFromConversation'
import PrivilegedActions from './PrivilegedActions'
import AISummary from './AISummary'
import TaskFormModal from './TaskFormModal'
import ConversationRightSidebar from './ConversationRightSidebar'
import { Conversation, Message } from '../types'
import { AiTaskSuggestionInput } from '../services/aiService'


interface ConversationDetailProps {
  conversation: Conversation
  onRefresh: () => void
  apiBase: string
  currentUserId?: string
}

const ConversationDetail: React.FC<ConversationDetailProps> = ({
  conversation,
  onRefresh,
  apiBase,
  currentUserId = 'current_user'
}) => {
  const [messages, setMessages] = useState<Message[]>([])
  const [wsConnected, setWsConnected] = useState(false)
  const [selectionMode, setSelectionMode] = useState(false)
  const [selectedMessageIds, setSelectedMessageIds] = useState<string[]>([])
  const [showCreateThreadModal, setShowCreateThreadModal] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showTaskModal, setShowTaskModal] = useState(false)
  const [taskModalData, setTaskModalData] = useState<{
    message: Message | null
    recentMessages: Message[]
  } | null>(null)
  const [rightSidebarOpen, setRightSidebarOpen] = useState(true)
  const wsRef = useRef<WebSocket | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { user, token } = useAuth()

  // Fetch messages when conversation changes
  useEffect(() => {
    const fetchMessages = async () => {
      if (!conversation?.id) {
        setMessages([])
        return
      }

      try {
        setError(null)
        console.log('Fetching messages for conversation:', conversation.id)

        const response = await api.get(
          `${apiBase}/conversations/${conversation.id}?limit=200&offset=0`
        )
        console.log('Conversation response:', response.data)

        if (response.data && response.data.messages) {
          // Backend returns messages sorted by created_at DESCENDING (latest first)
          // We need to sort them ASCENDING (oldest first) for display
          const rawMessages = response.data.messages || []
          
          // Filter out any invalid messages
          const validMessages = rawMessages.filter((msg: any) => 
            msg && msg.id && msg.body !== undefined && msg.direction && msg.channel
          )
          
          const sortedMessages = [...validMessages].sort(
            (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
          )

          const uniqueMessages = sortedMessages.reduce((acc: Message[], msg: Message) => {
            if (!acc.find((m: Message) => m.id === msg.id)) {
              acc.push(msg)
            }
            return acc
          }, [] as Message[])

          setMessages(uniqueMessages)
        } else {
          setMessages([])
        }
      } catch (error: any) {
        console.error('Failed to fetch messages:', error)
        if (error.response?.status === 403) {
          setError('You do not have access to this conversation.')
          setMessages([])
        } else {
          setError(error.response?.data?.detail || 'Failed to load messages')
          setMessages([])
        }
      }
    }

    fetchMessages()
  }, [conversation?.id, apiBase, currentUserId, token])

  useEffect(() => {
    if (messagesEndRef.current && messages.length > 0) {
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
      }, 300)
    }
  }, [messages])

  // WebSocket connection
  useEffect(() => {
    if (!conversation || !conversation.id) {
      return
    }

    let reconnectTimeout: NodeJS.Timeout | null = null
    let isMounted = true
    let reconnectAttempts = 0
    const MAX_RECONNECT_ATTEMPTS = 5

    const connectWebSocket = () => {
      if (!isMounted || !conversation?.id) return

      if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
        console.warn('Max WebSocket reconnection attempts reached')
        return
      }

      reconnectAttempts++

      try {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          return
        }

        const wsToken = token || 'test'

        let wsUrl: string
        if (apiBase.startsWith('http://') || apiBase.startsWith('https://')) {
          // apiBase is absolute URL (production)
          wsUrl = apiBase.replace('http://', 'ws://').replace('https://', 'wss://') + '/ws'
        } else {
          // apiBase is relative path (local dev with Vite proxy)
          const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
          wsUrl = `${wsProtocol}//${window.location.host}${apiBase}/ws`
        }

        const ws = new WebSocket(`${wsUrl}?token=${encodeURIComponent(wsToken)}`)
        wsRef.current = ws

        ws.onopen = () => {
          if (!isMounted || !conversation?.id) {
            ws.close()
            return
          }
          console.log('WebSocket connected')
          setWsConnected(true)
          reconnectAttempts = 0

          try {
            ws.send(
              JSON.stringify({
                action: 'subscribe',
                conversation_id: conversation.id
              })
            )
            console.log('Sent subscribe for conversation:', conversation.id)
          } catch (e) {
            console.error('Error sending subscribe:', e)
            ws.close()
          }
        }

        ws.onmessage = (event) => {
          if (!isMounted) return
          try {
            const data = JSON.parse(event.data)
            if (data.status === 'subscribed') {
              console.log('✅ Subscribed to conversation:', data.conversation_id)
            } else if (data.error) {
              console.error('WebSocket error response:', data.error)
            } else if (data.type === 'new_message') {
              console.log('📨 Received new message via WebSocket:', data.message)
              // Check if this message is for the current conversation
              const eventConvId = data.conversation_id || (data.message && data.message.conversation_id)
              if (eventConvId && eventConvId !== conversation.id) {
                console.log(`⚠️ Ignoring message for different conversation: ${eventConvId} (current: ${conversation.id})`)
                return
              }
              if (data.message) {
                const newMessage: Message = {
                  id: data.message.id,
                  conversation_id: conversation.id,
                  body: data.message.body,
                  channel: data.message.channel,
                  direction: data.message.direction,
                  status: data.message.status || 'delivered', // Default to 'delivered' for inbound
                  author_id: data.message.author_id,
                  author_name: data.message.author_name,
                  created_at: data.message.created_at,
                  sent_at: data.message.sent_at,
                  delivered_at: data.message.delivered_at,
                  provider_message_id: data.message.provider_message_id
                }
                setMessages((prev) => {
                  if (prev.some((m) => m.id === newMessage.id)) {
                    return prev
                      .map((m) => (m.id === newMessage.id ? newMessage : m))
                      .sort(
                        (a, b) =>
                          new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
                      )
                  }

                  const tempMessageIndex = prev.findIndex(
                    (m) =>
                      m.id.startsWith('temp-') &&
                      m.body === newMessage.body &&
                      Math.abs(
                        new Date(m.created_at).getTime() -
                          new Date(newMessage.created_at).getTime()
                      ) < 5000
                  )

                  if (tempMessageIndex !== -1) {
                    const updated = [...prev]
                    updated[tempMessageIndex] = newMessage
                    return updated.sort(
                      (a, b) =>
                        new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
                    )
                  }

                  const updated = [...prev, newMessage].sort(
                    (a, b) =>
                      new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
                  )
                  console.log(`✅ Added new message to list. Total messages: ${updated.length}`)
                  return updated
                })

                // Refresh messages from API to ensure we have the latest
                setTimeout(() => {
                  if (onRefresh) {
                    console.log('Refreshing conversation after new message')
                    onRefresh()
                  }
                  messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
                }, 100)
              } else {
                console.warn('WebSocket new_message event missing message data')
              }
            } else if (data.type === 'status_update') {
              console.log('📨 Received status update:', data.message)
              if (data.message && data.message.id) {
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === data.message.id
                      ? {
                          ...msg,
                          status: data.message.status,
                          ...(data.message.sent_at && { sent_at: data.message.sent_at }),
                          ...(data.message.delivered_at && {
                            delivered_at: data.message.delivered_at
                          })
                        }
                      : msg
                  )
                )
              }
            }
          } catch (e) {
            console.error('Error parsing WebSocket message:', e)
          }
        }

        ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          if (isMounted) {
            setWsConnected(false)
          }
        }

        ws.onclose = (event) => {
          console.log('WebSocket closed:', event.code, event.reason || 'No reason')
          if (isMounted) {
            setWsConnected(false)
            if (
                isMounted &&
                conversation?.id &&
                ![1000, 1001].includes(event.code)
              ) {
                reconnectTimeout = setTimeout(connectWebSocket, 3000)
              }

          }
        }
      } catch (error) {
        console.error('Failed to create WebSocket:', error)
        if (isMounted) {
          setWsConnected(false)
          reconnectTimeout = setTimeout(() => {
            if (isMounted && conversation?.id) {
              connectWebSocket()
            }
          }, 3000)
        }
      }
    }

    const connectTimeout = setTimeout(() => {
      if (conversation?.id) {
        connectWebSocket()
      }
    }, 200)

    return () => {
      isMounted = false
      if (connectTimeout) clearTimeout(connectTimeout)
      if (reconnectTimeout) clearTimeout(reconnectTimeout)
    
    }
  }, [conversation?.id])

  const handleUploadFile = async (file: File) => {
    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await api.post(
      `${apiBase}/conversations/${conversation.id}/attachments`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
)


      return response.data
    } catch (error: any) {
      console.error('Failed to upload file:', error)
      throw new Error(error.response?.data?.detail || 'Failed to upload file')
    }
  }

  const [aiDrafts, setAiDrafts] = useState<{
    professional?: string
    short?: string
    detailed?: string
    summary?: string
    facts?: string[]
  } | null>(null)
  const [aiDraftVariant, setAiDraftVariant] = useState<
    'professional' | 'short' | 'detailed'
  >('professional')
  const [aiLoading, setAiLoading] = useState(false)

  useEffect(() => {
    setAiDrafts(null)
    setAiDraftVariant('professional')
    setAiLoading(false)
  }, [conversation?.id])

  const handleGenerateAiDraft = async () => {
    if (!conversation?.id) return
    try {
      setAiLoading(true)

      const resp = await api.post(
        `${apiBase}/ai/compose-reply`,
        { conversation_id: conversation.id }
      )


      const { drafts, summary, facts } = resp.data || {}
      setAiDrafts({
        professional: drafts?.professional || '',
        short: drafts?.short || '',
        detailed: drafts?.detailed || '',
        summary: summary || '',
        facts: facts || []
      })
      setAiDraftVariant('professional')
    } catch (e) {
      console.error('Failed to generate AI drafts', e)
      alert('Failed to generate AI drafts. Please try again.')
    } finally {
      setAiLoading(false)
    }
  }

  const handleApplyDraftToEditor = (draft: string) => {
    const textarea = document.querySelector<HTMLTextAreaElement>(
      'textarea[placeholder="Type your message here..."]'
    )
    if (textarea) {
      textarea.value = draft
      const event = new Event('input', { bubbles: true })
      textarea.dispatchEvent(event)
      textarea.focus()
    }
  }

  const handleSendMessage = async (messageData: { channel: string; body: string; files?: File[] }) => {
    try {
      // 1) AI pre-send check for email
      if (messageData.channel === 'email' && messageData.body.trim()) {
        try {

          const checkResp = await api.post(
            `${apiBase}/ai/check-message`,
            {
              conversation_id: conversation.id,
              draft_body: messageData.body,
              attachments: (messageData.files || []).map((f) => f.name)
            }
)

          const check = checkResp.data as {
            issues: { type: string; message: string }[]
            okToSend: boolean
          }
          if (check.issues && check.issues.length > 0 && !check.okToSend) {
            const messagesText = check.issues.map((i) => `- ${i.message}`).join('\n')
            const proceed = window.confirm(
              `AI noticed some possible issues before sending:\n\n${messagesText}\n\nPress OK to send anyway, or Cancel to edit the message.`
            )
            if (!proceed) {
              return
            }
          }
        } catch (e) {
          console.warn('AI pre-send check failed, sending anyway', e)
        }
      }

      // 2) Upload files (no message_id yet)
      if (messageData.files && messageData.files.length > 0) {
        for (const file of messageData.files) {
          await handleUploadFile(file)
        }
      }

      // 3) Optimistic UI
      const currentAuthorId = user?.user_id || ''
      const currentAuthorName = user?.name || user?.email || currentAuthorId

      const tempId = `temp-${Date.now()}`
      const optimisticMessage: Message = {
        id: tempId,
        conversation_id: conversation.id,
        body: messageData.body,
        channel: messageData.channel as 'sms' | 'whatsapp' | 'email',
        direction: 'outbound',
        status: 'queued',
        author_id: currentAuthorId,
        author_name: currentAuthorName,
        created_at: new Date().toISOString(),
        sent_at: undefined,
        delivered_at: undefined,
        provider_message_id: undefined
      }

      setMessages((prev) => {
        const updated = [...prev, optimisticMessage].sort(
          (a, b) =>
            new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
        )
        return updated
      })

      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
      }, 100)

      // 4) Send to server
      const response = await api.post(
        `${apiBase}/conversations/${conversation.id}/messages`,
        { channel: messageData.channel, body: messageData.body }
)


      // 5) Link files to real message
      if (messageData.files && messageData.files.length > 0 && response.data.id) {
        for (const file of messageData.files) {
          const formData = new FormData()
          formData.append('file', file)
          formData.append('message_id', response.data.id)

          await api.post(
          `${apiBase}/conversations/${conversation.id}/attachments`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          }
        )

        }
      }

      const realMessage: Message = {
        id: response.data.id,
        conversation_id: conversation.id,
        body: response.data.body,
        channel: response.data.channel,
        direction: response.data.direction,
        status: response.data.status,
        author_id: response.data.author_id || currentAuthorId,
        author_name: response.data.author_name || currentAuthorName,
        created_at: response.data.created_at,
        sent_at: response.data.sent_at,
        delivered_at: response.data.delivered_at,
        provider_message_id: response.data.provider_message_id
      }

      setMessages((prev) => {
        if (prev.some((m) => m.id === realMessage.id)) {
          return prev
            .filter((m) => m.id !== tempId)
            .sort(
              (a, b) =>
                new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
            )
        }

        const filtered = prev.filter((m) => m.id !== tempId)
        const updated = [...filtered, realMessage].sort(
          (a, b) =>
            new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
        )
        return updated
      })

      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
      }, 100)

      setTimeout(() => {
        onRefresh()
      }, 500)
    } catch (error) {
      setMessages((prev) => prev.filter((m) => !m.id.startsWith('temp-')))
      throw error
    }
  }

  const handleMessageSelect = (messageId: string, selected: boolean) => {
    if (selected) {
      setSelectedMessageIds((prev) => [...prev, messageId])
    } else {
      setSelectedMessageIds((prev) => prev.filter((id) => id !== messageId))
    }
  }

  const handleToggleSelectionMode = () => {
    setSelectionMode(!selectionMode)
    if (selectionMode) {
      setSelectedMessageIds([])
    }
  }

  const handleCreateThread = () => {
    if (selectedMessageIds.length > 0) {
      setShowCreateThreadModal(true)
    }
  }

  const handleThreadCreated = () => {
    setSelectionMode(false)
    setSelectedMessageIds([])
    onRefresh()
  }

  const handleCreateTaskFromMessage = (message: Message, recentMessages: Message[] = []) => {
    setTaskModalData({
      message,
      recentMessages
    })
    setShowTaskModal(true)
  }

  return (
    <div className="flex flex-col h-full bg-white" style={{ height: '100%', overflow: 'hidden' }}>
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-3 flex-shrink-0 shadow-sm sticky top-0 z-10">
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-4 flex-1 min-w-0">
            <div className="flex-1 min-w-0">
              <h2 className="text-base font-semibold text-gray-900 truncate">
                {conversation.subject || 'Conversation'}
              </h2>
              <div className="flex items-center gap-3 text-xs text-gray-500 mt-0.5">
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    wsConnected ? 'bg-green-400' : 'bg-red-400'
                  }`}
                ></span>
                <span>{wsConnected ? 'Connected' : 'Connecting...'}</span>
                {conversation.participant_phone && (
                  <span>📞 {conversation.participant_phone}</span>
                )}
                {/* Display all recipient emails */}
                {conversation.participant_emails && conversation.participant_emails.length > 0 ? (
                  <span>✉️ {conversation.participant_emails.join(', ')}</span>
                ) : conversation.participant_email && (
                  <span>✉️ {conversation.participant_email}</span>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2.5 flex-shrink-0">
            {!selectionMode ? (
              <>
                {currentUserId && (
                  <PrivilegedActions
                    conversation={conversation}
                    currentUserId={currentUserId}
                    apiBase={apiBase}
                    onUpdate={onRefresh}
                  />
                )}
                <AISummary
                  conversationId={conversation.id}
                  apiBase={apiBase}
                  type="conversation"
                />
                <button
                  className="px-3 py-1.5 bg-white border border-gray-300 text-gray-700 rounded-lg transition text-xs font-medium hover:bg-gray-50 hover:border-gray-400 flex items-center gap-1.5 whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed"
                  onClick={handleGenerateAiDraft}
                  disabled={aiLoading}
                  title="Let AI draft a reply for this email thread"
                >
                  <span className={aiLoading ? 'animate-spin' : ''}>
                    {aiLoading ? '⏳' : '🤖'}
                  </span>
                  <span>{aiLoading ? 'Generating...' : 'AI Draft'}</span>
                </button>
                <button
                  className="px-3 py-1.5 bg-white border border-gray-300 text-gray-700 rounded-lg transition text-xs font-medium hover:bg-gray-50 hover:border-gray-400 whitespace-nowrap"
                  onClick={handleToggleSelectionMode}
                  title="Select messages to create thread"
                >
                  📋 <span className="hidden sm:inline">Select</span>
                </button>
                <button
                  className="px-3 py-1.5 bg-white border border-gray-300 text-gray-700 rounded-lg transition text-xs font-medium hover:bg-gray-50 hover:border-gray-400 whitespace-nowrap"
                  onClick={onRefresh}
                  title="Refresh messages"
                >
                  🔄 <span className="hidden sm:inline">Refresh</span>
                </button>
              </>
            ) : (
              <>
                <button
                  className="px-3 py-1.5 bg-[#168AAD] text-white rounded-lg transition text-xs font-medium hover:bg-[#1E73BE] disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5 whitespace-nowrap"
                  onClick={handleCreateThread}
                  disabled={selectedMessageIds.length === 0}
                  title="Create thread from selected messages"
                >
                  ➕ <span>Create Thread ({selectedMessageIds.length})</span>
                </button>
                <button
                  className="px-3 py-1.5 bg-white border border-gray-300 text-gray-700 rounded-lg transition text-xs font-medium hover:bg-gray-50 whitespace-nowrap"
                  onClick={handleToggleSelectionMode}
                >
                  ✕ Cancel
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden min-h-0">
        <div
          className="flex-1 overflow-y-auto bg-gray-50 p-6 min-h-0"
          style={{ WebkitOverflowScrolling: 'touch' }}
        >
          <div className="w-full">
            {error && (
              <div className="mb-4 p-3 bg-red-50 border-2 border-red-200 rounded-lg">
                <p className="text-sm text-red-800 font-semibold">{error}</p>
              </div>
            )}
            {selectionMode && (
              <div className="mb-4 p-3 bg-blue-50 border-2 border-dizzaroo-deep-blue/20 rounded-xl">
                <p className="text-sm text-dizzaroo-deep-blue font-semibold">
                  Selection Mode: Click messages to select them. {selectedMessageIds.length}{' '}
                  message{selectedMessageIds.length !== 1 ? 's' : ''} selected.
                </p>
              </div>
            )}
            {messages.length > 0 && (
              <div className="mb-2 text-xs text-gray-500">
                Showing {messages.length} message{messages.length !== 1 ? 's' : ''}
              </div>
            )}
            <MessageList
              messages={messages}
              onMessageSelect={handleMessageSelect}
              selectedMessageIds={selectedMessageIds}
              selectionMode={selectionMode}
              apiBase={apiBase}
              conversationId={conversation.id}
              onCreateTask={handleCreateTaskFromMessage}
            />

            {/* AI drafts panel */}
            {aiDrafts && (aiDrafts.professional || aiDrafts.short || aiDrafts.detailed) && (
              <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="md:col-span-3 bg-white border border-dizzaroo-deep-blue/20 rounded-xl p-3 shadow-sm">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                      <span>🤖 AI Drafts</span>
                    </h3>
                    <div className="flex items-center gap-2">
                      <div className="inline-flex rounded-lg border border-gray-200 overflow-hidden text-xs">
                        <button
                          type="button"
                          className={`px-2 py-1 font-semibold ${
                            aiDraftVariant === 'professional'
                              ? 'bg-dizzaroo-deep-blue text-white'
                              : 'bg-white text-gray-700'
                          }`}
                          onClick={() => setAiDraftVariant('professional')}
                        >
                          Professional
                        </button>
                        <button
                          type="button"
                          className={`px-2 py-1 font-semibold border-l border-gray-200 ${
                            aiDraftVariant === 'short'
                              ? 'bg-dizzaroo-blue-green text-white'
                              : 'bg-white text-gray-700'
                          }`}
                          onClick={() => setAiDraftVariant('short')}
                        >
                          Short
                        </button>
                        <button
                          type="button"
                          className={`px-2 py-1 font-semibold border-l border-gray-200 ${
                            aiDraftVariant === 'detailed'
                              ? 'bg-dizzaroo-soft-green text-white'
                              : 'bg-white text-gray-700'
                          }`}
                          onClick={() => setAiDraftVariant('detailed')}
                        >
                          Detailed
                        </button>
                      </div>
                      <button
                        type="button"
                        className="ml-2 text-xs px-2 py-1 rounded-md bg-gray-100 text-gray-600 hover:bg-gray-200"
                        onClick={() => setAiDrafts(null)}
                        title="Hide AI drafts for this conversation"
                      >
                        ✕ Close
                      </button>
                    </div>
                  </div>
                  <div className="border-t border-gray-200 pt-2 text-sm text-gray-800 whitespace-pre-line">
                    {aiDraftVariant === 'professional' && aiDrafts.professional}
                    {aiDraftVariant === 'short' && aiDrafts.short}
                    {aiDraftVariant === 'detailed' && aiDrafts.detailed}
                  </div>
                  <div className="mt-2 flex justify-end">
                    <button
                      type="button"
                      className="px-3 py-1.5 bg-dizzaroo-deep-blue text-white rounded-lg text-xs font-semibold hover:bg-dizzaroo-blue-green"
                      onClick={() => {
                        const draft =
                          aiDraftVariant === 'professional'
                            ? aiDrafts.professional
                            : aiDraftVariant === 'short'
                            ? aiDrafts.short
                            : aiDrafts.detailed
                        handleApplyDraftToEditor(draft || '')
                      }}
                    >
                      Use this draft in editor
                    </button>
                  </div>
                </div>

                <div className="bg-white border border-dizzaroo-deep-blue/20 rounded-xl p-3 shadow-sm">
                  <h4 className="text-xs font-bold text-gray-700 mb-1">AI Summary</h4>
                  <p className="text-xs text-gray-800 mb-2">
                    {aiDrafts.summary || 'No summary generated yet.'}
                  </p>
                  {aiDrafts.facts && aiDrafts.facts.length > 0 && (
                    <>
                      <h5 className="text-xs font-semibold text-gray-700 mb-1">
                        Key Facts
                      </h5>
                      <ul className="list-disc list-inside space-y-0.5 text-xs text-gray-800">
                        {aiDrafts.facts.map((f, idx) => (
                          <li key={idx}>{f}</li>
                        ))}
                      </ul>
                    </>
                  )}
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        <ConversationRightSidebar
          conversation={conversation}
          messages={messages}
          apiBase={apiBase}
          conversationId={conversation.id}
          isOpen={rightSidebarOpen}
          onToggle={() => setRightSidebarOpen(!rightSidebarOpen)}
        />
      </div>

      {/* Send form */}
      <div className="bg-white border-t border-gray-200 shadow-lg flex-shrink-0">
        <div className="px-6 py-4 w-full">
          <SendMessageForm
            onSend={handleSendMessage}
            onUploadFile={handleUploadFile}
            conversationId={conversation.id}
            apiBase={apiBase}
          />
        </div>
      </div>

      {/* Create Thread Modal */}
      {showCreateThreadModal && (
        <CreateThreadFromConversation
          conversationId={conversation.id}
          messages={messages}
          selectedMessageIds={selectedMessageIds}
          onClose={() => setShowCreateThreadModal(false)}
          onSuccess={handleThreadCreated}
          apiBase={apiBase}
        />
      )}

      {/* Task Form Modal */}
      {showTaskModal && taskModalData && (
        <TaskFormModal
          isOpen={showTaskModal}
          onClose={() => {
            setShowTaskModal(false)
            setTaskModalData(null)
          }}
          onTaskCreated={(task) => {
            console.log('Task created:', task)
            setShowTaskModal(false)
            setTaskModalData(null)
          }}
          initialTitle={taskModalData.message ? truncate(taskModalData.message.body, 80) : ''}
          initialDescription={taskModalData.message?.body || ''}
          defaultLinks={{
            conversationId: conversation.id,
            messageId: taskModalData.message?.id,
            siteId: conversation.site_id
          }}
          enableAiAssist={true}
          aiInput={
            taskModalData.message
              ? {
                  conversationId: conversation.id,
                  messageId: taskModalData.message.id,
                  messageText: taskModalData.message.body,
                  recentMessages: taskModalData.recentMessages.map((msg) => ({
                    author: msg.author_name || msg.author_id || 'Unknown',
                    text: msg.body,
                    createdAt: msg.created_at
                  }))
                }
              : undefined
          }
          apiBase={apiBase}
        />
      )}
    </div>
  )
}

// Helper function to truncate text
function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength - 3) + '...'
}

export default ConversationDetail