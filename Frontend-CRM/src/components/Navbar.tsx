import React, { useState, useRef, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useStudySite } from '../contexts/StudySiteContext'

interface NavbarProps {
  onModeChange?: (mode: string) => void
  currentMode?: string
  onNavigateToUsers?: () => void
  sidebarProps?: {
    onCreateConversation?: () => void
    onCreateThread?: () => void
  }
}

// Icons as simple SVG components (replacing lucide-react)
const MenuIcon = ({ size = 20 }: { size?: number }) => (
  <svg width={size} height={size} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
  </svg>
)

const ChevronDownIcon = ({ size = 14, className = '' }: { size?: number; className?: string }) => (
  <svg width={size} height={size} fill="none" stroke="currentColor" viewBox="0 0 24 24" className={className}>
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
  </svg>
)

const GlobeIcon = ({ size = 13 }: { size?: number }) => (
  <svg width={size} height={size} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
)

const UsersIcon = ({ size = 13 }: { size?: number }) => (
  <svg width={size} height={size} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
  </svg>
)

const ActivityIcon = ({ size = 13 }: { size?: number }) => (
  <svg width={size} height={size} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
)

const DatabaseIcon = ({ size = 13 }: { size?: number }) => (
  <svg width={size} height={size} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
  </svg>
)

const LogOutIcon = ({ size = 16 }: { size?: number }) => (
  <svg width={size} height={size} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
  </svg>
)

const SettingsIcon = ({ size = 16 }: { size?: number }) => (
  <svg width={size} height={size} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
)

