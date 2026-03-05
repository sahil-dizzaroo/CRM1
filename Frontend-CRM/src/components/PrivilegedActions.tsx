import React, { useState, useEffect } from 'react'
import { api } from '../lib/api'
import { Conversation, ConversationAccess } from '../types'

interface User {
  user_id: string
  name?: string
  email?: string
}

interface PrivilegedActionsProps {
  conversation: Conversation
  currentUserId: string
  apiBase: string
  onUpdate: () => void
}

const PrivilegedActions: React.FC<PrivilegedActionsProps> = ({
  conversation,
  currentUserId,
  apiBase,
  onUpdate
}) => {
  const [showModal, setShowModal] = useState(false)
  const [showConfidentialModal, setShowConfidentialModal] = useState(false)
  const [accessList, setAccessList] = useState<ConversationAccess[]>([])
  const [allUsers, setAllUsers] = useState<User[]>([])
  const [selectedUserIds, setSelectedUserIds] = useState<string[]>([])
  const [selectedUserId, setSelectedUserId] = useState('')
  const [accessType, setAccessType] = useState<'read' | 'write' | 'admin'>('read')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const canManage =
    conversation.created_by === currentUserId ||
    (accessList.length > 0 &&
      accessList.some(
        access =>
          access.user_id === currentUserId && access.access_type === 'admin'
      ))

  useEffect(() => {
    loadAccessList()
  }, [conversation.id])

  useEffect(() => {
    if (showModal) {
      loadAccessList()
    }
  }, [showModal, conversation.id])

  useEffect(() => {
    if (showConfidentialModal) {
      loadAllUsers()
    }
  }, [showConfidentialModal])

  const loadAllUsers = async () => {
    try {
      const response = await api.get(`${apiBase}/users`, {
        params: { limit: 500 }
      })
      setAllUsers(response.data)
    } catch (err) {
      console.error('Failed to load users:', err)
      setError('Failed to load users')
    }
  }

  const loadAccessList = async () => {
    try {
      const response = await api.get(
        `${apiBase}/conversations/${conversation.id}/access`
      )
      setAccessList(response.data)
    } catch (err) {
      console.error('Failed to load access list:', err)
    }
  }

  const handleMarkConfidentialClick = () => {
    if (conversation.is_confidential === 'true') {
      handleMakePublic()
    } else {
      setShowConfidentialModal(true)
      setSelectedUserIds([])
    }
  }

  const handleMakePublic = async () => {
    try {
      setLoading(true)
      await api.patch(
        `${apiBase}/conversations/${conversation.id}/access`,
        { is_confidential: false }
      )
      onUpdate()
      alert('Conversation marked as public')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update access')
    } finally {
      setLoading(false)
    }
  }

  const handleConfirmConfidential = async () => {
    if (selectedUserIds.length === 0) {
      setError('Please select at least one user to grant access')
      return
    }

    try {
      setLoading(true)
      setError(null)

      for (const userId of selectedUserIds) {
        try {
          await api.post(
            `${apiBase}/conversations/${conversation.id}/grant-access`,
            {
              user_id: userId,
              access_type: 'read'
            }
          )
        } catch (err) {
          console.error(`Failed to grant access to ${userId}:`, err)
        }
      }

      await api.patch(
        `${apiBase}/conversations/${conversation.id}/access`,
        { is_confidential: true }
      )

      setShowConfidentialModal(false)
      setSelectedUserIds([])
      onUpdate()
      alert(
        `Conversation marked as confidential. Access granted to ${selectedUserIds.length} user(s).`
      )
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to mark as confidential')
    } finally {
      setLoading(false)
    }
  }

  const toggleUserSelection = (userId: string) => {
    setSelectedUserIds(prev =>
      prev.includes(userId)
        ? prev.filter(id => id !== userId)
        : [...prev, userId]
    )
  }

  const handleGrantAccess = async () => {
    if (!selectedUserId.trim()) {
      setError('Please enter a user ID')
      return
    }

    try {
      setLoading(true)
      setError(null)

      await api.post(
        `${apiBase}/conversations/${conversation.id}/grant-access`,
        {
          user_id: selectedUserId,
          access_type: accessType
        }
      )

      setSelectedUserId('')
      loadAccessList()
      onUpdate()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to grant access')
    } finally {
      setLoading(false)
    }
  }

  const handleRevokeAccess = async (userId: string) => {
    if (!confirm('Are you sure you want to revoke access for this user?')) {
      return
    }

    try {
      setLoading(true)
      await api.delete(
        `${apiBase}/conversations/${conversation.id}/revoke-access/${userId}`
      )
      loadAccessList()
      onUpdate()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to revoke access')
    } finally {
      setLoading(false)
    }
  }

  const showMarkConfidential =
    canManage && conversation.is_confidential !== 'true'
  const showMakePublic =
    canManage && conversation.is_confidential === 'true'


  return (
    <>
      <div className="flex gap-2">
        {showMakePublic ? (
          <button
            onClick={handleMakePublic}
            className="px-3 py-1.5 rounded-lg text-xs font-medium transition bg-yellow-500 text-white hover:bg-yellow-600 disabled:opacity-50"
            disabled={loading}
            title="Make this conversation public"
          >
            🔓 Make Public
          </button>
        ) : showMarkConfidential ? (
          <button
            onClick={handleMarkConfidentialClick}
            className="px-3 py-1.5 rounded-xl text-xs font-medium transition bg-dizzaroo-deep-blue text-white hover:bg-dizzaroo-blue-green disabled:opacity-50"
            disabled={loading}
          >
            🔐 Mark Confidential
          </button>
        ) : null}
        <button
          onClick={() => setShowModal(true)}
          className="px-3 py-1.5 bg-dizzaroo-blue-green text-white rounded-xl text-xs font-medium hover:bg-dizzaroo-deep-blue transition"
        >
          👥 Manage Access
        </button>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] flex flex-col">
            {/* Header */}
            <div className="bg-dizzaroo-deep-blue text-white px-6 py-4 rounded-t-2xl">
              <h2 className="text-xl font-bold">Manage Conversation Access</h2>
              <p className="text-sm opacity-90 mt-1">{conversation.subject || 'Conversation'}</p>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {/* Current Status */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-semibold text-gray-700 mb-2">Current Status</h3>
                <div className="flex gap-2 flex-wrap">
                  <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                    conversation.is_confidential === 'true' 
                      ? 'bg-red-100 text-red-700' 
                      : 'bg-green-100 text-green-700'
                  }`}>
                    {conversation.is_confidential === 'true' ? '🔐 Confidential' : '🌐 Public'}
                  </span>
                  <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                    conversation.is_restricted === 'true' 
                      ? 'bg-yellow-100 text-yellow-700' 
                      : 'bg-gray-100 text-gray-700'
                  }`}>
                    {conversation.is_restricted === 'true' ? '🔒 Restricted' : 'Open'}
                  </span>
                </div>
              </div>

              {/* Grant Access */}
              <div className="border-2 border-gray-200 rounded-lg p-4">
                <h3 className="font-semibold text-gray-700 mb-3">Grant Access</h3>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      User ID
                    </label>
                    <input
                      type="text"
                      value={selectedUserId}
                      onChange={(e) => setSelectedUserId(e.target.value)}
                      className="w-full px-3 py-2 border-2 border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue"
                      placeholder="Enter user ID or email"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Access Type
                    </label>
                    <select
                      value={accessType}
                      onChange={(e) => setAccessType(e.target.value as 'read' | 'write' | 'admin')}
                      className="w-full px-3 py-2 border-2 border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue text-gray-900 bg-white"
                    >
                      <option value="read">Read Only</option>
                      <option value="write">Read & Write</option>
                      <option value="admin">Admin (Full Access)</option>
                    </select>
                  </div>
                  <button
                    onClick={handleGrantAccess}
                    disabled={loading || !selectedUserId.trim()}
                    className="w-full px-4 py-2 bg-dizzaroo-deep-blue text-white rounded-xl font-semibold hover:bg-dizzaroo-blue-green transition disabled:opacity-50"
                  >
                    Grant Access
                  </button>
                </div>
              </div>

              {/* Access List */}
              <div>
                <h3 className="font-semibold text-gray-700 mb-3">Users with Access</h3>
                {accessList.length === 0 ? (
                  <p className="text-gray-500 text-sm">No explicit access grants</p>
                ) : (
                  <div className="space-y-2">
                    {accessList.map((access) => (
                      <div
                        key={access.id}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                      >
                        <div>
                          <div className="font-medium text-sm text-gray-800">{access.user_id}</div>
                          <div className="text-xs text-gray-500">
                            {access.access_type} • Granted by {access.granted_by || 'System'}
                          </div>
                        </div>
                        <button
                          onClick={() => handleRevokeAccess(access.user_id)}
                          disabled={loading}
                          className="px-3 py-1 bg-red-500 text-white text-xs rounded hover:bg-red-600 transition disabled:opacity-50"
                        >
                          Revoke
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {error && (
                <div className="bg-red-50 border-2 border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="border-t-2 border-gray-200 px-6 py-4 flex justify-end">
              <button
                onClick={() => {
                  setShowModal(false)
                  setError(null)
                }}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300 transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Mark Confidential Modal */}
      {showConfidentialModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] flex flex-col">
            {/* Header */}
            <div className="bg-gradient-to-r from-red-600 to-orange-600 text-white px-6 py-4 rounded-t-2xl">
              <h2 className="text-xl font-bold">Mark Conversation as Confidential</h2>
              <p className="text-sm opacity-90 mt-1">{conversation.subject || 'Conversation'}</p>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              <div className="bg-yellow-50 border-2 border-yellow-200 p-4 rounded-lg">
                <p className="text-sm text-yellow-800 font-semibold">
                  ⚠️ Select users who should have access to this confidential conversation.
                </p>
              </div>

              {/* User Selection */}
              <div className="border-2 border-gray-200 rounded-lg p-4">
                <h3 className="font-semibold text-gray-700 mb-3">
                  Select Users ({selectedUserIds.length} selected)
                </h3>
                    <div className="max-h-64 overflow-y-auto space-y-2">
                      {allUsers.length === 0 ? (
                        <p className="text-gray-500 text-sm">Loading users...</p>
                      ) : (
                        allUsers
                          .filter(user => user.user_id !== currentUserId) // Filter out current user (they already have access)
                          .map((user) => (
                            <div
                              key={user.user_id}
                              className={`flex items-center gap-3 p-3 rounded-lg border-2 cursor-pointer transition ${
                                selectedUserIds.includes(user.user_id)
                                  ? 'bg-dizzaroo-deep-blue/10 border-dizzaroo-deep-blue'
                                  : 'bg-white border-gray-200 hover:border-dizzaroo-deep-blue/50'
                              }`}
                              onClick={() => toggleUserSelection(user.user_id)}
                            >
                              <input
                                type="checkbox"
                                checked={selectedUserIds.includes(user.user_id)}
                                onChange={() => toggleUserSelection(user.user_id)}
                                className="w-4 h-4 text-dizzaroo-deep-blue rounded focus:ring-dizzaroo-deep-blue"
                              />
                              <div className="flex-1">
                                <div className="font-medium text-sm text-gray-800">
                                  {user.name || user.user_id}
                                </div>
                                {user.email && (
                                  <div className="text-xs text-gray-500">{user.email}</div>
                                )}
                              </div>
                            </div>
                          ))
                      )}
                    </div>
              </div>

              {error && (
                <div className="bg-red-50 border-2 border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="border-t-2 border-gray-200 px-6 py-4 flex justify-between">
              <button
                onClick={() => {
                  setShowConfidentialModal(false)
                  setSelectedUserIds([])
                  setError(null)
                }}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300 transition"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmConfidential}
                disabled={loading || selectedUserIds.length === 0}
                className="px-4 py-2 bg-gradient-to-r from-red-600 to-orange-600 text-white rounded-lg font-semibold hover:from-red-700 hover:to-orange-700 transition disabled:opacity-50"
              >
                {loading ? 'Processing...' : `Mark Confidential (${selectedUserIds.length} users)`}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default PrivilegedActions

