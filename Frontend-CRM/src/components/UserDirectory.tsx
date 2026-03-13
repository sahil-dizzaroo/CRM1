import React, { useState, useEffect } from 'react'
import { api } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import Profile from './Profile'

interface UserDirectoryProps {
  apiBase: string
  onBack?: () => void
}

interface User {
  user_id: string
  name?: string
  email?: string
  role?: string
  is_privileged?: boolean
}

const UserDirectory: React.FC<UserDirectoryProps> = ({ apiBase, onBack }) => {
  const { token } = useAuth()
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null)

  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get<User[]>('/users', {
        params: { limit: 500, offset: 0 }
      })
      setUsers(response.data)
    } catch (err: any) {
      console.error('Failed to load users:', err)
      setError(err.response?.data?.detail || 'Failed to load users')
    } finally {
      setLoading(false)
    }
  }

  const filteredUsers = users.filter(user => {
    if (!searchQuery.trim()) return true
    const query = searchQuery.toLowerCase()
    return (
      (user.user_id && user.user_id.toLowerCase().includes(query)) ||
      (user.name && user.name.toLowerCase().includes(query)) ||
      (user.email && user.email.toLowerCase().includes(query))
    )
  })

  if (selectedUserId) {
    return (
      <Profile
        apiBase={apiBase}
        userId={selectedUserId}
        onBack={() => setSelectedUserId(null)}
      />
    )
  }

  return (
    <div className="h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex flex-col overflow-hidden">
      <div className="max-w-7xl mx-auto w-full flex flex-col h-full p-6">
        {/* Header */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6 flex-shrink-0">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-800 mb-2">👥 User Directory</h1>
              <p className="text-gray-600">View all users and their profiles</p>
            </div>
            {onBack && (
              <button
                onClick={onBack}
                className="px-5 py-2.5 bg-dizzaroo-deep-blue text-white rounded-xl hover:bg-dizzaroo-blue-green font-semibold transition shadow-lg"
              >
                ← Back to Inbox
              </button>
            )}
          </div>
        </div>

        {/* Search Bar */}
        <div className="bg-white rounded-xl shadow-lg p-4 mb-6 flex-shrink-0">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search users by name, email, or user ID..."
            className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-dizzaroo-deep-blue focus:border-dizzaroo-deep-blue"
          />
        </div>

        {/* Users List */}
        <div className="bg-white rounded-xl shadow-lg flex-1 min-h-0 overflow-hidden flex flex-col">
          <div className="p-6 border-b border-gray-200 flex-shrink-0">
            <h2 className="text-xl font-bold text-gray-800">
              Users ({filteredUsers.length})
            </h2>
          </div>
          
          <div className="flex-1 overflow-y-auto min-h-0" style={{ WebkitOverflowScrolling: 'touch' }}>
            {loading && (
              <div className="text-center py-12">
                <div className="animate-spin text-4xl mb-4">⏳</div>
                <p className="text-gray-600">Loading users...</p>
              </div>
            )}

            {error && (
              <div className="text-center py-12">
                <p className="text-red-600">{error}</p>
                <button
                  onClick={loadUsers}
                  className="mt-4 px-4 py-2 bg-dizzaroo-deep-blue text-white rounded-xl hover:bg-dizzaroo-blue-green"
                >
                  Retry
                </button>
              </div>
            )}

            {!loading && !error && filteredUsers.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                <p className="text-lg">No users found.</p>
                {searchQuery && (
                  <p className="text-sm mt-2">Try a different search query.</p>
                )}
              </div>
            )}

            {!loading && !error && filteredUsers.length > 0 && (
              <div className="divide-y divide-gray-200">
                {filteredUsers.map(user => (
                  <div
                    key={user.user_id}
                    onClick={() => setSelectedUserId(user.user_id)}
                    className="p-6 hover:bg-dizzaroo-deep-blue/10 cursor-pointer transition rounded-xl"
                  >
                    <div className="flex justify-between items-center">
                      <div className="flex-1">
                        <h3 className="text-lg font-bold text-gray-800 mb-1">
                          {user.name || user.user_id}
                        </h3>
                        <div className="flex gap-4 text-sm text-gray-600">
                          <span>ID: {user.user_id}</span>
                          {user.email && <span>Email: {user.email}</span>}
                          {user.role && (
                            <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-semibold">
                              {user.role}
                            </span>
                          )}
                          {user.is_privileged && (
                            <span className="px-2 py-1 bg-dizzaroo-soft-green/20 text-dizzaroo-deep-blue rounded-xl text-xs font-semibold">
                              Privileged
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="text-dizzaroo-deep-blue font-semibold">
                        View Profile →
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default UserDirectory

