import React, { useState, useEffect, useRef } from 'react'
import { api } from '../lib/api'
import { User } from '../types'

interface UserPickerProps {
  selectedUserEmails: string[]
  onSelectionChange: (emails: string[]) => void
  siteId?: string
  excludeEmails?: string[]  // Emails to exclude from selection (e.g., current user if already included)
  placeholder?: string
  className?: string
}

const UserPicker: React.FC<UserPickerProps> = ({
  selectedUserEmails,
  onSelectionChange,
  siteId,
  excludeEmails = [],
  placeholder = 'Search and select users...',
  className = ''
}) => {
  const [users, setUsers] = useState<User[]>([])
  const [filteredUsers, setFilteredUsers] = useState<User[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadUsers()
  }, [siteId])

  useEffect(() => {
    // Filter users based on search query
    if (!searchQuery.trim()) {
      setFilteredUsers(users.filter(u => !excludeEmails.includes(u.email?.toLowerCase() || '')))
    } else {
      const query = searchQuery.toLowerCase()
      setFilteredUsers(
        users.filter(u => {
          const email = u.email?.toLowerCase() || ''
          const name = u.name?.toLowerCase() || ''
          const userId = u.user_id?.toLowerCase() || ''
          return (
            (email.includes(query) || name.includes(query) || userId.includes(query)) &&
            !excludeEmails.includes(email)
          )
        })
      )
    }
  }, [searchQuery, users, excludeEmails])

  useEffect(() => {
    // Close dropdown when clicking outside
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const loadUsers = async () => {
    setLoading(true)
    try {
      const params: any = { limit: 500, offset: 0 }
      if (siteId) {
        params.site_id = siteId
      }
      const response = await api.get<User[]>('/users', { params })
      setUsers(response.data || [])
    } catch (error) {
      console.error('Failed to load users:', error)
      setUsers([])
    } finally {
      setLoading(false)
    }
  }

  const toggleUser = (user: User) => {
    const email = user.email?.toLowerCase() || ''
    if (!email) return

    if (selectedUserEmails.includes(email)) {
      // Remove user
      onSelectionChange(selectedUserEmails.filter(e => e !== email))
    } else {
      // Add user
      onSelectionChange([...selectedUserEmails, email])
    }
  }

  const removeUser = (email: string) => {
    onSelectionChange(selectedUserEmails.filter(e => e !== email))
  }

  const getSelectedUsers = () => {
    return users.filter(u => selectedUserEmails.includes(u.email?.toLowerCase() || ''))
  }

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {/* Selected Users Display */}
      {getSelectedUsers().length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2">
          {getSelectedUsers().map(user => (
            <div
              key={user.email}
              className="flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium"
            >
              <span>{user.name || user.email}</span>
              <button
                onClick={() => removeUser(user.email?.toLowerCase() || '')}
                className="text-blue-600 hover:text-blue-800 font-bold"
                type="button"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Search Input */}
      <div className="relative">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => {
            setSearchQuery(e.target.value)
            setIsOpen(true)
          }}
          onFocus={() => setIsOpen(true)}
          placeholder={placeholder}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue text-sm"
        />
        {loading && (
          <div className="absolute right-3 top-2.5">
            <span className="animate-spin text-gray-400">⏳</span>
          </div>
        )}
      </div>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {filteredUsers.length === 0 ? (
            <div className="px-4 py-3 text-sm text-gray-500 text-center">
              {loading ? 'Loading users...' : searchQuery ? 'No users found' : 'Start typing to search'}
            </div>
          ) : (
            <div className="py-1">
              {filteredUsers.map(user => {
                const email = user.email?.toLowerCase() || ''
                const isSelected = selectedUserEmails.includes(email)
                return (
                  <div
                    key={user.user_id}
                    onClick={() => toggleUser(user)}
                    className={`px-4 py-2 cursor-pointer hover:bg-gray-100 flex items-center justify-between ${
                      isSelected ? 'bg-blue-50' : ''
                    }`}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-gray-900 truncate">
                        {user.name || user.user_id}
                      </div>
                      <div className="text-xs text-gray-500 truncate">{user.email}</div>
                      {user.role && (
                        <div className="text-xs text-gray-400 mt-0.5">{user.role}</div>
                      )}
                    </div>
                    {isSelected && (
                      <span className="ml-2 text-blue-600 font-bold">✓</span>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default UserPicker
