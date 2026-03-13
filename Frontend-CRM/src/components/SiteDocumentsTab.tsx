import React, { useState, useEffect } from 'react'
import { api } from '../lib/api'
import { useStudySite } from '../contexts/StudySiteContext'
import { useAuth } from '../contexts/AuthContext'

interface SiteDocument {
  id: string
  site_id: string
  category: string
  file_name: string
  content_type: string
  size: number
  uploaded_by: string | null
  uploaded_at: string
  description: string | null
  metadata: Record<string, any>
  document_type?: string | null  // "sponsor" | "site"
  review_status?: string | null  // "pending" | "approved" | "rejected"
  tmf_filed?: string  // "true" | "false"
}

interface SiteDocumentsTabProps {
  apiBase?: string
}

type DocumentSection = 'sponsor' | 'site'

const SiteDocumentsTab: React.FC<SiteDocumentsTabProps> = ({ apiBase = '/api' }) => {
  const { selectedSiteId } = useStudySite()
  const { user } = useAuth()
  const [sponsorDocuments, setSponsorDocuments] = useState<SiteDocument[]>([])
  const [siteDocuments, setSiteDocuments] = useState<SiteDocument[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeSection, setActiveSection] = useState<DocumentSection>('sponsor')
  const [uploading, setUploading] = useState(false)
  const [processingDocId, setProcessingDocId] = useState<string | null>(null)

  const categories = [
    { value: 'investigator_cv', label: 'Investigator CV' },
    { value: 'signed_cda', label: 'Signed CDA' },
    { value: 'cta', label: 'CTA' },
    { value: 'irb_package', label: 'IRB Package' },
    { value: 'feasibility_questionnaire', label: 'Feasibility Questionnaire' },
    { value: 'feasibility_response', label: 'Feasibility Response' },
    { value: 'onsite_visit_report', label: 'On-site Visit Report' },
    { value: 'site_visibility_report', label: 'Site Visibility Report' },
    { value: 'other', label: 'Other' },
  ]

  useEffect(() => {
    if (selectedSiteId) {
      loadDocuments()
    } else {
      setSponsorDocuments([])
      setSiteDocuments([])
    }
  }, [selectedSiteId])

  const loadDocuments = async () => {
    if (!selectedSiteId) return

    setLoading(true)
    setError(null)
    try {
      // Load sponsor documents
      const sponsorResponse = await api.get<SiteDocument[]>(
        `${apiBase}/sites/${selectedSiteId}/documents?document_type=sponsor`
      )
      setSponsorDocuments(sponsorResponse.data)

      // Load site documents
      const siteResponse = await api.get<SiteDocument[]>(
        `${apiBase}/sites/${selectedSiteId}/documents?document_type=site`
      )
      setSiteDocuments(siteResponse.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load documents')
      console.error('Failed to load documents:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (file: File, category: string, documentType: DocumentSection, description?: string) => {
    if (!selectedSiteId) return

    setUploading(true)
    setError(null)
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('category', category)
      formData.append('document_type', documentType)
      if (description) formData.append('description', description)

      await api.post(`${apiBase}/sites/${selectedSiteId}/documents`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      await loadDocuments()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload document')
      console.error('Failed to upload document:', err)
    } finally {
      setUploading(false)
    }
  }

  const handleApprove = async (documentId: string) => {
    if (!selectedSiteId) return

    setProcessingDocId(documentId)
    setError(null)
    try {
      await api.post(`${apiBase}/sites/${selectedSiteId}/documents/${documentId}/approve`)
      await loadDocuments()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to approve document')
      console.error('Failed to approve document:', err)
    } finally {
      setProcessingDocId(null)
    }
  }

  const handleReject = async (documentId: string) => {
    if (!selectedSiteId) return

    setProcessingDocId(documentId)
    setError(null)
    try {
      await api.post(`${apiBase}/sites/${selectedSiteId}/documents/${documentId}/reject`)
      await loadDocuments()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reject document')
      console.error('Failed to reject document:', err)
    } finally {
      setProcessingDocId(null)
    }
  }

  const handleDownload = async (documentId: string, fileName: string) => {
    if (!selectedSiteId) return

    try {
      const response = await api.get(
        `${apiBase}/sites/${selectedSiteId}/documents/${documentId}/download`,
        {
          responseType: 'blob',
        }
      )

      // Create blob and download
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', fileName)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to download document')
      console.error('Failed to download document:', err)
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
  }

  const formatDate = (dateString: string): string => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return dateString
    }
  }

  const getReviewStatusBadge = (status: string | null | undefined) => {
    if (!status) return null
    
    const statusConfig = {
      pending: { label: 'Pending Review', className: 'bg-yellow-100 text-yellow-800' },
      approved: { label: 'Approved', className: 'bg-green-100 text-green-800' },
      rejected: { label: 'Rejected', className: 'bg-red-100 text-red-800' },
    }
    
    const config = statusConfig[status as keyof typeof statusConfig] || { label: status, className: 'bg-gray-100 text-gray-800' }
    
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${config.className}`}>
        {config.label}
      </span>
    )
  }

  if (!selectedSiteId) {
    return (
      <div className="flex items-center justify-center h-full p-8">
        <div className="text-center">
          <div className="text-6xl mb-4">📁</div>
          <h2 className="text-2xl font-semibold text-gray-800 mb-2">Site Documents</h2>
          <p className="text-gray-600">Please select a Study and Site to view documents.</p>
        </div>
      </div>
    )
  }

  const currentDocuments = activeSection === 'sponsor' ? sponsorDocuments : siteDocuments

  return (
    <div className="h-full flex flex-col bg-gray-50 overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6" style={{ minHeight: 0 }}>
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Site Documents</h1>
          <p className="text-gray-600">Site Master File - Documents persist regardless of site status changes.</p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800">
            {error}
          </div>
        )}

        {/* Section Tabs */}
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveSection('sponsor')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeSection === 'sponsor'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Sponsor Provided Documents
                {sponsorDocuments.length > 0 && (
                  <span className="ml-2 py-0.5 px-2 text-xs bg-gray-100 text-gray-600 rounded-full">
                    {sponsorDocuments.length}
                  </span>
                )}
              </button>
              <button
                onClick={() => setActiveSection('site')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeSection === 'site'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Site Uploaded Documents
                {siteDocuments.length > 0 && (
                  <span className="ml-2 py-0.5 px-2 text-xs bg-gray-100 text-gray-600 rounded-full">
                    {siteDocuments.length}
                  </span>
                )}
              </button>
            </nav>
          </div>
        </div>

        {/* Upload Section */}
        <div className="mb-6 p-4 bg-white border border-gray-200 rounded-lg">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Upload {activeSection === 'sponsor' ? 'Sponsor' : 'Site'} Document
          </h3>
          <DocumentUploadForm
            categories={categories}
            documentType={activeSection}
            onUpload={handleUpload}
            uploading={uploading}
          />
        </div>

        {/* Documents List */}
        {loading ? (
          <div className="text-center p-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="text-sm text-gray-600 mt-2">Loading documents...</p>
          </div>
        ) : currentDocuments.length === 0 ? (
          <div className="text-center p-8 bg-white border border-gray-200 rounded-lg">
            <div className="text-4xl mb-2">📄</div>
            <p className="text-gray-600">No {activeSection === 'sponsor' ? 'sponsor' : 'site'} documents found.</p>
            <p className="text-sm text-gray-500 mt-1">Upload your first document to get started.</p>
          </div>
        ) : (
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Document
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Size
                  </th>
                  {activeSection === 'site' && (
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Review Status
                    </th>
                  )}
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Uploaded
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {currentDocuments.map((doc) => (
                  <tr key={doc.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{doc.file_name}</div>
                        {doc.description && (
                          <div className="text-xs text-gray-500 mt-1">{doc.description}</div>
                        )}
                        {doc.tmf_filed === 'true' && (
                          <div className="text-xs text-green-600 mt-1">✓ Filed to TMF</div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                        {categories.find((c) => c.value === doc.category)?.label || doc.category}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatFileSize(doc.size)}
                    </td>
                    {activeSection === 'site' && (
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getReviewStatusBadge(doc.review_status)}
                      </td>
                    )}
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div>{formatDate(doc.uploaded_at)}</div>
                      {doc.uploaded_by && (
                        <div className="text-xs text-gray-400 mt-1">by {doc.uploaded_by}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleDownload(doc.id, doc.file_name)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          Download
                        </button>
                        {activeSection === 'site' && doc.review_status === 'pending' && (
                          <>
                            <span className="text-gray-300">|</span>
                            <button
                              onClick={() => handleApprove(doc.id)}
                              disabled={processingDocId === doc.id}
                              className="text-green-600 hover:text-green-900 disabled:text-gray-400 disabled:cursor-not-allowed"
                            >
                              {processingDocId === doc.id ? 'Processing...' : 'Approve & Send to TMF'}
                            </button>
                            <span className="text-gray-300">|</span>
                            <button
                              onClick={() => handleReject(doc.id)}
                              disabled={processingDocId === doc.id}
                              className="text-red-600 hover:text-red-900 disabled:text-gray-400 disabled:cursor-not-allowed"
                            >
                              {processingDocId === doc.id ? 'Processing...' : 'Reject'}
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

interface DocumentUploadFormProps {
  categories: Array<{ value: string; label: string }>
  documentType: DocumentSection
  onUpload: (file: File, category: string, documentType: DocumentSection, description?: string) => void
  uploading: boolean
}

const DocumentUploadForm: React.FC<DocumentUploadFormProps> = ({ categories, documentType, onUpload, uploading }) => {
  const [file, setFile] = useState<File | null>(null)
  const [category, setCategory] = useState<string>('other')
  const [description, setDescription] = useState<string>('')
  const fileInputRef = React.useRef<HTMLInputElement>(null)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (file) {
      onUpload(file, category, documentType, description || undefined)
      // Reset form
      setFile(null)
      setDescription('')
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">File</label>
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileSelect}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            required
          />
          {file && <p className="text-xs text-gray-600 mt-1">Selected: {file.name}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            required
          >
            {categories.map((cat) => (
              <option key={cat.value} value={cat.value}>
                {cat.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Description (Optional)</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          rows={2}
          placeholder="Add a description for this document..."
        />
      </div>

      <button
        type="submit"
        disabled={!file || uploading}
        className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
      >
        {uploading ? 'Uploading...' : 'Upload Document'}
      </button>
    </form>
  )
}

export default SiteDocumentsTab
