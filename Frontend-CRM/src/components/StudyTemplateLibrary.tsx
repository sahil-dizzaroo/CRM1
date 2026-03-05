import React, { useState, useEffect } from 'react'
import { api } from '../lib/api'
import { useStudySite } from '../contexts/StudySiteContext'
import { useAuth } from '../contexts/AuthContext'
import OnlyOfficeEditor from './OnlyOfficeEditor'

interface StudyTemplate {
  id: string
  study_id: string
  template_name: string
  template_type: 'CDA' | 'CTA' | 'BUDGET' | 'OTHER'
  template_content: any // TipTap JSON (legacy)
  template_file_path?: string | null // Path to DOCX file
  placeholder_config?: Record<string, { editable: boolean }> | null
  field_mappings?: Record<string, string> | null // Dynamic field mappings: {"PLACEHOLDER_NAME": "data_source.field_name"}
  created_by: string | null
  created_at: string
  updated_at: string
  is_active: string
}

interface StudyTemplateLibraryProps {
  apiBase?: string
}

interface FieldOption {
  field: string
  label: string
}

const StudyTemplateLibrary: React.FC<StudyTemplateLibraryProps> = ({ apiBase = '/api' }) => {
  const { selectedStudyId } = useStudySite()
  const { user } = useAuth()
  const [templates, setTemplates] = useState<StudyTemplate[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<StudyTemplate | null>(null)
  const [showPreview, setShowPreview] = useState(false)
  const [showConfigModal, setShowConfigModal] = useState(false)
  const [configTemplate, setConfigTemplate] = useState<StudyTemplate | null>(null)
  const [placeholderConfig, setPlaceholderConfig] = useState<Record<string, { editable: boolean }>>({})
  const [savingConfig, setSavingConfig] = useState(false)
  
  // Field mappings state
  const [showFieldMappingsModal, setShowFieldMappingsModal] = useState(false)
  const [fieldMappingsTemplate, setFieldMappingsTemplate] = useState<StudyTemplate | null>(null)
  const [fieldMappings, setFieldMappings] = useState<Record<string, string>>({})
  const [savingFieldMappings, setSavingFieldMappings] = useState(false)
  const [newMappingPlaceholder, setNewMappingPlaceholder] = useState('')
  const [newMappingDataSource, setNewMappingDataSource] = useState<'site_profile' | 'agreement'>('site_profile')
  const [newMappingField, setNewMappingField] = useState('')
  const [mappingOptions, setMappingOptions] = useState<{
    site_profile: FieldOption[]
    agreement: FieldOption[]
  }>({
    site_profile: [],
    agreement: [],
  })
  
  // Upload form state
  const [templateName, setTemplateName] = useState('')
  const [templateType, setTemplateType] = useState<'CDA' | 'CTA' | 'BUDGET' | 'OTHER'>('CDA')
  const [templateFile, setTemplateFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)

  useEffect(() => {
    if (selectedStudyId) {
      loadTemplates()
    } else {
      setTemplates([])
    }
  }, [selectedStudyId])

  const loadTemplates = async () => {
    if (!selectedStudyId) return
    
    setLoading(true)
    setError(null)
    try {
      const response = await api.get<StudyTemplate[]>(
        `${apiBase}/studies/${selectedStudyId}/templates?active_only=false`
      )
      setTemplates(response.data)
    } catch (err: any) {
      // Extract error message - handle both string and object errors
      let errorMessage = 'Failed to load templates'
      if (err.response?.data) {
        const errorData = err.response.data
        if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail
        } else if (Array.isArray(errorData.detail)) {
          // Pydantic validation errors are arrays
          errorMessage = errorData.detail.map((e: any) => e.msg || JSON.stringify(e)).join(', ')
        } else if (typeof errorData.detail === 'object') {
          errorMessage = errorData.detail.msg || JSON.stringify(errorData.detail)
        }
      }
      setError(errorMessage)
      console.error('Failed to load templates:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleUploadTemplate = async () => {
    if (!selectedStudyId || !templateName || !templateFile) {
      setError('Please provide template name and DOCX file')
      return
    }

    // Validate file type - DOCX only
    const fileName = templateFile.name.toLowerCase()
    if (!fileName.endsWith('.docx') && !fileName.endsWith('.doc')) {
      setError('Only DOCX files are supported. Please upload a .docx file. PDF uploads are no longer supported.')
      return
    }

    setUploading(true)
    setError(null)
    
    try {
      // Create FormData for file upload
      const formData = new FormData()
      formData.append('template_name', templateName)
      formData.append('template_type', templateType)
      formData.append('template_file', templateFile)

      await api.post(`${apiBase}/studies/${selectedStudyId}/templates`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      // Reset form
      setTemplateName('')
      setTemplateType('CDA')
      setTemplateFile(null)
      setShowUploadModal(false)
      
      // Reload templates
      await loadTemplates()
    } catch (err: any) {
      // Extract error message - handle both string and object errors
      let errorMessage = 'Failed to upload template'
      if (err.response?.data) {
        const errorData = err.response.data
        if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail
        } else if (Array.isArray(errorData.detail)) {
          errorMessage = errorData.detail.map((e: any) => e.msg || JSON.stringify(e)).join(', ')
        } else if (typeof errorData.detail === 'object') {
          errorMessage = errorData.detail.msg || JSON.stringify(errorData.detail)
        }
      }
      setError(errorMessage)
      console.error('Failed to upload template:', err)
    } finally {
      setUploading(false)
    }
  }

  const handleDeactivateTemplate = async (templateId: string) => {
    if (!confirm('Are you sure you want to deactivate this template? It cannot be used for new agreements.')) {
      return
    }

    try {
      await api.patch(`${apiBase}/templates/${templateId}/deactivate`)
      await loadTemplates()
    } catch (err: any) {
      // Extract error message - handle both string and object errors
      let errorMessage = 'Failed to deactivate template'
      if (err.response?.data) {
        const errorData = err.response.data
        if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail
        } else if (Array.isArray(errorData.detail)) {
          errorMessage = errorData.detail.map((e: any) => e.msg || JSON.stringify(e)).join(', ')
        } else if (typeof errorData.detail === 'object') {
          errorMessage = errorData.detail.msg || JSON.stringify(errorData.detail)
        }
      }
      setError(errorMessage)
      console.error('Failed to deactivate template:', err)
    }
  }

  const handlePreviewTemplate = (template: StudyTemplate) => {
    setSelectedTemplate(template)
    setShowPreview(true)
  }

  const handleConfigurePlaceholders = (template: StudyTemplate) => {
    setConfigTemplate(template)
    // Initialize config with template's existing config or default (all editable)
    const config = template.placeholder_config || {}
    setPlaceholderConfig(config)
    setShowConfigModal(true)
  }

  const handleSavePlaceholderConfig = async () => {
    if (!configTemplate) return

    setSavingConfig(true)
    try {
      await api.put(
        `${apiBase}/templates/${configTemplate.id}/placeholder-config`,
        { placeholder_config: placeholderConfig }
      )
      setShowConfigModal(false)
      setConfigTemplate(null)
      await loadTemplates() // Reload to get updated config
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to save placeholder configuration'
      setError(errorMessage)
      console.error('Failed to save placeholder config:', err)
    } finally {
      setSavingConfig(false)
    }
  }

  const handleToggleEditable = (placeholderName: string) => {
    setPlaceholderConfig(prev => ({
      ...prev,
      [placeholderName]: {
        editable: !(prev[placeholderName]?.editable ?? true)
      }
    }))
  }

  const handleConfigureFieldMappings = async (template: StudyTemplate) => {
    setFieldMappingsTemplate(template)
    // Initialize mappings with template's existing mappings or empty object
    const mappings = template.field_mappings || {}
    setFieldMappings(mappings)

    // Load available mapping options (site_profile / agreement fields)
    try {
      const response = await api.get<{
        site_profile: FieldOption[]
        agreement: FieldOption[]
      }>(`${apiBase}/templates/field-mapping-options`)
      setMappingOptions(response.data)
    } catch (err) {
      console.error('Failed to load field mapping options:', err)
      // Do not block modal - user can still manually type if needed
    }

    setShowFieldMappingsModal(true)
  }

  const handleSaveFieldMappings = async () => {
    if (!fieldMappingsTemplate) return

    setSavingFieldMappings(true)
    try {
      await api.put(
        `${apiBase}/templates/${fieldMappingsTemplate.id}/field-mappings`,
        { field_mappings: fieldMappings }
      )
      setShowFieldMappingsModal(false)
      setFieldMappingsTemplate(null)
      setFieldMappings({})
      await loadTemplates() // Reload to get updated mappings
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to save field mappings'
      setError(errorMessage)
      console.error('Failed to save field mappings:', err)
    } finally {
      setSavingFieldMappings(false)
    }
  }

  const handleAddFieldMapping = () => {
    if (!newMappingPlaceholder || !newMappingField) {
      setError('Please provide both placeholder name and field name')
      return
    }
    
    const placeholderName = newMappingPlaceholder.toUpperCase().replace(/\s+/g, '_')
    const mappingPath = `${newMappingDataSource}.${newMappingField}`
    
    setFieldMappings(prev => ({
      ...prev,
      [placeholderName]: mappingPath
    }))
    
    // Reset form
    setNewMappingPlaceholder('')
    setNewMappingDataSource('site_profile')
    setNewMappingField('')
  }

  const handleRemoveFieldMapping = (placeholderName: string) => {
    setFieldMappings(prev => {
      const updated = { ...prev }
      delete updated[placeholderName]
      return updated
    })
  }

  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString()
  }

  if (!selectedStudyId) {
    return (
      <div className="flex items-center justify-center h-full p-8">
        <div className="text-center">
          <div className="text-6xl mb-4">📚</div>
          <h2 className="text-2xl font-semibold text-gray-800 mb-2">Template Library</h2>
          <p className="text-gray-600">
            Please select a Study to view templates.
          </p>
        </div>
      </div>
    )
  }

  return (
  <div className="flex flex-col h-full bg-gray-50 p-6 overflow-y-auto min-h-0">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Template Library</h1>
        <p className="text-gray-600">
          Manage document templates for this study. Templates are used to create new agreements.
        </p>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800">
          {typeof error === 'string' ? error : JSON.stringify(error)}
        </div>
      )}

      {/* Actions */}
      <div className="mb-6 flex justify-between items-center">
        <button
          onClick={() => setShowUploadModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
        >
          + Upload Template
        </button>
      </div>

      {/* Templates List */}
      {loading ? (
        <div className="text-center py-8 text-gray-500">Loading templates...</div>
      ) : templates.length === 0 ? (
        <div className="text-center py-8 bg-white rounded-lg border border-gray-200">
          <div className="text-4xl mb-2">📄</div>
          <p className="text-gray-600">No templates found. Upload a template to get started.</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Template Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {templates.map((template) => (
                <tr key={template.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{template.template_name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                      {template.template_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      template.is_active === 'true' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {template.is_active === 'true' ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(template.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handlePreviewTemplate(template)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        View
                      </button>
                      <button
                        onClick={() => handleConfigurePlaceholders(template)}
                        className="text-purple-600 hover:text-purple-900"
                      >
                        Configure
                      </button>
                      <button
                        onClick={() => handleConfigureFieldMappings(template)}
                        className="text-indigo-600 hover:text-indigo-900"
                        title="Configure Field Mappings"
                      >
                        Field Mappings
                      </button>
                      {template.is_active === 'true' && (
                        <button
                          onClick={() => handleDeactivateTemplate(template.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Deactivate
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Upload Template</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Template Name
                </label>
                <input
                  type="text"
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  placeholder="e.g., Standard CDA Template"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Template Type
                </label>
                <select
                  value={templateType}
                  onChange={(e) => setTemplateType(e.target.value as any)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="CDA">CDA</option>
                  <option value="CTA">CTA</option>
                  <option value="BUDGET">BUDGET</option>
                  <option value="OTHER">OTHER</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Template File (DOCX)
                </label>
                <input
                  type="file"
                  accept=".docx,.doc"
                  onChange={(e) => setTemplateFile(e.target.files?.[0] || null)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
                <p className="text-xs text-gray-500 mt-1">
                  DOCX files will be automatically converted to editable format. PDF uploads are no longer supported.
                </p>
              </div>
            </div>

            <div className="flex gap-2 justify-end mt-6">
              <button
                onClick={() => {
                  setShowUploadModal(false)
                  setTemplateName('')
                  setTemplateType('CDA')
                  setTemplateFile(null)
                }}
                disabled={uploading}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 disabled:bg-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={handleUploadTemplate}
                disabled={uploading || !templateName || !templateFile}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
              >
                {uploading ? 'Uploading...' : 'Upload'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Preview Modal */}
      {showPreview && selectedTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-[95vw] h-[90vh] mx-4 flex flex-col">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold text-gray-900">{selectedTemplate.template_name}</h3>
              <button
                onClick={() => {
                  setShowPreview(false)
                  setSelectedTemplate(null)
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            <div className="mb-4">
              <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800 mr-2">
                {selectedTemplate.template_type}
              </span>
              <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                selectedTemplate.is_active === 'true' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {selectedTemplate.is_active === 'true' ? 'Active' : 'Inactive'}
              </span>
            </div>

            {/* Show ONLYOFFICE editor if template has DOCX file, otherwise show JSON */}
            {selectedTemplate.template_file_path ? (
              <div className="flex-1 border border-gray-200 rounded-lg overflow-hidden" style={{ minHeight: '600px' }}>
                <OnlyOfficeEditor
                  templateId={selectedTemplate.id}
                  apiBase={apiBase}
                  canEdit={false}
                />
              </div>
            ) : (
              <div className="flex-1 border border-gray-200 rounded-lg p-4 bg-gray-50 overflow-auto">
                <pre className="text-xs">
                  {JSON.stringify(selectedTemplate.template_content, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Placeholder Configuration Modal */}
      {showConfigModal && configTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold text-gray-900">
                Template Field Configuration
              </h3>
              <button
                onClick={() => {
                  setShowConfigModal(false)
                  setConfigTemplate(null)
                  setPlaceholderConfig({})
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            <p className="text-sm text-gray-600 mb-4">
              Configure which placeholder fields are editable in agreements created from "{configTemplate.template_name}".
              Uncheck fields that should be locked and cannot be edited.
            </p>

            {Object.keys(placeholderConfig).length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>No placeholders detected in this template.</p>
                <p className="text-xs mt-2">Placeholders are automatically detected when templates are uploaded.</p>
              </div>
            ) : (
              <div className="space-y-3 mb-6">
                {Object.entries(placeholderConfig).map(([placeholderName, config]) => (
                  <div
                    key={placeholderName}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200"
                  >
                    <div className="flex items-center gap-3">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={config.editable}
                          onChange={() => handleToggleEditable(placeholderName)}
                          className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        />
                        <span className="text-sm font-medium text-gray-700">
                          {placeholderName.replace(/_/g, ' ')}
                        </span>
                      </label>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded ${
                      config.editable
                        ? 'bg-green-100 text-green-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {config.editable ? 'Editable' : 'Locked'}
                    </span>
                  </div>
                ))}
              </div>
            )}

            <div className="flex gap-2 justify-end mt-6 border-t border-gray-200 pt-4">
              <button
                onClick={() => {
                  setShowConfigModal(false)
                  setConfigTemplate(null)
                  setPlaceholderConfig({})
                }}
                disabled={savingConfig}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 disabled:bg-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={handleSavePlaceholderConfig}
                disabled={savingConfig || Object.keys(placeholderConfig).length === 0}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
              >
                {savingConfig ? 'Saving...' : 'Save Configuration'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Field Mappings Modal */}
      {showFieldMappingsModal && fieldMappingsTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold text-gray-900">
                Dynamic Field Mapping
              </h3>
              <button
                onClick={() => {
                  setShowFieldMappingsModal(false)
                  setFieldMappingsTemplate(null)
                  setFieldMappings({})
                  setNewMappingPlaceholder('')
                  setNewMappingDataSource('site_profile')
                  setNewMappingField('')
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            <p className="text-sm text-gray-600 mb-4">
              Configure how placeholders in "{fieldMappingsTemplate.template_name}" map to data sources.
              When creating an agreement from this template, placeholders will be automatically replaced with values from Site Profile or Agreement.
            </p>

            {/* Add New Mapping Form */}
            <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
              <h4 className="text-sm font-semibold text-gray-700 mb-3">Add New Mapping</h4>
              <div className="grid grid-cols-12 gap-2">
                <div className="col-span-3">
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Placeholder
                  </label>
                  <select
                    value={newMappingPlaceholder}
                    onChange={(e) => setNewMappingPlaceholder(e.target.value)}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                  >
                    <option value="">Select placeholder</option>
                    {fieldMappingsTemplate?.placeholder_config &&
                      Object.keys(fieldMappingsTemplate.placeholder_config).sort().map((name) => (
                        <option key={name} value={name}>
                          {`{{${name}}}`}
                        </option>
                      ))}
                  </select>
                </div>
                <div className="col-span-3">
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Data Source
                  </label>
                  <select
                    value={newMappingDataSource}
                    onChange={(e) => setNewMappingDataSource(e.target.value as 'site_profile' | 'agreement')}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                  >
                    <option value="site_profile">Site Profile</option>
                    <option value="agreement">Agreement</option>
                  </select>
                </div>
                <div className="col-span-4">
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Field Name
                  </label>
                  <select
                    value={newMappingField}
                    onChange={(e) => setNewMappingField(e.target.value)}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                  >
                    <option value="">Select field</option>
                    {mappingOptions[newMappingDataSource].map((opt) => (
                      <option key={opt.field} value={opt.field}>
                        {opt.label} ({opt.field})
                      </option>
                    ))}
                  </select>
                </div>
                <div className="col-span-2 flex items-end">
                  <button
                    onClick={handleAddFieldMapping}
                    disabled={!newMappingPlaceholder || !newMappingField}
                    className="w-full px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                  >
                    Add
                  </button>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Example: Placeholder "SITE_NAME" → Site Profile → "site_name"
              </p>
            </div>

            {/* Existing Mappings */}
            <div className="mb-6">
              <h4 className="text-sm font-semibold text-gray-700 mb-3">Current Mappings</h4>
              {Object.keys(fieldMappings).length === 0 ? (
                <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-lg border border-gray-200">
                  <p>No field mappings configured.</p>
                  <p className="text-xs mt-2">Add mappings above to enable automatic placeholder replacement.</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {Object.entries(fieldMappings).map(([placeholderName, mappingPath]) => {
                    const [dataSource, fieldName] = mappingPath.split('.', 2)
                    return (
                      <div
                        key={placeholderName}
                        className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-200"
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-gray-900">
                              {`{{${placeholderName}}}`}
                            </span>
                            <span className="text-gray-400">→</span>
                            <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded">
                              {dataSource}
                            </span>
                            <span className="text-gray-400">→</span>
                            <span className="text-sm text-gray-700">
                              {fieldName}
                            </span>
                          </div>
                        </div>
                        <button
                          onClick={() => handleRemoveFieldMapping(placeholderName)}
                          className="ml-2 px-2 py-1 text-xs text-red-600 hover:text-red-800 hover:bg-red-50 rounded"
                        >
                          Remove
                        </button>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>

            {/* Available Fields Reference */}
            <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h4 className="text-sm font-semibold text-blue-900 mb-2">Available Fields</h4>
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <p className="font-medium text-blue-800 mb-1">Site Profile:</p>
                  <ul className="text-blue-700 space-y-1">
                    <li>• site_name</li>
                    <li>• pi_name (principal_investigator)</li>
                    <li>• address_line_1</li>
                    <li>• city, state, country</li>
                    <li>• authorized_signatory_name</li>
                    <li>• authorized_signatory_email</li>
                  </ul>
                </div>
                <div>
                  <p className="font-medium text-blue-800 mb-1">Agreement:</p>
                  <ul className="text-blue-700 space-y-1">
                    <li>• title</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="flex gap-2 justify-end mt-6 border-t border-gray-200 pt-4">
              <button
                onClick={() => {
                  setShowFieldMappingsModal(false)
                  setFieldMappingsTemplate(null)
                  setFieldMappings({})
                  setNewMappingPlaceholder('')
                  setNewMappingDataSource('site_profile')
                  setNewMappingField('')
                }}
                disabled={savingFieldMappings}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 disabled:bg-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveFieldMappings}
                disabled={savingFieldMappings}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
              >
                {savingFieldMappings ? 'Saving...' : 'Save Mappings'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default StudyTemplateLibrary