const Navbar: React.FC<NavbarProps> = ({ 
  onModeChange, 
  currentMode = 'conversations',
  onNavigateToUsers,
  sidebarProps,
}) => {
  const { user, logout } = useAuth()
  const {
    selectedStudyId,
    selectedSiteId,
    setSelectedStudyId,
    setSelectedSiteId,
    studies,
    filteredSites,
  } = useStudySite()
  const [isOpen, setIsOpen] = useState(false)
  const [showUserMenu, setShowUserMenu] = useState(false)
  const userMenuRef = useRef<HTMLDivElement>(null)
  
  // Only show mode buttons and study selector when both study and site are selected
  const showNavigationControls = selectedStudyId && selectedSiteId

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleModeClick = (mode: string) => {
    if (onModeChange) {
      onModeChange(mode)
    }
  }

  const getUserInitials = () => {
    if (user?.name) {
      return user.name
        .split(' ')
        .map(n => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    }
    if (user?.email) {
      return user.email[0].toUpperCase()
    }
    return 'U'
  }

  const handleLogout = () => {
    logout()
    setShowUserMenu(false)
  }

  const [showMoreDropdown, setShowMoreDropdown] = useState(false)
  const moreDropdownRef = useRef<HTMLDivElement>(null)

  const [showConversationsDropdown, setShowConversationsDropdown] = useState(false)
  const conversationsDropdownRef = useRef<HTMLDivElement>(null)
  const conversationsTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const [showSitesDropdown, setShowSitesDropdown] = useState(false)
  const sitesDropdownRef = useRef<HTMLDivElement>(null)
  const sitesTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  // Close more dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node
      
      // Check if click is outside each dropdown
      // Only close if the dropdown is actually open and click is truly outside
      if (moreDropdownRef.current && showMoreDropdown && !moreDropdownRef.current.contains(target)) {
        setShowMoreDropdown(false)
      }
      if (conversationsDropdownRef.current && showConversationsDropdown && !conversationsDropdownRef.current.contains(target)) {
        setShowConversationsDropdown(false)
      }
      if (sitesDropdownRef.current && showSitesDropdown && !sitesDropdownRef.current.contains(target)) {
        setShowSitesDropdown(false)
      }
    }
    // Use 'mousedown' with a small delay to allow button clicks to complete first
    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      // Cleanup timeouts on unmount
      if (conversationsTimeoutRef.current) {
        clearTimeout(conversationsTimeoutRef.current)
      }
      if (sitesTimeoutRef.current) {
        clearTimeout(sitesTimeoutRef.current)
      }
    }
  }, [showMoreDropdown, showConversationsDropdown, showSitesDropdown])

  // CRM Mode buttons (MAIN MENU) - 3 primary items + More dropdown
  const primaryModes = [
    { id: 'conversations', label: 'Conversations', icon: '💬' },
    { id: 'sites', label: 'Sites', icon: '📊' },
    { id: 'users', label: 'Users', icon: '👥' },
  ]

  // Conversations dropdown items
  const conversationsItems = [
    { id: 'conversations', label: 'Conversations', icon: '💬' },
    { id: 'threads', label: 'Threads', icon: '🧵' },
  ]

  // Sites dropdown items
  const sitesItems = [
    { id: 'site-status', label: 'Site Status', icon: '📊' },
    { id: 'logistics', label: 'Logistics', icon: '📦' },
    { id: 'monitoring', label: 'Monitoring', icon: '🔍' },
    { id: 'tasks', label: 'Tasks', icon: '✅' },
    { id: 'documents', label: 'Documents', icon: '📁' },
    { id: 'agreements', label: 'Agreement', icon: '📄' },
    { id: 'study-setup', label: 'Study Setup', icon: '⚙️' },
    { id: 'site-profile', label: 'Site Profile', icon: '📋' },
  ]

  // Secondary items for More dropdown - hide non-CRM tabs
  const moreItems = [
    { id: 'ask', label: 'Ask Me Anything', icon: '⚙️' },
    // Non-CRM tabs hidden: Tasks, Monitoring, Logistics
  ]

  // Check if conversations or any of its sub-items are active
  const isConversationsActive = () => {
    return currentMode === 'conversations' || currentMode === 'threads'
  }

  // Check if sites or any of its sub-items are active
  const isSitesActive = () => {
    return currentMode === 'sites' || 
           currentMode === 'site-status' ||
           currentMode === 'logistics' ||
           currentMode === 'monitoring' ||
           currentMode === 'tasks' ||
           currentMode === 'documents' ||
           currentMode === 'agreements' ||
           currentMode === 'study-setup' ||
           currentMode === 'site-profile'
  }

  return (
    <nav className="h-16 flex items-center px-4 overflow-visible relative z-[200]" style={{ 
      background: 'linear-gradient(to right, rgba(22, 138, 173, 0.92), rgba(118, 200, 147, 0.92))',
      backdropFilter: 'blur(12px) saturate(180%)',
      WebkitBackdropFilter: 'blur(12px) saturate(180%)',
      boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.12), 0 0 0 1px rgba(255, 255, 255, 0.2) inset',
      borderBottom: '1px solid rgba(255, 255, 255, 0.15)',
    }}>
      <div className="flex items-center justify-between gap-2 w-full">
        <div className="flex items-center flex-shrink-0 min-w-0 overflow-visible">
          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="lg:hidden p-2 rounded-md text-white hover:text-white hover:bg-white/20 mr-1 sm:mr-2 shrink-0"
          >
            <MenuIcon size={20} />
          </button>

          {/* Mobile Sheet Menu */}
          {isOpen && (
            <div className="fixed inset-0 z-50 lg:hidden">
              <div 
                className="fixed inset-0 bg-black/50" 
                onClick={() => setIsOpen(false)}
              />
              <div className="fixed left-0 top-0 bottom-0 w-[280px] sm:w-[320px] bg-gradient-to-b from-[#168AAD] to-[#76C893] shadow-xl overflow-y-auto">
                <div className="p-4 border-b border-white/20">
                  <div className="flex items-center gap-2 mb-2">
                    <img
                      src="/dizzaroo_logo.png"
                      alt="Dizzaroo"
                      className="h-6 w-auto object-contain"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement
                        target.style.display = 'none'
                      }}
                    />
                    <h2 className="text-xl font-bold text-white">Dizzaroo CRM</h2>
                  </div>
                </div>
                <div className="p-4 space-y-4">
                  {/* Mobile menu content removed - study selection happens on main page */}
                </div>
              </div>
            </div>
          )}

          {/* Logo + Brand Name */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <img
              src="/dizzaroo_logo.png"
              alt="Dizzaroo"
              className="h-7 w-auto object-contain"
              style={{ maxHeight: '28px', height: 'auto', width: 'auto' }}
              onError={(e) => {
                const target = e.target as HTMLImageElement
                target.style.display = 'none'
                const parent = target.parentElement
                if (parent && !parent.querySelector('.logo-fallback')) {
                  const fallback = document.createElement('div')
                  fallback.className = 'logo-fallback h-6 w-6 bg-white/20 rounded flex items-center justify-center'
                  fallback.innerHTML = '<span class="text-white font-bold text-xs">D</span>'
                  parent.insertBefore(fallback, target)
                }
              }}
            />
            <div className="text-sm font-semibold text-white">
              CRM
            </div>
          </div>

          {/* Primary Navigation - only when study & site selected */}
          {showNavigationControls && (
            <div className="hidden md:flex items-center gap-0.5 ml-6">
              {/* Conversations Dropdown */}
              <div 
                className="relative" 
                ref={conversationsDropdownRef}
                onMouseEnter={() => {
                  // Clear any pending close timeout
                  if (conversationsTimeoutRef.current) {
                    clearTimeout(conversationsTimeoutRef.current)
                    conversationsTimeoutRef.current = null
                  }
                  setShowConversationsDropdown(true)
                  setShowSitesDropdown(false)
                  setShowMoreDropdown(false)
                }}
                onMouseLeave={() => {
                  // Use a delay to allow mouse to move to dropdown
                  conversationsTimeoutRef.current = setTimeout(() => {
                    setShowConversationsDropdown(false)
                    conversationsTimeoutRef.current = null
                  }, 200)
                }}
              >
                <button
                  className={`px-3 py-1.5 text-sm font-medium transition-all relative flex items-center gap-1 ${
                    isConversationsActive()
                      ? 'text-white'
                      : 'text-white/80 hover:text-white'
                  }`}
                  onClick={(e) => {
                    e.stopPropagation()
                    e.preventDefault()
                    setShowConversationsDropdown(!showConversationsDropdown)
                    setShowSitesDropdown(false)
                    setShowMoreDropdown(false)
                  }}
                  onMouseDown={(e) => {
                    // Prevent the click outside handler from firing immediately
                    e.stopPropagation()
                  }}
                >
                  Conversations
                  <ChevronDownIcon size={12} className={`transition-transform ${showConversationsDropdown ? 'rotate-180' : ''}`} />
                  {isConversationsActive() && (
                    <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-white rounded-full"></span>
                  )}
                </button>
                
                {showConversationsDropdown && (
                  <div 
                    className="absolute top-full left-0 z-[100]"
                    onMouseEnter={() => {
                      // Clear any pending close timeout
                      if (conversationsTimeoutRef.current) {
                        clearTimeout(conversationsTimeoutRef.current)
                        conversationsTimeoutRef.current = null
                      }
                      setShowConversationsDropdown(true)
                    }}
                    onMouseLeave={() => {
                      // Small delay before closing
                      conversationsTimeoutRef.current = setTimeout(() => {
                        setShowConversationsDropdown(false)
                        conversationsTimeoutRef.current = null
                      }, 200)
                    }}
                  >
                    <div className="bg-white rounded-lg shadow-xl border border-gray-200 py-1 min-w-[180px]">
                      {conversationsItems.map((item) => {
                        const isActive = currentMode === item.id
                        return (
                          <button
                            key={item.id}
                            className={`w-full text-left px-4 py-2 text-sm transition-colors flex items-center gap-2 ${
                              isActive
                                ? 'bg-[#168AAD]/10 text-[#168AAD] font-medium'
                                : 'text-gray-700 hover:bg-gray-50'
                            }`}
                            onClick={(e) => {
                              e.stopPropagation()
                              handleModeClick(item.id)
                              setShowConversationsDropdown(false)
                            }}
                            onMouseDown={(e) => {
                              e.stopPropagation()
                            }}
                          >
                            <span>{item.icon}</span>
                            <span>{item.label}</span>
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )}
              </div>

              {/* Sites Dropdown */}
              <div
                className="relative"
                ref={sitesDropdownRef}
                onMouseEnter={() => {
                  if (sitesTimeoutRef.current) {
                    clearTimeout(sitesTimeoutRef.current)
                    sitesTimeoutRef.current = null
                  }
                  setShowSitesDropdown(true)
                  setShowConversationsDropdown(false)
                  setShowMoreDropdown(false)
                }}
                onMouseLeave={() => {
                  sitesTimeoutRef.current = setTimeout(() => {
                    setShowSitesDropdown(false)
                    sitesTimeoutRef.current = null
                  }, 150)
                }}
              >
                <button
                  className={`px-3 py-1.5 text-sm font-medium transition-all relative flex items-center gap-1 ${
                    isSitesActive()
                      ? 'text-white'
                      : 'text-white/80 hover:text-white'
                  }`}
                  onClick={(e) => {
                    e.stopPropagation()
                    setShowSitesDropdown(prev => !prev)
                    setShowConversationsDropdown(false)
                    setShowMoreDropdown(false)
                  }}
                >
                  Sites
                  <ChevronDownIcon size={12} />
                  {isSitesActive() && (
                    <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-white rounded-full" />
                  )}
                </button>

                {showSitesDropdown && (
                  <div
                    className="absolute top-full left-0 z-[100] bg-white border border-gray-200 rounded-lg shadow-xl overflow-hidden"
                    style={{ minWidth: '180px' }}
                    onMouseEnter={() => {
                      if (sitesTimeoutRef.current) {
                        clearTimeout(sitesTimeoutRef.current)
                        sitesTimeoutRef.current = null
                      }
                    }}
                    onMouseLeave={() => {
                      sitesTimeoutRef.current = setTimeout(() => {
                        setShowSitesDropdown(false)
                        sitesTimeoutRef.current = null
                      }, 150)
                    }}
                    onMouseDown={(e) => e.stopPropagation()}
                  >
                    {sitesItems.map((item) => (
                      <button
                        key={item.id}
                        type="button"
                        className={`block w-full text-left px-4 py-2 text-sm ${
                          currentMode === item.id
                            ? 'bg-[#168AAD]/10 text-[#168AAD] font-medium'
                            : 'text-gray-700 hover:bg-gray-50'
                        }`}
                        onClick={(e) => {
                          e.stopPropagation()
                          handleModeClick(item.id)
                          setShowSitesDropdown(false)
                        }}
                        onMouseDown={(e) => e.stopPropagation()}
                      >
                        <span className="mr-2">{item.icon}</span>
                        {item.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Users Button (no dropdown) */}
              {primaryModes.map((mode) => {
                if (mode.id === 'conversations' || mode.id === 'sites') return null
                const isActive = currentMode === mode.id
                return (
                  <button
                    key={mode.id}
                    className={`px-3 py-1.5 text-sm font-medium transition-all relative ${
                      isActive
                        ? 'text-white'
                        : 'text-white/80 hover:text-white'
                    }`}
                    onClick={() => {
                      if (mode.id === 'users' && onNavigateToUsers) {
                        onNavigateToUsers()
                      } else {
                        handleModeClick(mode.id)
                      }
                    }}
                  >
                    {mode.label}
                    {isActive && (
                      <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-white rounded-full"></span>
                    )}
                  </button>
                )
              })}
              
              {/* More Dropdown - only show if there are items */}
              {moreItems.length > 0 && (
                <div className="relative" ref={moreDropdownRef}>
                  <button
                    className={`px-3 py-1.5 text-sm font-medium transition-all relative flex items-center gap-1 ${
                      moreItems.some(item => currentMode === item.id)
                        ? 'text-white'
                        : 'text-white/80 hover:text-white'
                    }`}
                    onClick={(e) => {
                      e.stopPropagation()
                      setShowMoreDropdown(!showMoreDropdown)
                    }}
                  >
                    More
                    <ChevronDownIcon size={12} className={`transition-transform ${showMoreDropdown ? 'rotate-180' : ''}`} />
                    {moreItems.some(item => currentMode === item.id) && (
                      <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-white rounded-full"></span>
                    )}
                  </button>
                  
                  {showMoreDropdown && (
                    <div className="absolute top-full right-0 mt-1 bg-white rounded-lg shadow-xl border border-gray-200 py-1 z-[100] min-w-[180px]">
                      {moreItems.map((item) => {
                        const isActive = currentMode === item.id
                        return (
                          <button
                            key={item.id}
                            className={`w-full text-left px-4 py-2 text-sm transition-colors flex items-center gap-2 ${
                              isActive
                                ? 'bg-[#168AAD]/10 text-[#168AAD] font-medium'
                                : 'text-gray-700 hover:bg-gray-50'
                            }`}
                            onClick={(e) => {
                              e.stopPropagation()
                              handleModeClick(item.id)
                              setShowMoreDropdown(false)
                            }}
                          >
                            <span>{item.icon}</span>
                            <span>{item.label}</span>
                          </button>
                        )
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0 min-w-0 overflow-visible ml-auto">
          {/* Back to Selection + Current Selection - shown when study & site are selected */}
          {showNavigationControls && (
            <div className="hidden md:flex items-center gap-2 border-r border-white/30 pr-3 mr-1">
              <button
                onClick={() => {
                  setSelectedStudyId(null)
                  setSelectedSiteId(null)
                }}
                className="px-3 py-1.5 bg-white/15 hover:bg-white/25 text-white text-xs font-medium rounded-lg transition-all flex items-center gap-1 shrink-0"
              >
                ← Back
              </button>
              <span className="text-white/90 text-xs truncate max-w-[200px] xl:max-w-[280px]">
                <span className="text-white/60">Selection:</span>{' '}
                <span className="font-semibold text-white">
                  {studies.find(s => s.id === selectedStudyId)?.name || selectedStudyId}
                </span>
                <span className="text-white/60 mx-1">→</span>
                <span className="font-semibold text-white">
                  {filteredSites.find(s => s.site_id === selectedSiteId)?.name || selectedSiteId}
                </span>
              </span>
            </div>
          )}

          {/* Profile Dropdown */}
          {user && (
            <div className="relative overflow-visible" ref={userMenuRef}>
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-1 sm:gap-1.5 lg:gap-2 pl-1 sm:pl-2 lg:pl-3 ml-0.5 sm:ml-1 lg:ml-2 hover:opacity-80 transition-opacity duration-200 focus:outline-none focus:ring-2 focus:ring-white/50 focus:ring-offset-2 focus:ring-offset-transparent rounded-lg shrink-0"
              >
                <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-full bg-white/20 flex items-center justify-center text-white font-semibold text-xs sm:text-sm border-2 border-white/30 ring-2 ring-white/20 shrink-0">
                  {getUserInitials()}
                </div>
                <div className="hidden lg:block text-left min-w-0">
                  <div className="text-sm font-semibold text-white leading-tight truncate">
                    {user.name || user.email || 'User'}
                  </div>
                  {user.email && (
                    <div className="text-xs text-white/70 leading-tight truncate max-w-[120px] xl:max-w-[150px]">
                      {user.email}
                    </div>
                  )}
                </div>
                <ChevronDownIcon size={14} className="sm:w-4 sm:h-4 text-white/80 transition-transform duration-200 hidden sm:block shrink-0" />
              </button>

              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-xl border border-gray-200 py-1 z-[100] overflow-y-auto max-h-[calc(100vh-5rem)]" style={{ position: 'fixed', top: '4rem', right: '1rem' }}>
                  {/* User Info Section */}
                  <div className="px-3 py-3 border-b border-gray-100">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-full bg-[#1E73BE] flex items-center justify-center text-white font-semibold text-lg border-2 border-gray-200">
                        {getUserInitials()}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-gray-900 truncate">
                          {user.name || user.email || 'User'}
                        </p>
                        {user.email && (
                          <p className="text-xs text-gray-500 truncate mt-0.5">
                            {user.email}
                          </p>
                        )}
                        {user.is_privileged && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-[#1E73BE]/10 text-[#1E73BE] mt-1">
                            Admin
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="h-px bg-gray-100"></div>
                  
                  {/* Menu Items */}
                  <div className="px-3 py-2">
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
                      Account
                    </p>
                    <button
                      onClick={() => {
                        // Settings placeholder
                        setShowUserMenu(false)
                      }}
                      className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors rounded-md flex items-center gap-2"
                    >
                      <SettingsIcon size={16} />
                      <span>Settings</span>
                    </button>
                  </div>
                  <div className="h-px bg-gray-100"></div>
                  <button
                    onClick={handleLogout}
                    className="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors rounded-md flex items-center gap-2"
                  >
                    <LogOutIcon size={16} />
                    <span>Logout</span>
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </nav>
  )
}

export default Navbar
