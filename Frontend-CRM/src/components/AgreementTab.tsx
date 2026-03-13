import React, { useState, useEffect, useRef } from 'react'
import { api } from '../lib/api'
import { useStudySite } from '../contexts/StudySiteContext'
import { useAuth } from '../contexts/AuthContext'
import OnlyOfficeEditor from './OnlyOfficeEditor'

// Component to display signed PDF with authentication
const SignedPDFViewer: React.FC<{
  agreementId: string
  signedDocumentId: string
  apiBase: string
}> = ({ agreementId, signedDocumentId, apiBase }) => {
  const [pdfBlobUrl, setPdfBlobUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let blobUrl: string | null = null
    let isMounted = true
    
    const loadPDF = async () => {
      try {
        setLoading(true)
        setError(null)
        
        // Fetch PDF with authentication via axios
        const response = await api.get(
          `${apiBase}/agreements/${agreementId}/signed-document/${signedDocumentId}`,
          { responseType: 'blob' }
        )
        
        if (!isMounted) return
        
        // Create blob URL
        const blob = new Blob([response.data], { type: 'application/pdf' })
        blobUrl = URL.createObjectURL(blob)
        setPdfBlobUrl(blobUrl)
      } catch (err: any) {
        if (!isMounted) return
        console.error('Failed to load signed PDF:', err)
        setError(err.response?.data?.detail || 'Failed to load signed PDF')
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }

    loadPDF()

    // Cleanup blob URL on unmount or when dependencies change
    return () => {
      isMounted = false
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl)
      }
      // Also cleanup if state has a blob URL
      setPdfBlobUrl((prev) => {
        if (prev) {
          URL.revokeObjectURL(prev)
        }
        return null
      })
    }
  }, [agreementId, signedDocumentId, apiBase])

  if (loading) {
    return (
      <div className="w-full h-full flex items-center justify-center p-8">
        <p className="text-gray-600">Loading signed document...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="w-full h-full flex items-center justify-center p-8">
        <div className="text-center">
          <p className="text-red-600 font-medium mb-2">Failed to load signed PDF</p>
          <p className="text-sm text-gray-600">{error}</p>
        </div>
      </div>
    )
  }

  if (!pdfBlobUrl) {
    return (
      <div className="w-full h-full flex items-center justify-center p-8">
        <p className="text-gray-600">No PDF available</p>
      </div>
    )
  }

  return (
    <div className="w-full h-full flex flex-col">
      <div className="border-b border-gray-200 p-2 bg-green-50 text-xs text-green-800 text-center">
        ✓ Signed Document - Viewing final executed version with signatures
      </div>
      <div className="flex-1 overflow-hidden">
        <iframe
          src={pdfBlobUrl}
          className="w-full h-full border-0"
          title="Signed Agreement PDF"
          style={{ minHeight: '600px' }}
        />
      </div>
      <div className="border-t border-gray-200 p-2 bg-gray-50 text-xs text-gray-600 text-center">
        Read-only mode - This is the final signed document with Zoho signatures
      </div>
    </div>
  )
}

interface AgreementVersion {
  id: string
  agreement_id: string
  version_number: number
  file_path: string | null
  document_html: string | null
  uploaded_by: string | null
  uploaded_at: string
  is_signed_version: string
  is_external_visible: string
}

interface AgreementComment {
  id: string
  agreement_id: string
  version_id: string | null
  comment_type: string
  content: string
  created_by: string | null
  created_at: string
}

interface AgreementDocument {
  id: string
  agreement_id: string
  version_number: number
  document_content: any // TipTap JSON (legacy)
  document_file_path?: string | null // Path to DOCX file
  created_from_template_id: string | null
  created_by: string | null
  created_at: string
  is_signed_version: string
}

interface Agreement {
  id: string
  site_id: string
  title: string
  status: string
  created_by: string | null
  created_at: string
  updated_at: string
  current_version_id: string | null
  is_legacy: string
  versions: AgreementVersion[]
  documents: AgreementDocument[]
  comments: AgreementComment[]
  can_upload_new_version: boolean
  can_edit: boolean
  can_comment: boolean
  can_save: boolean
  can_move_status: boolean
  is_locked: boolean
  zoho_request_id?: string | null
  signature_status?: string | null
  signed_documents?: Array<{
    id: string
    file_path: string
    signed_at: string | null
    downloaded_from_zoho_at: string
  }>
}

interface AgreementTabProps {
  apiBase?: string
}

