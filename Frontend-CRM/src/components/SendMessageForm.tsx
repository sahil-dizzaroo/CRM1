import React, { useState, FormEvent, useRef } from 'react'

interface SendMessageFormProps {
  onSend: (data: { channel: string; body: string; files?: File[] }) => Promise<void>
  onUploadFile?: (file: File) => Promise<void>
  conversationId?: string
  threadId?: string
  apiBase?: string
}

const SendMessageForm: React.FC<SendMessageFormProps> = ({ onSend, onUploadFile, conversationId, threadId, apiBase }) => {
  const [channel] = useState<'email'>('email')
  const [body, setBody] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files)
      setFiles(prev => [...prev, ...selectedFiles])
    }
  }

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!body.trim() && files.length === 0) {
      setError('Message body or file is required')
      return
    }

    setLoading(true)
    setError(null)

    try {
      // Upload files first if any
      if (files.length > 0 && onUploadFile) {
        for (const file of files) {
          await onUploadFile(file)
        }
      }
      
      // Send message (even if empty, files might have been uploaded)
      await onSend({ channel, body: body.trim() || '📎 File attached', files })
      setBody('')
      setFiles([])
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      setError(null)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send message')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full">
      {error && (
        <div className="mb-2 bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-xs">
          {error}
        </div>
      )}
      
      {/* Files Preview */}
      {files.length > 0 && (
        <div className="mb-2 flex flex-wrap gap-2">
          {files.map((file, index) => (
            <div key={index} className="flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-lg px-2.5 py-1.5 text-xs">
              <span className="text-blue-700">📎 {file.name}</span>
              <button
                type="button"
                onClick={() => removeFile(index)}
                className="text-blue-700 hover:text-blue-900 font-bold text-sm"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input Container - Slack Style */}
      <div className="flex items-end gap-2 bg-white rounded-2xl border border-gray-300 shadow-sm px-3 py-2.5 focus-within:border-[#168AAD] focus-within:ring-1 focus-within:ring-[#168AAD] transition">
        {/* Email Channel Indicator */}
        <div className="flex-shrink-0">
          <div className="px-2.5 py-2 text-base font-medium text-gray-700" title="Email channel" style={{ fontSize: '18px' }}>
            📧
          </div>
        </div>

        {/* Message Input */}
        <div className="flex-1 min-w-0">
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Type a message..."
            className="w-full px-2 py-1.5 border-0 resize-none text-sm focus:outline-none text-gray-900 placeholder-gray-400"
            rows={1}
            disabled={loading}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSubmit(e as any)
              }
            }}
            style={{ maxHeight: '120px', overflowY: 'auto' }}
          />
        </div>

        {/* Action Buttons - Larger icons with labels */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {/* File Upload Button - Larger with tooltip */}
          <input
            ref={fileInputRef}
            type="file"
            multiple
            onChange={handleFileSelect}
            className="hidden"
            id="file-upload"
          />
          <label
            htmlFor="file-upload"
            className="px-2.5 py-2 text-gray-500 hover:text-gray-700 cursor-pointer transition rounded hover:bg-gray-100 flex items-center justify-center"
            title="Attach file"
            style={{ fontSize: '18px', minWidth: '20px', minHeight: '20px' }}
          >
            📎
          </label>

          {/* Send Button - Larger */}
          <button 
            type="submit" 
            className={`px-4 py-2 rounded-lg text-sm font-medium transition flex items-center justify-center ${
              loading || (!body.trim() && files.length === 0)
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-[#168AAD] text-white hover:bg-[#1E73BE]'
            }`}
            disabled={loading || (!body.trim() && files.length === 0)}
            title="Send message"
            style={{ minWidth: '40px', minHeight: '20px' }}
          >
            {loading ? <span className="animate-spin">⏳</span> : <span style={{ fontSize: '18px' }}>→</span>}
          </button>
        </div>
      </div>
    </form>
  )
}

export default SendMessageForm
