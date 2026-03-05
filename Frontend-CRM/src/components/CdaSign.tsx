import React, { useState, useEffect } from 'react'
import { api } from '../lib/api'

interface CdaSignData {
  token: string
  study_name: string
  site_name: string
  internal_signer_name: string
  internal_signer_title: string
  internal_signed_at: string
  cda_template: string
  cda_document_url?: string
}

const CdaSign: React.FC = () => {
  const getTokenFromUrl = () => {
    const params = new URLSearchParams(window.location.search)
    return params.get('token')
  }
  
  const [token] = useState<string | null>(getTokenFromUrl())
  
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [formData, setFormData] = useState<CdaSignData | null>(null)
  const [siteSignerName, setSiteSignerName] = useState('')
  const [siteSignerTitle, setSiteSignerTitle] = useState('')

  useEffect(() => {
    if (!token) {
      setError('Missing token parameter')
      setLoading(false)
      return
    }

    loadCdaData()
  }, [token])

  const loadCdaData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await api.get<CdaSignData>(`/cda/sign?token=${token}`)
      
      if (!response.data) {
        setError('No CDA data received')
        return
      }
      
      setFormData(response.data)
    } catch (err: any) {
      console.error('Error loading CDA data:', err)
      setError(err.response?.data?.detail || err.message || 'Failed to load CDA')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData || !token) return
    
    if (!siteSignerName.trim() || !siteSignerTitle.trim()) {
      setError('Please enter both name and title')
      return
    }

    try {
      setSubmitting(true)
      setError(null)
      
      const submitData = new FormData()
      submitData.append('token', token)
      submitData.append('site_signer_name', siteSignerName.trim())
      submitData.append('site_signer_title', siteSignerTitle.trim())
      
      await api.post('/cda/sign', submitData)
      setSuccess(true)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to sign CDA')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading CDA...</p>
        </div>
      </div>
    )
  }

  if (error && !formData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
          <div className="text-center">
            <div className="text-red-600 text-4xl mb-4">⚠️</div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Error</h2>
            <p className="text-gray-600">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
          <div className="text-center">
            <div className="text-green-600 text-4xl mb-4">✓</div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">CDA Signed Successfully</h2>
            <p className="text-gray-600">
              Thank you for signing the CDA. The document has been finalized and both parties have signed.
            </p>
          </div>
        </div>
      </div>
    )
  }

  if (!formData) {
    return null
  }

  // Resolve backend base URL from axios config (e.g. http://localhost:8000/api)
  const apiBase = (api.defaults.baseURL || '').replace(/\/+$/, '')
  const backendOrigin = apiBase.startsWith('http')
    ? apiBase.replace(/\/api\/?$/i, '')
    : window.location.origin

  const resolveDocumentUrl = (url: string) => {
    if (!url) return ''
    if (url.startsWith('http')) return url
    // Backend returns URLs like /api/cda/document/...
    if (url.startsWith('/api/')) return `${backendOrigin}${url}`
    if (url.startsWith('/')) return `${backendOrigin}/api${url}`
    return `${backendOrigin}/api/${url}`
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 overflow-y-auto">
      <div className="max-w-4xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Confidentiality Disclosure Agreement (CDA)</h1>
          <p className="text-gray-600">
            <strong>Study:</strong> {formData.study_name}
          </p>
          <p className="text-gray-600">
            <strong>Site:</strong> {formData.site_name}
          </p>
          <p className="text-gray-600">
            <strong>Template:</strong> {formData.cda_template === 'standard' ? 'Standard CDA Template' : 'Investigator CDA Template'}
          </p>

          <div className="mt-4 flex flex-wrap gap-3">
            <a
              href="#sign-section"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
            >
              Jump to Sign & Submit
            </a>
            {formData.cda_document_url && (
              <a
                href={resolveDocumentUrl(formData.cda_document_url)}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-4 py-2 bg-gray-100 text-gray-800 rounded-lg hover:bg-gray-200 text-sm font-medium"
              >
                Open Document in New Tab
              </a>
            )}
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* CDA Document Preview - Read-only inline preview */}
        {formData.cda_document_url ? (
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">CDA Document Preview</h2>
            <div className="border border-gray-300 rounded-lg overflow-hidden bg-gray-50">
              <iframe
                src={resolveDocumentUrl(formData.cda_document_url)}
                className="w-full"
                style={{ height: '70vh', border: 'none' }}
                title="CDA Document Preview"
                scrolling="yes"
                sandbox="allow-same-origin"
              />
            </div>
            <p className="text-xs text-gray-500 mt-2 italic">
              This is a read-only preview of the CDA document. Please review the document above before signing below.
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">CDA Document Preview</h2>
            <p className="text-sm text-gray-600">
              Document preview is not available yet. Please refresh or contact the sender.
            </p>
          </div>
        )}

        <div id="sign-section" className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Signatures</h2>
          
          {/* Internal Signer (Read-only) */}
          <div className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
            <h3 className="text-sm font-semibold text-gray-900 mb-2">Internal Signer (Dizzaroo)</h3>
            <p className="text-sm text-gray-700"><strong>Name:</strong> {formData.internal_signer_name}</p>
            <p className="text-sm text-gray-700"><strong>Title:</strong> {formData.internal_signer_title}</p>
            {formData.internal_signed_at && (
              <p className="text-xs text-gray-500 mt-2">
                Signed: {new Date(formData.internal_signed_at).toLocaleString()}
              </p>
            )}
          </div>

          {/* External Signer (Editable) */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h3 className="text-sm font-semibold text-blue-900 mb-4">External Signer ({formData.site_name})</h3>
              
              <div className="space-y-4">
                <div>
                  <label htmlFor="site_signer_name" className="block text-sm font-medium text-gray-700 mb-1">
                    Signer Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    id="site_signer_name"
                    value={siteSignerName}
                    onChange={(e) => setSiteSignerName(e.target.value)}
                    placeholder="Enter your name"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label htmlFor="site_signer_title" className="block text-sm font-medium text-gray-700 mb-1">
                    Signer Title <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    id="site_signer_title"
                    value={siteSignerTitle}
                    onChange={(e) => setSiteSignerTitle(e.target.value)}
                    placeholder="Enter your title"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <button
                type="submit"
                disabled={submitting || !siteSignerName.trim() || !siteSignerTitle.trim()}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                {submitting ? 'Signing...' : 'Sign & Submit CDA'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default CdaSign