const AgreementTab: React.FC<AgreementTabProps> = ({ apiBase = '/api' }) => {
  const { selectedSiteId, selectedStudyId, studies } = useStudySite()
  const { user } = useAuth()
  const [agreement, setAgreement] = useState<Agreement | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [newAgreementTitle, setNewAgreementTitle] = useState('')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('')
  const [availableTemplates, setAvailableTemplates] = useState<any[]>([])
  const [nextStatus, setNextStatus] = useState<string | null>(null)
  const [showStatusConfirmModal, setShowStatusConfirmModal] = useState(false)
  const [changingStatus, setChangingStatus] = useState(false)
  // REMOVED: Reset workflow state - not part of production workflow
  // const [resetting, setResetting] = useState(false)
  // const [showResetConfirmModal, setShowResetConfirmModal] = useState(false)
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null)
  const [savingDocument, setSavingDocument] = useState(false)
  const [hasUnsavedEdits, setHasUnsavedEdits] = useState(false)
  const agreementRef = useRef<Agreement | null>(null)
  const [sendingForSignature, setSendingForSignature] = useState(false)
  const [showSignatureModal, setShowSignatureModal] = useState(false)
  const [siteSignerEmail, setSiteSignerEmail] = useState('')
  const [sponsorSignerEmail, setSponsorSignerEmail] = useState('')
  const [ccEmails, setCcEmails] = useState('')
  const [siteProfile, setSiteProfile] = useState<any>(null)
  const [syncingZohoStatus, setSyncingZohoStatus] = useState(false)
  const [resettingWorkflow, setResettingWorkflow] = useState(false)

  useEffect(() => {
    if (selectedSiteId) {
      loadAgreement()
    } else {
      setAgreement(null)
      setNextStatus(null)
    }
  }, [selectedSiteId])

  useEffect(() => {
    if (agreement) {
      loadNextStatus()
      
      // Validate selectedVersion: if it doesn't exist in current documents, reset it
      if (selectedVersion !== null) {
        const hasVersion = agreement.documents?.some(d => d.version_number === selectedVersion)
        if (!hasVersion) {
          console.log(`Selected version ${selectedVersion} no longer exists, resetting to null`)
          setSelectedVersion(null)
        }
      }
      
      // Load templates if agreement has no documents (after reset)
      if ((!agreement.documents || agreement.documents.length === 0) && selectedStudyId) {
        loadTemplates()
      }

      // Update ref with current agreement
      agreementRef.current = agreement

      // Start continuous polling when agreement has documents (editor is open)
      // Polling only updates UI, does NOT remount editor
      if (agreement.documents && agreement.documents.length > 0) {
        const interval = setInterval(async () => {
          // Get current state from ref (always up-to-date)
          const currentAgreement = agreementRef.current
          if (!currentAgreement || !currentAgreement.documents) return

          const currentDocs = currentAgreement.documents
          const currentVersionCount = currentDocs.length
          const currentLatestVersion = currentDocs.length > 0
            ? Math.max(...currentDocs.map(d => d.version_number))
            : 0

          const updated = await refreshAgreementOnce()
          if (updated && updated.documents) {
            // Update ref immediately
            agreementRef.current = updated

            const newVersionCount = updated.documents.length
            const newLatestVersion = updated.documents.length > 0
              ? Math.max(...updated.documents.map(d => d.version_number))
              : 0

            // If new version detected, update UI immediately (but don't remount editor)
            if (newVersionCount > currentVersionCount || newLatestVersion > currentLatestVersion) {
              console.log(`[Auto-Poll] ✅ New version detected: ${newLatestVersion} (was ${currentLatestVersion})`)
              setSelectedVersion(null) // Reset to show latest
              // DO NOT remount editor - just update agreement state
            }
          }
        }, 2000) // Poll every 2 seconds

        // Cleanup
        return () => {
          clearInterval(interval)
        }
      }
    } else {
      setNextStatus(null)
      setSelectedVersion(null)
      agreementRef.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agreement, selectedStudyId])

  // Load templates when study is selected
  useEffect(() => {
    if (selectedStudyId) {
      loadTemplates()
    } else {
      setAvailableTemplates([])
    }
  }, [selectedStudyId])

  const loadTemplates = async () => {
    // Try to get study ID from context first
    let studyIdToUse = selectedStudyId
    
    // If not available, try to get from site
    if (!studyIdToUse && selectedSiteId && studies.length > 0) {
      try {
        const siteResponse = await api.get(`${apiBase}/sites/${selectedSiteId}`)
        const site = siteResponse.data
        if (site && site.study_id) {
          // Find study by study_id string
          const study = studies.find(s => s.study_id === site.study_id)
          if (study) {
            studyIdToUse = study.id // Use UUID
            console.log('Found study ID from site:', studyIdToUse)
          }
        }
      } catch (err) {
        console.warn('Could not get study_id from site:', err)
      }
    }
    
    if (!studyIdToUse) {
      console.warn('No study ID available for loading templates. selectedStudyId:', selectedStudyId, 'selectedSiteId:', selectedSiteId)
      setAvailableTemplates([])
      return
    }
    
    try {
      console.log('Loading templates for study:', studyIdToUse)
      const response = await api.get(`${apiBase}/studies/${studyIdToUse}/templates?active_only=true`)
      console.log('Templates loaded:', response.data?.length || 0, 'templates')
      setAvailableTemplates(response.data || [])
    } catch (err: any) {
      console.error('Failed to load templates:', err)
      console.error('Error details:', {
        status: err.response?.status,
        data: err.response?.data,
        studyId: studyIdToUse,
        url: `${apiBase}/studies/${studyIdToUse}/templates?active_only=true`
      })
      setAvailableTemplates([])
    }
  }

  // Lightweight refresh used after ONLYOFFICE save – does NOT touch global loading flag
  const refreshAgreementOnce = async (): Promise<Agreement | null> => {
    if (!selectedSiteId || !selectedStudyId) return null
    try {
      const response = await api.get<Agreement[]>(
        `${apiBase}/sites/${selectedSiteId}/agreements?study_id=${selectedStudyId}`
      )
      if (response.data && response.data.length > 0) {
        const agreementData = response.data[0]
        // Update ref
        agreementRef.current = agreementData
        // Force React to detect the change by creating a new object reference
        setAgreement({ ...agreementData })
        return agreementData
      } else {
        setAgreement(null)
        return null
      }
    } catch (err: any) {
      console.error('Failed to refresh agreement after save:', err)
      return null
    }
  }

  const loadAgreement = async (skipLoadingState: boolean = false): Promise<Agreement | null> => {
    if (!selectedSiteId || !selectedStudyId) return null

    if (!skipLoadingState) {
      setLoading(true)
    }
    setError(null)
    try {
      // For Phase 1, we'll assume one agreement per site
      // In future phases, we may need to list agreements and select one
      // For now, we'll try to get the first agreement or create one
      const response = await api.get<Agreement[]>(
        `${apiBase}/sites/${selectedSiteId}/agreements?study_id=${selectedStudyId}`
      )
      if (response.data && response.data.length > 0) {
        const agreementData = response.data[0]
        
        // 🔍 DEBUG: Inspect agreement data
        console.log('=== AGREEMENT DEBUG INFO ===')
        console.log('Agreement ID:', agreementData.id)
        console.log('Status:', agreementData.status)
        console.log('can_edit:', agreementData.can_edit, '(type:', typeof agreementData.can_edit, ')')
        console.log('can_comment:', agreementData.can_comment)
        console.log('is_legacy:', agreementData.is_legacy, '(type:', typeof agreementData.is_legacy, ')')
        console.log('AgreementDocument count:', agreementData.documents?.length || 0)
        console.log('AgreementVersion count:', agreementData.versions?.length || 0)
        console.log('Has documents:', !!agreementData.documents && agreementData.documents.length > 0)
        console.log('Has versions:', !!agreementData.versions && agreementData.versions.length > 0)
        if (agreementData.documents && agreementData.documents.length > 0) {
          console.log('Documents:', agreementData.documents.map(d => ({
            id: d.id,
            version_number: d.version_number,
            has_content: !!d.document_content
          })))
        }
        if (agreementData.versions && agreementData.versions.length > 0) {
          console.log('Versions:', agreementData.versions.map(v => ({
            id: v.id,
            version_number: v.version_number,
            has_file: !!v.file_path
          })))
        }
        console.log('=== END DEBUG INFO ===')
        
        // Use the first agreement from the list (which already includes versions and comments)
        // Force React re-render by creating new object
        setAgreement({ ...agreementData })
        return agreementData
      } else {
        // No agreements exist yet
        setAgreement(null)
        return null
      }
    } catch (err: any) {
      // If no agreements exist, that's okay for Phase 1
      if (err.response?.status !== 404) {
        setError(err.response?.data?.detail || 'Failed to load agreement')
        console.error('Failed to load agreement:', err)
      } else {
        setAgreement(null)
      }
      return null
    } finally {
      if (!skipLoadingState) {
        setLoading(false)
      }
    }
  }

  const handleCreateAgreement = async () => {
    if (!selectedSiteId || !selectedStudyId || !newAgreementTitle.trim() || !selectedTemplateId) {
      setError('Please provide agreement title and select a template')
      return
    }

    setCreating(true)
    setError(null)
    try {
      await api.post<Agreement>(
        `${apiBase}/sites/${selectedSiteId}/agreements?study_id=${selectedStudyId}`,
        {
          site_id: selectedSiteId,
          title: newAgreementTitle,
          status: 'DRAFT',
          template_id: selectedTemplateId, // REQUIRED: Template selection for new agreements
        }
      )
      setNewAgreementTitle('')
      setSelectedTemplateId('')
      setShowCreateForm(false)
      
      // Reload agreement to get full details with relationships
      await loadAgreement()
      
      // 🔍 DEBUG: Verify newly created agreement
      console.log('=== NEW AGREEMENT CREATED - VERIFICATION ===')
      const verifyResponse = await api.get<Agreement[]>(
        `${apiBase}/sites/${selectedSiteId}/agreements?study_id=${selectedStudyId}`
      )
      if (verifyResponse.data && verifyResponse.data.length > 0) {
        const newAgreement = verifyResponse.data[0]
        console.log('✅ Agreement ID:', newAgreement.id)
        console.log('✅ is_legacy:', newAgreement.is_legacy, '(should be "false")')
        console.log('✅ Documents count:', newAgreement.documents?.length || 0, '(should be >= 1)')
        console.log('✅ Versions count:', newAgreement.versions?.length || 0, '(should be 0 for new agreements)')
        if (newAgreement.documents && newAgreement.documents.length > 0) {
          console.log('✅ First document version:', newAgreement.documents[0].version_number, '(should be 1)')
          console.log('✅ First document has content:', !!newAgreement.documents[0].document_content)
        }
        console.log('=== END VERIFICATION ===')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create agreement')
      console.error('Failed to create agreement:', err)
    } finally {
      setCreating(false)
    }
  }

  // Create document from template for existing agreement (after reset)
  const handleCreateDocumentFromTemplate = async () => {
    if (!agreement || !selectedTemplateId) {
      setError('Please select a template')
      return
    }

    setCreating(true)
    setError(null)
    try {
      const formData = new FormData()
      formData.append('template_id', selectedTemplateId)
      
      await api.post(`${apiBase}/agreements/${agreement.id}/create-from-template`, formData)
      
      setSelectedTemplateId('')
      
      // Reload agreement to get updated documents
      await loadAgreement()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create document from template')
      console.error('Failed to create document from template:', err)
    } finally {
      setCreating(false)
    }
  }

  // DISABLED: Manual file upload temporarily disabled during workflow restructuring
  const handleUploadVersion = async () => {
    // ⚠️ DISABLED DURING WORKFLOW RESTRUCTURING
    // Manual file upload is temporarily disabled.
    // For new agreements, use template-based creation and the document editor.
    alert('Manual file upload is temporarily disabled during workflow restructuring. Use template-based creation and the document editor instead.')
    return
    if (!agreement || !selectedFile) return

    setUploading(true)
    setError(null)
    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      await api.post(`${apiBase}/agreements/${agreement.id}/versions`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      
      // Reload agreement to get updated versions
      await loadAgreement()
      setSelectedFile(null)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload version')
      console.error('Failed to upload version:', err)
    } finally {
      setUploading(false)
    }
  }

  const loadNextStatus = async () => {
    if (!agreement) return

    try {
      const response = await api.get<{ current_status: string; next_status: string | null; can_transition: boolean }>(
        `${apiBase}/agreements/${agreement.id}/next-status`
      )
      setNextStatus(response.data.next_status)
    } catch (err: any) {
      console.error('Failed to load next status:', err)
      setNextStatus(null)
    }
  }

  const handleMoveToNextStage = () => {
    if (!nextStatus) return
    
    // Check for unsaved edits before allowing status change
    if (hasUnsavedEdits) {
      const confirm = window.confirm(
        'You have unsaved changes. Do you want to save them before moving to the next stage?\n\n' +
        'Click OK to save, or Cancel to proceed without saving.'
      )
      if (confirm) {
        // User wants to save - we'll need to trigger save, but for now just warn
        setError('Please save your changes before moving to the next stage.')
        return
      }
      // User chose to proceed without saving - allow status change
    }
    
    setShowStatusConfirmModal(true)
  }

  const confirmStatusChange = async () => {
    if (!agreement || !nextStatus) return

    setChangingStatus(true)
    setError(null)
    try {
      const response = await api.patch<Agreement>(
        `${apiBase}/agreements/${agreement.id}/status`,
        { status: nextStatus }
      )
      setAgreement(response.data)
      setShowStatusConfirmModal(false)
      // Next status will be updated automatically via useEffect
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to change status')
      console.error('Failed to change status:', err)
      setShowStatusConfirmModal(false)
    } finally {
      setChangingStatus(false)
    }
  }

  // REMOVED: Reset workflow handlers - not part of production workflow
  // const handleResetWorkflow = () => { ... }
  // const confirmResetWorkflow = async () => { ... }


  // Handle save from ONLYOFFICE editor - refresh agreement to show new version
  const handleSaveDocument = async () => {
    if (!agreement) return

    console.log('[Save] Save triggered, starting refresh...')
    setSavingDocument(true)
    setError(null)
    
    try {
      const previousVersionCount = agreement.documents?.length || 0
      const previousLatestVersion = agreement.documents && agreement.documents.length > 0
        ? Math.max(...agreement.documents.map(d => d.version_number))
        : 0

      console.log(`[Save] Previous: ${previousVersionCount} docs, latest version: ${previousLatestVersion}`)

      let newVersionCreated = false

      // Poll until new version appears (max 15 attempts, 1 second each)
      for (let attempt = 0; attempt < 15; attempt++) {
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        // Use full loadAgreement to ensure complete refresh (skip loading state to avoid UI flicker)
        const updated = await loadAgreement(true)
        if (updated) {
          const newVersionCount = updated.documents?.length || 0
          const newLatestVersion = updated.documents && updated.documents.length > 0
            ? Math.max(...updated.documents.map(d => d.version_number))
            : 0
          
          console.log(`[Save] Attempt ${attempt + 1}: ${newVersionCount} docs, latest: ${newLatestVersion}`)
          
          // If we see a new version, stop polling
          if (newVersionCount > previousVersionCount || newLatestVersion > previousLatestVersion) {
            console.log(`[Save] ✅ New version detected: ${newLatestVersion} (was ${previousLatestVersion})`)
            // Force UI update
            setSelectedVersion(null)
            setHasUnsavedEdits(false)
            newVersionCreated = true
            break
          }
        }
      }

      // Handle the edge case where no changes were made
      if (!newVersionCreated) {
        console.log('[Save] No new version detected. Document content was identical.')
        setError('Document saved. No changes were detected, so a new version was not created.')
        setHasUnsavedEdits(false)
      }

    } catch (err: any) {
      console.error('[Save] Failed to refresh after save:', err)
      setError('Failed to verify document save status.')
    } finally {
      setSavingDocument(false)
      console.log('[Save] Refresh complete')
    }
  }
  
  // Reset unsaved edits when version changes
  useEffect(() => {
    setHasUnsavedEdits(false)
  }, [selectedVersion])

  // Load site profile when signature modal opens
  useEffect(() => {
    const loadSiteProfile = async () => {
      if (showSignatureModal && selectedSiteId) {
        try {
          const response = await api.get(`${apiBase}/sites/${selectedSiteId}/profile`)
          setSiteProfile(response.data)
          // Auto-fill emails from profile
          if (response.data?.authorized_signatory_email) {
            setSiteSignerEmail(response.data.authorized_signatory_email)
          }
        } catch (err: any) {
          // Profile might not exist yet - that's okay, backend will handle it
          console.log('Site profile not found, backend will auto-fill:', err)
          setSiteProfile(null)
        }
      }
    }
    loadSiteProfile()
  }, [showSignatureModal, selectedSiteId, apiBase])

  const handleSendForSignature = async () => {
    if (!agreement) {
      setError('Agreement not found')
      return
    }

    setSendingForSignature(true)
    setError(null)
    try {
      const formData = new FormData()
      // Only send emails if provided (backend will auto-fill if empty)
      if (siteSignerEmail.trim()) {
        formData.append('site_signer_email', siteSignerEmail.trim())
      }
      if (sponsorSignerEmail.trim()) {
        formData.append('sponsor_signer_email', sponsorSignerEmail.trim())
      }
      if (ccEmails.trim()) {
        formData.append('cc_emails', ccEmails.trim())
      }

      const response = await api.post<Agreement>(
        `${apiBase}/agreements/${agreement.id}/send-for-signature`,
        formData
      )
      setAgreement(response.data)
      setShowSignatureModal(false)
      setSiteSignerEmail('')
      setSponsorSignerEmail('')
      setCcEmails('')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send for signature')
      console.error('Failed to send for signature:', err)
    } finally {
      setSendingForSignature(false)
    }
  }

  const handleDownloadSignedPDF = async (signedDoc: { id: string; file_path: string }) => {
    try {
      // Use the signed document endpoint
      const response = await api.get(
        `${apiBase}/agreements/${agreement?.id}/signed-document/${signedDoc.id}`,
        { responseType: 'blob' }
      )
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      // Extract file name from path
      const fileName = signedDoc.file_path.split('/').pop() || 'signed_agreement.pdf'
      link.setAttribute('download', fileName)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      setError('Failed to download signed PDF')
      console.error('Failed to download signed PDF:', err)
    }
  }

  const handleViewSignedPDF = async (signedDoc: { id: string; file_path: string }) => {
    try {
      // Use the signed document endpoint to get PDF blob
      const response = await api.get(
        `${apiBase}/agreements/${agreement?.id}/signed-document/${signedDoc.id}`,
        { responseType: 'blob' }
      )
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const blobUrl = URL.createObjectURL(blob)
      window.open(blobUrl, '_blank', 'noopener,noreferrer')
      // Clean up after 30 seconds
      setTimeout(() => URL.revokeObjectURL(blobUrl), 30000)
    } catch (err: any) {
      setError('Failed to view signed PDF')
      console.error('Failed to view signed PDF:', err)
    }
  }

  const handleSyncZohoStatus = async () => {
    if (!agreement) return

    setSyncingZohoStatus(true)
    setError(null)
    try {
      const response = await api.post<{ status: string; message: string; agreement: Agreement }>(
        `${apiBase}/agreements/${agreement.id}/sync-zoho-status`
      )
      setAgreement(response.data.agreement)
      console.log('Zoho Sign sync response:', response.data)
      // Reload agreement to get updated signed documents
      await loadAgreement()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to sync Zoho Sign status')
      console.error('Error syncing Zoho Sign status:', err)
    } finally {
      setSyncingZohoStatus(false)
    }
  }

  const handleResetWorkflow = async () => {
    if (!agreement) return

    const confirmed = window.confirm(
      'This will completely reset the agreement workflow:\n\n' +
      '- Reset status to DRAFT\n' +
      '- Delete ALL comments\n' +
      '- Delete ALL document versions\n' +
      '- Delete ALL legacy versions\n' +
      '- Clear signature fields\n' +
      '- Delete signed documents\n\n' +
      'You will need to select a template again to start fresh.\n\n' +
      'Do you want to continue?'
    )
    if (!confirmed) return

    setResettingWorkflow(true)
    setError(null)
    try {
      const response = await api.delete<{ status: string; message: string; agreement: Agreement }>(
        `${apiBase}/agreements/${agreement.id}/reset`
      )
      // Reload agreement to ensure we have the latest state
      await loadAgreement()
      setSelectedVersion(null) // Reset selected version to null (will show latest or nothing)
      setShowCreateForm(false) // Hide create form if shown
      setSelectedTemplateId('') // Reset template selection
      setHasUnsavedEdits(false) // Clear unsaved edits flag
      console.log('Agreement workflow reset response:', response.data)
      
      // Explicitly load templates after reset if study is selected
      if (selectedStudyId) {
        await loadTemplates()
      }
      
      // Show success message
      alert(response.data.message || 'Agreement workflow reset successfully. Please select a template to start fresh.')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reset agreement workflow')
      console.error('Error resetting agreement workflow:', err)
    } finally {
      setResettingWorkflow(false)
    }
  }


  // Get current document content
  const getCurrentDocument = () => {
    if (!agreement || !agreement.documents || agreement.documents.length === 0) {
      return null
    }
    
    // If selectedVersion is explicitly set, use it; otherwise default to latest
    const versionToShow = selectedVersion !== null ? selectedVersion : getLatestVersionNumber()
    
    if (versionToShow === null) {
      // No version available, return first document as fallback
      return agreement.documents[0]
    }
    
    // Find document with matching version, or fallback to latest
    const doc = agreement.documents.find(d => d.version_number === versionToShow)
    if (doc) {
      return doc
    }
    
    // Fallback: return latest document if selected version not found
    const latest = getLatestVersionNumber()
    return agreement.documents.find(d => d.version_number === latest) || agreement.documents[0]
  }
  
  // Get latest version number
  const getLatestVersionNumber = () => {
    if (!agreement || !agreement.documents || agreement.documents.length === 0) {
      return null
    }
    return Math.max(...agreement.documents.map(d => d.version_number))
  }
  
  // Check if current selected version is the latest (and thus editable)
  // Uses backend permission flags - no hardcoded status checks
  const isCurrentVersionEditable = () => {
    if (!agreement) return false
    const currentDoc = getCurrentDocument()
    const latestVersion = getLatestVersionNumber()
    if (!currentDoc || !latestVersion) {
      return false
    }
    const isLatest = currentDoc.version_number === latestVersion
    // Use backend can_edit flag (no hardcoded status logic)
    const canEdit = agreement.can_edit === true || agreement.can_edit === 'true'
    // Only latest version can be edited, and only if backend says can_edit
    return isLatest && canEdit
  }
  
  // Check if current version can be saved (creates new version)
  // Uses backend can_save flag - no hardcoded status checks
  const canSaveCurrentVersion = () => {
    if (!agreement) return false
    const currentDoc = getCurrentDocument()
    const latestVersion = getLatestVersionNumber()
    if (!currentDoc || !latestVersion) return false
    const isLatest = currentDoc.version_number === latestVersion
    // Use backend can_save flag (no hardcoded status logic)
    const canSave = agreement.can_save === true || agreement.can_save === 'true'
    // Only latest version can be saved
    return isLatest && canSave
  }

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString()
    } catch {
      return dateString
    }
  }

  if (!selectedSiteId) {
    return (
      <div className="flex flex-col h-full bg-gray-50 p-6">
        <h2 className="text-2xl font-semibold text-gray-800 mb-2">Agreement Workflow</h2>
        <p className="text-gray-600">Please select a Study and Site to view agreements.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-gray-50 p-6 overflow-y-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Agreement Workflow</h1>
        <p className="text-gray-600">Manage agreement versions and track status changes.</p>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      {/* Create Agreement Form */}
      {!agreement && !loading && (
        <div className="mb-6 p-4 bg-white border border-gray-200 rounded-lg">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Create New Agreement</h3>
          <p className="text-sm text-gray-600 mb-4">
            New agreements must be created from a template. Please select a template to proceed.
          </p>
          {!showCreateForm ? (
            <button
              onClick={() => setShowCreateForm(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Create from Template
            </button>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Template <span className="text-red-500">*</span>
                </label>
                <select
                  value={selectedTemplateId}
                  onChange={(e) => setSelectedTemplateId(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  required
                >
                  <option value="">Select a template...</option>
                  {availableTemplates.map((template) => (
                    <option key={template.id} value={template.id}>
                      {template.template_name} ({template.template_type})
                    </option>
                  ))}
                </select>
                {availableTemplates.length === 0 && (
                  <p className="text-xs text-gray-500 mt-1">
                    No active templates found. Please create templates in Study Setup first.
                  </p>
                )}
              </div>
              <input
                type="text"
                value={newAgreementTitle}
                onChange={(e) => setNewAgreementTitle(e.target.value)}
                placeholder="Agreement Title"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
              <div className="flex gap-2">
                <button
                  onClick={handleCreateAgreement}
                  disabled={creating || !newAgreementTitle.trim() || !selectedTemplateId}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {creating ? 'Creating...' : 'Create'}
                </button>
                <button
                  onClick={() => {
                    setShowCreateForm(false)
                    setNewAgreementTitle('')
                  }}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Loading State */}
      {loading && !agreement && (
        <div className="text-center p-8">
          <p className="text-sm text-gray-600 mt-2">Loading agreement...</p>
        </div>
      )}

      {/* Agreement Display */}
      {agreement && (
        <div className="space-y-6">
          {/* Agreement Status */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-start justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900">Agreement Status</h2>
              <button
                type="button"
                onClick={handleResetWorkflow}
                disabled={resettingWorkflow}
                className="inline-flex items-center rounded-md border border-red-300 bg-white px-3 py-1 text-xs font-medium text-red-700 shadow-sm hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {resettingWorkflow ? 'Resetting...' : 'Reset Workflow'}
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-700">Title:</label>
                <p className="text-gray-900">{agreement.title}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Current Status:</label>
                <p className="text-gray-900 font-semibold">{agreement.status}</p>
              </div>
              {/* Status transition button - Only show if documents exist */}
              {agreement.documents && agreement.documents.length > 0 && (
                <>
                  {nextStatus && (agreement.can_move_status === true || agreement.can_move_status === 'true') && (
                    <div>
                      <label className="text-sm font-medium text-gray-700">Next Stage:</label>
                      <div className="mt-2">
                        <button
                          onClick={handleMoveToNextStage}
                          disabled={changingStatus}
                          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 font-medium"
                        >
                          {changingStatus ? 'Processing...' : `Move to ${nextStatus.replace(/_/g, ' ')}`}
                        </button>
                        <p className="text-xs text-gray-500 mt-1">
                          Next allowed status: {nextStatus.replace(/_/g, ' ')}
                        </p>
                      </div>
                    </div>
                  )}
                  {!nextStatus && !agreement.is_locked && (
                    <div>
                      <p className="text-sm text-gray-500 italic">No further transitions available</p>
                    </div>
                  )}
                  {(agreement.is_locked === true || agreement.is_locked === 'true') && (
                    <div>
                      <p className="text-sm text-gray-500 italic">Agreement is locked. No changes allowed.</p>
                    </div>
                  )}
                  {nextStatus && !(agreement.can_move_status === true || agreement.can_move_status === 'true') && (
                    <div>
                      <p className="text-sm text-yellow-600 italic">Status transition is not allowed at this time.</p>
                    </div>
                  )}
                </>
              )}
              
              {/* Show message when no documents exist */}
              {(!agreement.documents || agreement.documents.length === 0) && (
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm font-semibold text-blue-900 mb-1">
                    📄 No document versions found
                  </p>
                  <p className="text-sm text-blue-800">
                    Please select a template below to create the initial document version.
                  </p>
                </div>
              )}
              
              {/* Send for Signature Button - Only show when status is READY_FOR_SIGNATURE */}
              {agreement.status === 'READY_FOR_SIGNATURE' && (
                <div className="mt-4">
                  <button
                    onClick={() => setShowSignatureModal(true)}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium"
                  >
                    Send for Signature
                  </button>
                  <p className="text-xs text-gray-500 mt-1">
                    Send this agreement to Zoho Sign for electronic signature
                  </p>
                </div>
              )}
              
              {/* Signature Status Display */}
              {agreement.status === 'SENT_FOR_SIGNATURE' && (
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-blue-800 font-medium">
                        ⏳ Waiting for signature...
                      </p>
                      {agreement.zoho_request_id && (
                        <p className="text-xs text-blue-600 mt-1">
                          Request ID: {agreement.zoho_request_id}
                        </p>
                      )}
                    </div>
                    <button
                      onClick={handleSyncZohoStatus}
                      disabled={syncingZohoStatus}
                      className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                    >
                      {syncingZohoStatus ? 'Syncing...' : 'Sync Status'}
                    </button>
                  </div>
                  <p className="text-xs text-gray-600 mt-2">
                    Click "Sync Status" to manually check the signature status from Zoho Sign
                  </p>
                  {/* Show signed documents if available (after sync) */}
                  {agreement.signed_documents && agreement.signed_documents.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-blue-200">
                      <p className="text-xs text-blue-800 font-medium mb-2">Signed Document Available:</p>
                      {agreement.signed_documents.map((doc) => (
                        <div key={doc.id} className="space-y-2">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleViewSignedPDF(doc)}
                              className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 font-medium"
                            >
                              View Signed PDF
                            </button>
                            <button
                              onClick={() => handleDownloadSignedPDF(doc)}
                              className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                            >
                              Download Signed PDF
                            </button>
                          </div>
                          {doc.signed_at && (
                            <p className="text-xs text-gray-600">
                              Signed: {new Date(doc.signed_at).toLocaleString()}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
              
              {/* Executed Status - Show signed documents */}
              {agreement.status === 'EXECUTED' && agreement.signed_documents && agreement.signed_documents.length > 0 && (
                <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-sm text-green-800 font-medium mb-2">
                    ✓ Agreement Executed
                  </p>
                  {agreement.signed_documents.map((doc) => (
                    <div key={doc.id} className="space-y-2">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleViewSignedPDF(doc)}
                          className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 font-medium"
                        >
                          View Signed PDF
                        </button>
                        <button
                          onClick={() => handleDownloadSignedPDF(doc)}
                          className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                        >
                          Download Signed PDF
                        </button>
                      </div>
                      {doc.signed_at && (
                        <p className="text-xs text-gray-600">
                          Signed: {new Date(doc.signed_at).toLocaleString()}
                        </p>
                      )}
                      <p className="text-xs text-gray-500">
                        Downloaded from Zoho: {new Date(doc.downloaded_from_zoho_at).toLocaleString()}
                      </p>
                    </div>
                  ))}
                </div>
              )}
              
              {/* REMOVED: Reset Workflow Button - not part of production workflow */}
            </div>
          </div>

          {/* Conditional Rendering: Legacy vs New Agreement */}
          {/* Auto-detect legacy: if has versions but no documents, treat as legacy */}
          {(() => {
            // Auto-detect legacy status (fallback if backend flag is incorrect)
            const hasVersions = agreement.versions && agreement.versions.length > 0
            const hasDocuments = agreement.documents && agreement.documents.length > 0
            const isLegacyByData = hasVersions && !hasDocuments
            const effectiveIsLegacy = agreement.is_legacy === 'true' || isLegacyByData
            
            // Log detection for debugging
            console.log('🔍 LEGACY DETECTION:', {
              is_legacy: agreement.is_legacy,
              hasVersions,
              hasDocuments,
              isLegacyByData,
              effectiveIsLegacy
            })
            
            if (isLegacyByData && agreement.is_legacy !== 'true') {
              console.log('⚠️ AUTO-DETECTED LEGACY: Agreement has versions but no documents, treating as legacy')
            }
            
            return effectiveIsLegacy
          })() ? (
            /* LEGACY AGREEMENT: Show file-based workflow */
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Versions (Legacy)</h2>
              
              {/* Upload New Version - Only for legacy agreements */}
              {agreement.can_upload_new_version && (
                <div className="mb-4 p-4 bg-gray-50 rounded-lg">
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">Upload New Version</h3>
                  {/* Use backend is_locked flag instead of hardcoded status check */}
                  {(agreement.is_locked === true || agreement.is_locked === 'true') ? (
                    <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <p className="text-sm text-yellow-800">
                        Version uploads are locked. Agreement is locked.
                      </p>
                    </div>
                  ) : (
                    <div className="flex gap-2">
                      <input
                        type="file"
                        onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                        className="px-4 py-2 border border-gray-300 rounded-lg"
                        disabled={uploading}
                      />
                      <button
                        onClick={handleUploadVersion}
                        disabled={!selectedFile || uploading}
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400"
                      >
                        {uploading ? 'Uploading...' : 'Upload Version'}
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Legacy Versions List */}
              {agreement.versions.length === 0 ? (
                <p className="text-gray-600">No versions uploaded yet.</p>
              ) : (
                <div className="space-y-2">
                  {agreement.versions.map((version) => {
                    let badgeLabel = 'Draft'
                    let badgeColor = 'bg-gray-100 text-gray-800'
                    
                    if (version.is_signed_version === 'true') {
                      badgeLabel = 'Signed'
                      badgeColor = 'bg-green-100 text-green-800'
                    } else if (version.is_external_visible === 'true') {
                      badgeLabel = 'Shared'
                      badgeColor = 'bg-blue-100 text-blue-800'
                    }
                    
                    return (
                      <div
                        key={version.id}
                        className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <div className="flex items-center gap-2 mb-2">
                              <p className="font-semibold text-gray-900">
                                Version {version.version_number}
                              </p>
                              <span className={`px-2 py-1 ${badgeColor} text-xs rounded font-medium`}>
                                {badgeLabel}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600">
                              Uploaded by: {version.uploaded_by || 'System'}
                            </p>
                            <p className="text-sm text-gray-600">
                              Uploaded at: {formatDate(version.uploaded_at)}
                            </p>
                            {version.file_path && (
                              <p className="text-sm text-gray-600">File: {version.file_path.split('/').pop()}</p>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          ) : (
            /* NEW AGREEMENT: Show template-based document workflow */
            <div className="bg-white border border-gray-200 rounded-lg p-6 flex flex-col" style={{ minHeight: '700px', height: '100%' }}>
              <h2 className="text-xl font-bold text-gray-900 mb-4">Document Editor</h2>

              {/* Document Editor */}
              {(() => {
                const docCount = agreement.documents?.length || 0
                console.log('🔍 DOCUMENT EDITOR RENDER:', {
                  docCount,
                  hasDocuments: docCount > 0,
                  availableTemplatesCount: availableTemplates.length
                })
                return docCount > 0
              })() ? (
                <div className="space-y-4">
                  {/* Version Selector */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Select Version:
                    </label>
                    <select
                      value={selectedVersion ?? getLatestVersionNumber() ?? ''}
                      onChange={(e) => {
                        const version = e.target.value ? parseInt(e.target.value) : null
                        setSelectedVersion(version)
                      }}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                    >
                      {agreement.documents
                        .sort((a, b) => b.version_number - a.version_number)
                        .map((doc) => (
                          <option key={doc.id} value={doc.version_number}>
                            Version {doc.version_number} {doc.is_signed_version === 'true' ? '(Signed)' : ''}
                          </option>
                        ))}
                    </select>
                    {(() => {
                      const currentVersion = selectedVersion ?? getLatestVersionNumber()
                      const latestVersion = getLatestVersionNumber()
                      if (currentVersion && latestVersion && currentVersion !== latestVersion) {
                        return (
                          <p className="text-xs text-gray-500 mt-1">
                            Viewing older version (read-only)
                          </p>
                        )
                      }
                      return null
                    })()}
                  </div>

                  {/* Document Editor or Signed PDF Viewer */}
                  <div className="flex-1 border border-gray-200 rounded-lg bg-white overflow-hidden flex flex-col" style={{ minHeight: '600px', height: '100%' }}>
                    {(() => {
                      const currentDoc = getCurrentDocument()
                      const isSigned = currentDoc?.is_signed_version === 'true'
                      
                      // If this is a signed version, show the signed PDF
                      if (isSigned) {
                        if (agreement.signed_documents && agreement.signed_documents.length > 0) {
                          // Get the first signed document (there should typically be one per agreement)
                          const signedDoc = agreement.signed_documents[0]
                          
                          // Use SignedPDFViewer component to handle authenticated PDF loading
                          return <SignedPDFViewer 
                            agreementId={agreement.id} 
                            signedDocumentId={signedDoc.id}
                            apiBase={apiBase}
                          />
                        } else {
                          // Signed version but PDF not yet available (shouldn't happen, but handle gracefully)
                          return (
                            <div className="w-full h-full flex flex-col items-center justify-center p-8">
                              <div className="text-center">
                                <p className="text-yellow-800 font-medium mb-2">
                                  ⚠️ Signed version selected, but signed PDF is not yet available
                                </p>
                                <p className="text-sm text-gray-600 mb-4">
                                  The signed document may still be processing. Please sync the Zoho Sign status.
                                </p>
                                <button
                                  onClick={handleSyncZohoStatus}
                                  disabled={syncingZohoStatus}
                                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
                                >
                                  {syncingZohoStatus ? 'Syncing...' : 'Sync Status from Zoho'}
                                </button>
                              </div>
                            </div>
                          )
                        }
                      }
                      
                      // Debug: Log current document info
                      console.log('🔍 CURRENT DOCUMENT CHECK:', {
                        hasCurrentDoc: !!currentDoc,
                        documentId: currentDoc?.id,
                        versionNumber: currentDoc?.version_number,
                        hasDocumentFilePath: !!currentDoc?.document_file_path,
                        documentFilePath: currentDoc?.document_file_path,
                        hasDocumentContent: !!currentDoc?.document_content,
                        allDocKeys: currentDoc ? Object.keys(currentDoc) : []
                      })
                      
                      // If no current document, show message to create one
                      if (!currentDoc) {
                        return (
                          <div className="w-full h-full flex items-center justify-center p-8">
                            <div className="text-center">
                              <p className="text-gray-600 mb-4">
                                No document available. Please select a template to create a new document.
                              </p>
                            </div>
                          </div>
                        )
                      }
                      
                      // Check if document has DOCX file path
                      if (currentDoc.document_file_path) {
                        // Show ONLYOFFICE editor for DOCX files
                        console.log('✅ Rendering ONLYOFFICE editor for document with file path')
                        const currentVersionNumber = currentDoc.version_number
                        if (!currentVersionNumber) {
                          return (
                            <div className="w-full h-full flex items-center justify-center p-8">
                              <div className="text-center">
                                <p className="text-red-600 mb-2">Error: Document version number is missing</p>
                              </div>
                            </div>
                          )
                        }
                        const configEndpoint = `/agreements/${agreement.id}/onlyoffice-config?version=${currentVersionNumber}`
                        
                        // Use stable key based on document ID to prevent remounting
                        // Only remount if document ID actually changes (different version selected)
                        const editorKey = `editor-${currentDoc.id}`
                        
                        return (
                          <OnlyOfficeEditor
                            key={editorKey}
                            agreementId={agreement.id}
                            apiBase={apiBase}
                            canEdit={isCurrentVersionEditable()}
                            onSave={canSaveCurrentVersion() ? handleSaveDocument : undefined}
                            configEndpoint={configEndpoint}
                          />
                        )
                      } else if (currentDoc.document_content) {
                        // Fallback to old TipTap editor for legacy JSON content
                        return (
                          <div className="w-full h-full flex items-center justify-center p-8">
                            <div className="text-center">
                              <p className="text-gray-600 mb-2">
                                Legacy document format detected
                              </p>
                              <p className="text-sm text-gray-500">
                                This document uses the old JSON format. Please create a new version from template to use ONLYOFFICE editor.
                              </p>
                            </div>
                          </div>
                        )
                      } else {
                        // No document content available
                        return (
                          <div className="w-full h-full flex items-center justify-center p-8">
                            <div className="text-center">
                              <p className="text-gray-600">
                                No document content available
                              </p>
                            </div>
                          </div>
                        )
                      }
                    })()}
                  </div>

                  {/* Document History */}
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-2">Version History</h3>
                    <div className="space-y-2">
                      {agreement.documents.map((doc) => (
                        <div
                          key={doc.id}
                          className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="font-medium text-gray-900">
                                Version {doc.version_number}
                                {doc.is_signed_version === 'true' && (
                                  <span className="ml-2 px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                                    Signed
                                  </span>
                                )}
                              </p>
                              <p className="text-xs text-gray-600">
                                Created: {formatDate(doc.created_at)} by {doc.created_by || 'System'}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                /* No documents - Show template selection to start fresh */
                <div className="space-y-4">
                  {console.log('🔍 RENDERING TEMPLATE SELECTION UI - No documents found')}
                  <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <p className="text-sm font-semibold text-blue-900 mb-2">
                      📄 No document versions found
                    </p>
                    <p className="text-sm text-blue-800">
                      Please select a template to create the initial document version.
                    </p>
                    <p className="text-xs text-gray-600 mt-2">
                      Study ID: {selectedStudyId || 'Not set'} | Templates loaded: {availableTemplates.length}
                    </p>
                  </div>
                  
                  {/* Template Selection Form */}
                  <div className="p-4 border border-gray-200 rounded-lg bg-gray-50">
                    <h3 className="text-sm font-semibold text-gray-700 mb-3">Select Template</h3>
                    {availableTemplates.length === 0 ? (
                      <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                        <p className="text-sm text-yellow-800 font-medium mb-2">
                          ⚠️ No templates available
                        </p>
                        <p className="text-sm text-yellow-700">
                          Please create a template in the Study Setup tab first. 
                          {selectedStudyId ? (
                            <span> Templates are loaded for study: {selectedStudyId}</span>
                          ) : (
                            <span> No study selected. Please select a study first.</span>
                          )}
                        </p>
                        <button
                          onClick={() => loadTemplates()}
                          className="mt-2 px-3 py-1 bg-yellow-600 text-white text-sm rounded hover:bg-yellow-700"
                        >
                          🔄 Retry Loading Templates
                        </button>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <select
                          value={selectedTemplateId}
                          onChange={(e) => setSelectedTemplateId(e.target.value)}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="">-- Select Template --</option>
                          {availableTemplates.map((template) => (
                            <option key={template.id} value={template.id}>
                              {template.template_name} ({template.template_type})
                            </option>
                          ))}
                        </select>
                        <button
                          onClick={handleCreateDocumentFromTemplate}
                          disabled={!selectedTemplateId || creating}
                          className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
                        >
                          {creating ? 'Creating Document...' : 'Create Document from Template'}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Activity Timeline */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Activity Timeline</h2>
            
            {/* Comments List (SYSTEM logs only) */}
            {agreement.comments.length === 0 ? (
              <p className="text-gray-600">No comments yet.</p>
            ) : (
              <div className="space-y-4">
                {agreement.comments.map((comment) => {
                  // Determine badge color based on comment type
                  let badgeColor = 'bg-gray-100 text-gray-800'
                  let badgeLabel = 'External'
                  
                  if (comment.comment_type === 'SYSTEM') {
                    badgeColor = 'bg-blue-100 text-blue-800'
                    badgeLabel = 'System'
                  } else if (comment.comment_type === 'INTERNAL') {
                    badgeColor = 'bg-green-100 text-green-800'
                    badgeLabel = 'Internal'
                  }
                  
                  return (
                    <div
                      key={comment.id}
                      className="p-4 border-l-4 rounded-lg bg-gray-50 border-gray-300"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-1 ${badgeColor} text-xs rounded font-medium`}>
                            {badgeLabel}
                          </span>
                          <span className="text-xs text-gray-600">
                            {comment.created_by || 'System'}
                          </span>
                        </div>
                        <span className="text-xs text-gray-500">
                          {formatDate(comment.created_at)}
                        </span>
                      </div>
                      <p className="text-gray-900 mb-2 whitespace-pre-wrap">{comment.content}</p>
                      {comment.version_id && (
                        <p className="text-xs text-gray-600 mt-1">
                          Related to Version {agreement.versions.find((v) => v.id === comment.version_id)?.version_number || 'N/A'}
                        </p>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Status Change Confirmation Modal */}
      {showStatusConfirmModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Confirm Status Change</h3>
            <p className="text-gray-700 mb-2">
              Are you sure you want to move this agreement from <strong>{agreement?.status.replace(/_/g, ' ')}</strong> to <strong>{nextStatus?.replace(/_/g, ' ')}</strong>?
            </p>
            <p className="text-sm text-gray-500 mb-6">
              This action will be logged and cannot be undone.
            </p>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setShowStatusConfirmModal(false)}
                disabled={changingStatus}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 disabled:bg-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={confirmStatusChange}
                disabled={changingStatus}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400"
              >
                {changingStatus ? 'Processing...' : 'Confirm'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Send for Signature Modal */}
      {showSignatureModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Send for Signature</h3>
            <p className="text-sm text-gray-600 mb-4">
              Email addresses are auto-filled from Site Profile and system configuration. 
              The site signatory will sign first (Order 1), followed by the sponsor signatory (Order 2).
              You can override the auto-filled values if needed.
            </p>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Site Signatory Email (Order 1) <span className="text-gray-500 text-xs">(Auto-filled)</span>
                </label>
                <input
                  type="email"
                  value={siteSignerEmail}
                  onChange={(e) => setSiteSignerEmail(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  placeholder="Auto-filled from Site Profile"
                />
                {siteProfile?.authorized_signatory_email && (
                  <p className="text-xs text-gray-500 mt-1">
                    From Site Profile: {siteProfile.authorized_signatory_email}
                  </p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Sponsor Signatory Email (Order 2) <span className="text-gray-500 text-xs">(Auto-filled)</span>
                </label>
                <input
                  type="email"
                  value={sponsorSignerEmail}
                  onChange={(e) => setSponsorSignerEmail(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  placeholder="Auto-filled from system config"
                />
                <p className="text-xs text-gray-500 mt-1">
                  From system configuration or current user
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  CC Emails (Optional)
                </label>
                <input
                  type="text"
                  value={ccEmails}
                  onChange={(e) => setCcEmails(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  placeholder="cc1@example.com, cc2@example.com"
                />
                <p className="text-xs text-gray-500 mt-1">Comma-separated list of email addresses</p>
              </div>
            </div>
            <div className="flex gap-2 justify-end mt-6">
              <button
                onClick={() => {
                  setShowSignatureModal(false)
                  setSiteSignerEmail('')
                  setSponsorSignerEmail('')
                  setCcEmails('')
                }}
                disabled={sendingForSignature}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 disabled:bg-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={handleSendForSignature}
                disabled={sendingForSignature}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400"
              >
                {sendingForSignature ? 'Sending...' : 'Send for Signature'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* REMOVED: Reset Workflow Confirmation Modal - not part of production workflow */}
    </div>
  )
}

export default AgreementTab
