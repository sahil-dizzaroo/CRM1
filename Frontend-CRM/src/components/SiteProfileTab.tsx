import React, { useState, useEffect } from 'react'
import { api } from '../lib/api'
import { useStudySite } from '../contexts/StudySiteContext'

interface SiteProfileTabProps {
  apiBase?: string
}

interface SiteProfile {
  id: string
  site_id: string
  site_name?: string
  hospital_name?: string
  pi_name?: string
  pi_email?: string
  pi_phone?: string
  primary_contracting_entity?: string
  authorized_signatory_name?: string
  authorized_signatory_email?: string
  authorized_signatory_title?: string
  address_line_1?: string
  city?: string
  state?: string
  country?: string
  postal_code?: string
  site_coordinator_name?: string
  site_coordinator_email?: string
  created_at?: string
  updated_at?: string
}

const SiteProfileTab: React.FC<SiteProfileTabProps> = ({ apiBase = '/api' }) => {
  const { selectedSiteId } = useStudySite()
  const [profile, setProfile] = useState<SiteProfile | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

  // Form state
  const [formData, setFormData] = useState<Partial<SiteProfile>>({
    site_name: '',
    hospital_name: '',
    pi_name: '',
    pi_email: '',
    pi_phone: '',
    primary_contracting_entity: '',
    authorized_signatory_name: '',
    authorized_signatory_email: '',
    authorized_signatory_title: '',
    address_line_1: '',
    city: '',
    state: '',
    country: '',
    postal_code: '',
    site_coordinator_name: '',
    site_coordinator_email: '',
  })

  // Load profile when site changes
  useEffect(() => {
    if (selectedSiteId) {
      loadProfile()
    } else {
      setProfile(null)
      setFormData({
        site_name: '',
        hospital_name: '',
        pi_name: '',
        pi_email: '',
        pi_phone: '',
        primary_contracting_entity: '',
        authorized_signatory_name: '',
        authorized_signatory_email: '',
        authorized_signatory_title: '',
        address_line_1: '',
        city: '',
        state: '',
        country: '',
        postal_code: '',
        site_coordinator_name: '',
        site_coordinator_email: '',
      })
    }
  }, [selectedSiteId])

  const loadProfile = async () => {
    if (!selectedSiteId) return

    setLoading(true)
    setError(null)
    setSuccess(null)
    try {
      const response = await api.get<SiteProfile>(`${apiBase}/sites/${selectedSiteId}/profile`)
      setProfile(response.data)
      setFormData({
        site_name: response.data.site_name || '',
        hospital_name: response.data.hospital_name || '',
        pi_name: response.data.pi_name || '',
        pi_email: response.data.pi_email || '',
        pi_phone: response.data.pi_phone || '',
        primary_contracting_entity: response.data.primary_contracting_entity || '',
        authorized_signatory_name: response.data.authorized_signatory_name || '',
        authorized_signatory_email: response.data.authorized_signatory_email || '',
        authorized_signatory_title: response.data.authorized_signatory_title || '',
        address_line_1: response.data.address_line_1 || '',
        city: response.data.city || '',
        state: response.data.state || '',
        country: response.data.country || '',
        postal_code: response.data.postal_code || '',
        site_coordinator_name: response.data.site_coordinator_name || '',
        site_coordinator_email: response.data.site_coordinator_email || '',
      })
    } catch (err: any) {
      if (err.response?.status === 404) {
        // Profile doesn't exist yet, that's okay - show empty form
        setProfile(null)
        setError(null) // Clear any previous errors - 404 is expected for new sites
        // Form data is already reset in useEffect when selectedSiteId changes
      } else {
        setError(err.response?.data?.detail || 'Failed to load site profile')
      }
    } finally {
      setLoading(false)
    }
  }

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {}

    if (!formData.pi_name?.trim()) {
      errors.pi_name = 'PI Name is required'
    }

    if (!formData.authorized_signatory_name?.trim()) {
      errors.authorized_signatory_name = 'Authorized Signatory Name is required'
    }

    if (!formData.authorized_signatory_email?.trim()) {
      errors.authorized_signatory_email = 'Authorized Signatory Email is required'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.authorized_signatory_email)) {
      errors.authorized_signatory_email = 'Invalid email format'
    }

    if (!formData.hospital_name?.trim()) {
      errors.hospital_name = 'Hospital Name is required'
    }

    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSave = async () => {
    if (!selectedSiteId) {
      setError('No site selected')
      return
    }

    if (!validateForm()) {
      setError('Please fix validation errors before saving')
      return
    }

    setSaving(true)
    setError(null)
    setSuccess(null)

    try {
      if (profile) {
        // Update existing profile
        const response = await api.put<SiteProfile>(
          `${apiBase}/sites/${selectedSiteId}/profile`,
          formData
        )
        setProfile(response.data)
        setSuccess('Site profile updated successfully')
      } else {
        // Create new profile
        const response = await api.post<SiteProfile>(
          `${apiBase}/sites/${selectedSiteId}/profile`,
          formData
        )
        setProfile(response.data)
        setSuccess('Site profile created successfully')
      }
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save site profile')
    } finally {
      setSaving(false)
    }
  }

  const handleInputChange = (field: keyof SiteProfile, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    // Clear validation error for this field
    if (validationErrors[field]) {
      setValidationErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors[field]
        return newErrors
      })
    }
  }

  if (!selectedSiteId) {
    return (
      <div className="h-full w-full flex items-center justify-center p-8">
        <p className="text-gray-600">Please select a site to view or edit its profile</p>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="h-full w-full flex items-center justify-center p-8">
        <p className="text-gray-600">Loading site profile...</p>
      </div>
    )
  }

  return (
    <div className="h-full w-full overflow-y-auto bg-gray-50">
      <div className="p-6 max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Site Profile</h2>
            <p className="text-sm text-gray-600 mt-1">Manage site profile information</p>
          </div>

          {!profile && !loading && (
            <div className="mx-6 mt-4 p-3 bg-blue-50 border border-blue-200 rounded text-blue-700 text-sm">
              No profile found. Fill in the form below and click Save to create a new site profile.
            </div>
          )}

          {error && (
            <div className="mx-6 mt-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              {error}
            </div>
          )}

          {success && (
            <div className="mx-6 mt-4 p-3 bg-green-50 border border-green-200 rounded text-green-700 text-sm">
              {success}
            </div>
          )}

          <div className="p-6 space-y-8">
            {/* Identification Section */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 border-b border-gray-200 pb-2">
                Identification
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Site Name
                  </label>
                  <input
                    type="text"
                    value={formData.site_name || ''}
                    onChange={(e) => handleInputChange('site_name', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#168AAD] focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Hospital Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.hospital_name || ''}
                    onChange={(e) => handleInputChange('hospital_name', e.target.value)}
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-[#168AAD] focus:border-transparent ${
                      validationErrors.hospital_name ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                  {validationErrors.hospital_name && (
                    <p className="mt-1 text-sm text-red-600">{validationErrors.hospital_name}</p>
                  )}
                </div>
              </div>
            </div>

            {/* PI Details Section */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 border-b border-gray-200 pb-2">
                Principal Investigator (PI) Details
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    PI Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.pi_name || ''}
                    onChange={(e) => handleInputChange('pi_name', e.target.value)}
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-[#168AAD] focus:border-transparent ${
                      validationErrors.pi_name ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                  {validationErrors.pi_name && (
                    <p className="mt-1 text-sm text-red-600">{validationErrors.pi_name}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    PI Email
                  </label>
                  <input
                    type="email"
                    value={formData.pi_email || ''}
                    onChange={(e) => handleInputChange('pi_email', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#168AAD] focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    PI Phone
                  </label>
                  <input
                    type="tel"
                    value={formData.pi_phone || ''}
                    onChange={(e) => handleInputChange('pi_phone', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#168AAD] focus:border-transparent"
                  />
                </div>
              </div>
            </div>

            {/* Contract Details Section */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 border-b border-gray-200 pb-2">
                Contract Details
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Primary Contracting Entity
                  </label>
                  <input
                    type="text"
                    value={formData.primary_contracting_entity || ''}
                    onChange={(e) => handleInputChange('primary_contracting_entity', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#168AAD] focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Authorized Signatory Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.authorized_signatory_name || ''}
                    onChange={(e) => handleInputChange('authorized_signatory_name', e.target.value)}
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-[#168AAD] focus:border-transparent ${
                      validationErrors.authorized_signatory_name ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                  {validationErrors.authorized_signatory_name && (
                    <p className="mt-1 text-sm text-red-600">{validationErrors.authorized_signatory_name}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Authorized Signatory Email <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="email"
                    value={formData.authorized_signatory_email || ''}
                    onChange={(e) => handleInputChange('authorized_signatory_email', e.target.value)}
                    className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-[#168AAD] focus:border-transparent ${
                      validationErrors.authorized_signatory_email ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                  {validationErrors.authorized_signatory_email && (
                    <p className="mt-1 text-sm text-red-600">{validationErrors.authorized_signatory_email}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Authorized Signatory Title
                  </label>
                  <input
                    type="text"
                    value={formData.authorized_signatory_title || ''}
                    onChange={(e) => handleInputChange('authorized_signatory_title', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#168AAD] focus:border-transparent"
                  />
                </div>
              </div>
            </div>

            {/* Address Section */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 border-b border-gray-200 pb-2">
                Address
              </h3>
              <div className="grid grid-cols-1 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Address Line 1
                  </label>
                  <input
                    type="text"
                    value={formData.address_line_1 || ''}
                    onChange={(e) => handleInputChange('address_line_1', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#168AAD] focus:border-transparent"
                  />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      City
                    </label>
                    <input
                      type="text"
                      value={formData.city || ''}
                      onChange={(e) => handleInputChange('city', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#168AAD] focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      State
                    </label>
                    <input
                      type="text"
                      value={formData.state || ''}
                      onChange={(e) => handleInputChange('state', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#168AAD] focus:border-transparent"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Country
                    </label>
                    <input
                      type="text"
                      value={formData.country || ''}
                      onChange={(e) => handleInputChange('country', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#168AAD] focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Postal Code
                    </label>
                    <input
                      type="text"
                      value={formData.postal_code || ''}
                      onChange={(e) => handleInputChange('postal_code', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#168AAD] focus:border-transparent"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Operational Contacts Section */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 border-b border-gray-200 pb-2">
                Operational Contacts
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Site Coordinator Name
                  </label>
                  <input
                    type="text"
                    value={formData.site_coordinator_name || ''}
                    onChange={(e) => handleInputChange('site_coordinator_name', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#168AAD] focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Site Coordinator Email
                  </label>
                  <input
                    type="email"
                    value={formData.site_coordinator_email || ''}
                    onChange={(e) => handleInputChange('site_coordinator_email', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#168AAD] focus:border-transparent"
                  />
                </div>
              </div>
            </div>

            {/* Save Button */}
            <div className="flex justify-end pt-4 border-t border-gray-200">
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-6 py-2 bg-[#168AAD] text-white rounded-md font-medium hover:bg-[#0f6b85] focus:outline-none focus:ring-2 focus:ring-[#168AAD] focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SiteProfileTab
