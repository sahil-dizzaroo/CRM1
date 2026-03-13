import React, { useState } from 'react'
import { api } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'

type CDAStatus = 'NOT_CREATED' | 'SENT' | 'SIGNED'

interface CDAWorkflowActionsProps {
  siteId: string
  apiBase?: string
  cdaStatus?: CDAStatus | string | null
  cdaMetadata?: {
    sent_at?: string
    sent_by?: string
    signed_at?: string
    signed_document?: string
  } | null
  onUpdate?: () => void
}

const CDAWorkflowActions: React.FC<CDAWorkflowActionsProps> = ({
  siteId,
  apiBase = '/api',
  cdaStatus,
  cdaMetadata,
  onUpdate,
}) => {
  const { user } = useAuth()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = React.useRef<HTMLInputElement>(null)

  const currentStatus: CDAStatus = (cdaStatus as CDAStatus) || 'NOT_CREATED'
  
  // Check if CDA was created but not yet sent (allows sending)
  const canSend = currentStatus === 'NOT_CREATED' && cdaMetadata?.created_at

  const formatDate = (dateString?: string) => {
    if (!dateString) return '–'
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return '–'
    }
  }

  const handleCreateCDA = async () => {
    setLoading(true)
    setError(null)

    try {
      // TODO: Create API endpoint POST /sites/{site_id}/cda/create
      // This endpoint should:
      // 1. Create CDA document record
      // 2. Update site status metadata with cda_status: 'NOT_CREATED'
      // 3. Return updated metadata
      await api.post(`${apiBase}/sites/${siteId}/cda/create`, {
        created_by: user?.user_id,
      })

      if (onUpdate) {
        onUpdate()
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to create CDA'
      setError(errorMsg)
      console.error('Failed to create CDA:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSendCDA = async () => {
    setLoading(true)
    setError(null)

    try {
      // TODO: Create API endpoint POST /sites/{site_id}/cda/send
      // This endpoint should:
      // 1. Update CDA status to 'SENT'
      // 2. Update site status metadata with cda_status: 'SENT', cda_sent_at, cda_sent_by
      // 3. Return updated metadata
      await api.post(`${apiBase}/sites/${siteId}/cda/send`, {
        sent_by: user?.user_id,
      })

      if (onUpdate) {
        onUpdate()
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to send CDA'
      setError(errorMsg)
      console.error('Failed to send CDA:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleFileSelect = () => {
    fileInputRef.current?.click()
  }

  const handleReceiveSignedCDA = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setLoading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('site_id', siteId)

      // TODO: Create API endpoint POST /sites/{site_id}/cda/receive-signed
      // This endpoint should:
      // 1. Save the signed CDA document
      // 2. Update CDA status to 'SIGNED'
      // 3. Update site status metadata with cda_status: 'SIGNED', cda_signed_at, cda_signed_document
      // 4. Return updated metadata
      await api.post(`${apiBase}/sites/${siteId}/cda/receive-signed`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      if (onUpdate) {
        onUpdate()
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to receive signed CDA'
      setError(errorMsg)
      console.error('Failed to receive signed CDA:', err)
    } finally {
      setLoading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  return (
    <div className="space-y-3">
      {/* Status Display */}
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-gray-600 uppercase">Status:</span>
        <span
          className={`px-2 py-1 rounded text-xs font-semibold ${
            currentStatus === 'SIGNED'
              ? 'bg-green-100 text-green-800'
              : currentStatus === 'SENT'
              ? 'bg-blue-100 text-blue-800'
              : 'bg-gray-100 text-gray-800'
          }`}
        >
          {currentStatus === 'NOT_CREATED' ? 'Not Created' : currentStatus}
        </span>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <div className="text-sm text-red-800">{error}</div>
        </div>
      )}

      {/* Actions based on status */}
      {currentStatus === 'NOT_CREATED' && !canSend && (
        <button
          onClick={handleCreateCDA}
          disabled={loading}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm font-medium transition"
        >
          {loading ? 'Creating...' : 'Create CDA'}
        </button>
      )}

      {/* After creation, allow sending */}
      {(currentStatus === 'NOT_CREATED' && canSend) && (
        <button
          onClick={handleSendCDA}
          disabled={loading}
          className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm font-medium transition"
        >
          {loading ? 'Sending...' : 'Send for Signature'}
        </button>
      )}

      {currentStatus === 'SENT' && (

      {currentStatus === 'SENT' && (
        <div className="space-y-2">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="text-xs text-blue-800">
              {cdaMetadata?.sent_at && (
                <div>
                  <span className="font-semibold">Sent:</span> {formatDate(cdaMetadata.sent_at)}
                </div>
              )}
              {cdaMetadata?.sent_by && (
                <div>
                  <span className="font-semibold">By:</span> {cdaMetadata.sent_by}
                </div>
              )}
            </div>
          </div>
          <button
            onClick={handleFileSelect}
            disabled={loading}
            className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm font-medium transition"
          >
            {loading ? 'Processing...' : 'Receive Signed CDA'}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.doc,.docx"
            onChange={handleReceiveSignedCDA}
            className="hidden"
          />
        </div>
      )}

      {currentStatus === 'SIGNED' && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3">
          <div className="text-sm font-semibold text-green-900 mb-1">✓ CDA Signed</div>
          <div className="text-xs text-green-800 space-y-1">
            {cdaMetadata?.signed_at && (
              <div>
                <span className="font-semibold">Signed:</span> {formatDate(cdaMetadata.signed_at)}
              </div>
            )}
            {cdaMetadata?.signed_document && (
              <div>
                <span className="font-semibold">Document:</span> {cdaMetadata.signed_document}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default CDAWorkflowActions

