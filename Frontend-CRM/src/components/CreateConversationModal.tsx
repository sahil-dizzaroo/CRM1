import React, { useState, FormEvent, ChangeEvent } from 'react'

interface CreateConversationModalProps {
  onClose: () => void
  onSubmit: (data: {
    participant_phone?: string
    participant_email?: string
    participant_emails?: string[]
    subject?: string
    study_id?: string
    site_id?: string
  }) => void
  loading: boolean
  studyName?: string
  siteName?: string
}

const CreateConversationModal: React.FC<CreateConversationModalProps> = ({ onClose, onSubmit, loading, studyName, siteName }) => {
  const [formData, setFormData] = useState({
    participant_phone: '',
    participant_emails: [''] as string[],
    subject: '',
    study_id: ''
  })

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    // New conversations no longer require participant email/phone.
    // Email delivery is driven by @email mentions in message bodies.
    onSubmit({
      subject: formData.subject,
      study_id: formData.study_id
    })
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Create New Conversation</h2>
          <button 
            className="text-2xl text-gray-500 hover:text-gray-700"
            onClick={onClose}
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {studyName && siteName && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
              <p className="text-sm text-blue-800">
                <strong>Creating conversation for:</strong><br />
                📊 {studyName} → 🏥 {siteName}
              </p>
            </div>
          )}
          {/* Study ID hidden - automatically using selected study from global selector */}

          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-gray-700">Subject</label>
            <input
              type="text"
              name="subject"
              value={formData.subject}
              onChange={handleChange}
              placeholder="Conversation subject"
              className="px-3 py-2 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue"
            />
          </div>

          {/* Participant phone / email inputs were removed because email delivery now relies on @email mentions
              inside message bodies, not on static participant fields at conversation creation time. */}

          <div className="flex gap-3 justify-end pt-2">
            <button 
              type="button" 
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition"
              onClick={onClose}
            >
              Cancel
            </button>
            <button 
              type="submit" 
              className="px-4 py-2 bg-dizzaroo-deep-blue text-white rounded-xl hover:bg-dizzaroo-blue-green disabled:opacity-50 transition"
              disabled={loading}
            >
              {loading ? 'Creating...' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default CreateConversationModal

