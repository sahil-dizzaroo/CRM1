import React, { useState, useRef, useEffect } from 'react'
import { api } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'

interface AskMeAnythingProps {
  apiBase: string
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

const AskMeAnything: React.FC<AskMeAnythingProps> = ({ apiBase }) => {
  const { token } = useAuth()
  const [mode, setMode] = useState<'select' | 'general' | 'document'>('select')
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [documentId, setDocumentId] = useState<string | null>(null)
  const [documentName, setDocumentName] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  // Load chat history from backend when component mounts
  useEffect(() => {
    if (token) {
      loadChatHistory()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, apiBase])

  const loadChatHistory = async () => {
    try {
      const response = await api.get('/chat/messages', {
        params: { limit: 100, offset: 0 }
      })

      const loadedMessages: ChatMessage[] = response.data.map((msg: any) => ({
        role: msg.role as 'user' | 'assistant',
        content: msg.content,
        timestamp: new Date(msg.created_at)
      }))

      setMessages(loadedMessages)

      if (loadedMessages.length > 0) {
        const msgWithDoc = response.data.find((m: any) => m.document_id)
        if (msgWithDoc && msgWithDoc.document_id) {
          setDocumentId(msgWithDoc.document_id)
          setMode('document')
          try {
            const docResponse = await api.get('/chat/documents')
            const doc = docResponse.data.find((d: any) => d.id === msgWithDoc.document_id)
            if (doc) {
              setDocumentName(doc.filename)
            }
          } catch (e) {
            console.error('Error loading document info:', e)
          }
        } else if (mode === 'select') {
          setMode('general')
        }
      } else if (mode === 'select') {
        setMode('select')
      }
    } catch (error) {
      console.error('Error loading chat history:', error)
      setMessages([])
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await api.post('/chat/upload-document', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      setDocumentId(response.data.document_id)
      setDocumentName(response.data.filename)
      setMode('document')
      setMessages([])
    } catch (error) {
      console.error('Error uploading document:', error)
      alert('Failed to upload document. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  const handleSendMessage = async () => {
    if (!question.trim() || loading) return

    const currentQuestion = question.trim()
    setQuestion('')
    setLoading(true)

    const userMessage: ChatMessage = {
      role: 'user',
      content: currentQuestion,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, userMessage])

    try {
      const formData = new FormData()
      formData.append('question', currentQuestion)
      formData.append('mode', mode)
      if (documentId) {
        formData.append('document_id', documentId)
      }

      const response = await api.post('/chat', formData)

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
      await loadChatHistory()
    } catch (error: any) {
      console.error('Error sending message:', error)
      setMessages(prev => prev.slice(0, -1))

      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: `Error: ${
          error.response?.data?.detail || error.message || 'Failed to get response'
        }`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleReset = async () => {
    setMode('select')
    setMessages([])
    setQuestion('')
    setDocumentId(null)
    setDocumentName(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }


  return (
    <div className="h-full w-full bg-white flex flex-col">
      {/* Header */}
      <div className="bg-gradient-to-r from-dizzaroo-deep-blue to-dizzaroo-blue-green text-white p-4 flex justify-between items-center flex-shrink-0">
        <h3 className="font-bold text-lg">💬 Ask Me Anything</h3>
        <button
          onClick={handleReset}
          className="text-white hover:text-gray-200 text-sm px-3 py-1 bg-white/20 rounded-lg transition"
        >
          Reset
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden flex flex-col bg-gray-50">
        {mode === 'select' ? (
          <div className="p-6 flex flex-col gap-4 h-full">
            <h4 className="font-semibold text-gray-800 mb-2">What would you like to do?</h4>
            <button
              onClick={() => setMode('general')}
              className="p-4 bg-dizzaroo-deep-blue/10 hover:bg-dizzaroo-deep-blue/20 rounded-xl border-2 border-dizzaroo-deep-blue/30 transition text-left"
            >
              <div className="font-semibold text-dizzaroo-deep-blue mb-1">💬 General Chat</div>
              <div className="text-sm text-gray-600">Ask questions about the CRM, how it works, features, etc.</div>
            </button>
            <button
              onClick={() => {
                fileInputRef.current?.click()
              }}
              className="p-4 bg-dizzaroo-soft-green/10 hover:bg-dizzaroo-soft-green/20 rounded-xl border-2 border-dizzaroo-soft-green/30 transition text-left"
            >
              <div className="font-semibold text-dizzaroo-soft-green mb-1">📄 Ask About Document</div>
              <div className="text-sm text-gray-600">Upload a document and ask questions about it</div>
            </button>
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileUpload}
              className="hidden"
              accept=".pdf,.doc,.docx,.txt"
            />
            {uploading && (
              <div className="text-center text-gray-500 text-sm">Uploading document...</div>
            )}
          </div>
        ) : (
          <>
            {/* Mode indicator */}
            <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-gray-700">
                  {mode === 'general' ? '💬 General Chat' : `📄 Document: ${documentName || 'Uploaded'}`}
                </span>
              </div>
              <button
                onClick={handleReset}
                className="text-xs text-gray-500 hover:text-gray-700"
              >
                Reset
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4" style={{ WebkitOverflowScrolling: 'touch' }}>
              {messages.length === 0 && (
                <div className="text-center text-gray-500 text-sm py-8">
                  {mode === 'general' 
                    ? 'Ask me anything about the CRM system, how it works, or its features!'
                    : 'Ask questions about the uploaded document!'}
                </div>
              )}
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-xl p-3 ${
                      msg.role === 'user'
                        ? 'bg-dizzaroo-deep-blue text-white'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 rounded-xl p-3">
                    <div className="flex gap-1">
                      <span className="animate-bounce">●</span>
                      <span className="animate-bounce" style={{ animationDelay: '0.1s' }}>●</span>
                      <span className="animate-bounce" style={{ animationDelay: '0.2s' }}>●</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-gray-200">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      handleSendMessage()
                    }
                  }}
                  placeholder="Type your question..."
                  className="flex-1 px-4 py-2 border-2 border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue focus:border-dizzaroo-deep-blue"
                  disabled={loading}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={loading || !question.trim()}
                  className="px-4 py-2 bg-dizzaroo-deep-blue text-white rounded-xl hover:bg-dizzaroo-blue-green transition disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
                >
                  Send
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default AskMeAnything

