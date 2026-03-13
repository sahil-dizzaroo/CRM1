import React, { useState, useEffect, useMemo } from 'react'
import { api } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import { useStudySite } from '../contexts/StudySiteContext'
import StudySiteSelector from './StudySiteSelector'
import ConversationList from './ConversationList'
import ConversationDetail from './ConversationDetail'
import CreateConversationModal from './CreateConversationModal'
import DashboardStats from './DashboardStats'
import ThreadList from './ThreadList'
import ThreadDetail from './ThreadDetail'
import CreateThreadModal from './CreateThreadModal'
import ThreadCombinationSuggestions from './ThreadCombinationSuggestions'
import AskMeAnything from './AskMeAnything'
import SiteControlTower from './SiteControlTower'
import LogisticsTab from './LogisticsTab'
import MonitoringTab from './MonitoringTab'
import TasksTab from './TasksTab'
import SiteDocumentsTab from './SiteDocumentsTab'
import AgreementTab from './AgreementTab'
import StudyTemplateLibrary from './StudyTemplateLibrary'
import SiteProfileTab from './SiteProfileTab'
import ResizableSidebar from './ResizableSidebar'
import { RotatingText } from './animated/RotatingText'
import { Conversation, Thread, Stats } from '../types'

interface UnifiedInboxProps {
  apiBase: string
  onNavigateToUsers?: () => void
  currentMode?: string
  onModeChange?: (mode: string) => void
  onSidebarPropsChange?: (props: {
    selectedConversationId?: string | null
    selectedThreadId?: string | null
    onSelectConversation?: (id: string) => void
    onSelectThread?: (id: string) => void
    onCreateConversation?: () => void
    onCreateThread?: () => void
  }) => void
}

const UnifiedInbox: React.FC<UnifiedInboxProps> = ({
  apiBase,
  currentMode: externalMode,
  onSidebarPropsChange,
}) => {
  const { user } = useAuth()
  const {
    selectedStudyId,
    selectedSiteId,
    studies,
    filteredSites,
    setSelectedStudyId,
    setSelectedSiteId
  } = useStudySite()

  const currentUserId = user?.user_id || ''

  const [internalMode] = useState<
    'conversations' | 'threads' | 'users' | 'sites' | 'ask' | 'site-status' | 'logistics' | 'monitoring' | 'tasks'
  >('conversations')

  const [conversationsTab, setConversationsTab] =
    useState<'conversations' | 'threads'>('conversations')

  const [sitesTab, setSitesTab] =
    useState<'site-status' | 'logistics' | 'monitoring' | 'tasks' | 'documents' | 'agreements' | 'study-setup' | 'site-profile'>('site-status')

  useEffect(() => {
    const currentMode = externalMode || internalMode

    if (currentMode === 'threads') {
      setConversationsTab('threads')
    } else if (currentMode === 'conversations') {
      setConversationsTab('conversations')
    } else if (
      currentMode === 'site-status' ||
      currentMode === 'logistics' ||
      currentMode === 'monitoring' ||
      currentMode === 'tasks' ||
      currentMode === 'documents' ||
      currentMode === 'agreements' ||
      currentMode === 'study-setup' ||
      currentMode === 'site-profile'
    ) {
      setSitesTab(currentMode as any)
    }
  }, [externalMode, internalMode])

  let topLevelMode = externalMode || internalMode
  if (topLevelMode === 'threads') topLevelMode = 'conversations'
  else if (
    topLevelMode === 'site-status' ||
    topLevelMode === 'logistics' ||
    topLevelMode === 'monitoring' ||
    topLevelMode === 'tasks' ||
    topLevelMode === 'documents' ||
    topLevelMode === 'agreements' ||
    topLevelMode === 'study-setup' ||
    topLevelMode === 'site-profile'
  ) {
    topLevelMode = 'sites'
  }

  let activeTab: string
  if (topLevelMode === 'conversations') activeTab = conversationsTab
  else if (topLevelMode === 'sites') activeTab = sitesTab
  else activeTab = topLevelMode

  const [conversations, setConversations] = useState<Conversation[]>([])
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null)
  const [threads, setThreads] = useState<Thread[]>([])
  const [selectedThread, setSelectedThread] = useState<Thread | null>(null)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showCreateThreadModal, setShowCreateThreadModal] = useState(false)

  const [threadFilters, setThreadFilters] = useState({
    thread_type: 'all',
    status: 'all'
  })

  const [filters, setFilters] = useState({
    channel: 'all',
    study_id: '',
    search: '',
    confidential: 'all'
  })

  const [stats, setStats] = useState<Stats | null>(null)

  useEffect(() => {
    if (onSidebarPropsChange) {
      const isThreadsTab = conversationsTab === 'threads'

      onSidebarPropsChange({
        selectedConversationId: selectedConversation?.id || null,
        selectedThreadId: selectedThread?.id || null,
        onSelectConversation: handleSelectConversation,
        onSelectThread: handleSelectThread,
        onCreateConversation: () => {
          if (isThreadsTab) setShowCreateThreadModal(true)
          else setShowCreateModal(true)
        },
        onCreateThread: () => setShowCreateThreadModal(true)
      })
    }
  }, [selectedConversation?.id, selectedThread?.id, conversationsTab])

  useEffect(() => {
    if (!selectedStudyId || !selectedSiteId) {
      setConversations([])
      setThreads([])
      setStats(null)
      return
    }

    if (activeTab === 'conversations') {
      loadConversations()
      loadStats()
    } else {
      loadThreads()
    }

    const interval = setInterval(() => {
      if (activeTab === 'conversations') {
        loadConversations()
        loadStats()
      } else {
        loadThreads()
      }
    }, 30000)

    return () => clearInterval(interval)
  }, [filters, threadFilters, activeTab, selectedStudyId, selectedSiteId])

  const loadConversations = async () => {
    try {
      setLoading(true)
      setError(null)

      const params: any = {
        limit: 100,
        offset: 0,
        study_id: selectedStudyId,
        site_id: selectedSiteId
      }

      if (filters.channel !== 'all') params.channel = filters.channel

      const response = await api.get('/conversations', { params })
      let data = response.data || []

      if (filters.search) {
        const s = filters.search.toLowerCase()
        data = data.filter((c: Conversation) =>
          c.participant_phone?.toLowerCase().includes(s) ||
          c.participant_email?.toLowerCase().includes(s) ||
          c.subject?.toLowerCase().includes(s)
        )
      }

      if (filters.confidential === 'confidential') {
        data = data.filter((c: Conversation) => c.is_confidential === 'true')
      } else if (filters.confidential === 'public') {
        data = data.filter((c: Conversation) => c.is_confidential !== 'true')
      }

      setConversations(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load conversations')
      setConversations([])
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const response = await api.get('/conversations/stats')
      setStats(response.data)
    } catch {
      console.error('Failed to load stats')
    }
  }

  const handleSelectConversation = async (id: string) => {
    try {
      setLoading(true)
      const response = await api.get(`/conversations/${id}?limit=200&offset=0`)
      setSelectedConversation(response.data)
    } catch (err: any) {
      if (err.response?.status === 403) {
        setError('You do not have access to this conversation.')
        setSelectedConversation(null)
        await loadConversations()
      } else {
        setError(err.response?.data?.detail || 'Failed to load conversation')
      }
    } finally {
      setLoading(false)
    }
  }

  const loadThreads = async () => {
    try {
      setLoading(true)
      setError(null)

      const params: any = {
        limit: 100,
        offset: 0,
        study_id: selectedStudyId,
        site_id: selectedSiteId
      }

      if (threadFilters.thread_type !== 'all') params.thread_type = threadFilters.thread_type
      if (threadFilters.status !== 'all') params.status = threadFilters.status

      const response = await api.get('/threads', { params })
      setThreads(response.data || [])
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load threads')
      setThreads([])
    } finally {
      setLoading(false)
    }
  }

  const handleSelectThread = async (id: string) => {
    try {
      setLoading(true)
      const response = await api.get(`/threads/${id}?limit=200&offset=0`)
      setSelectedThread(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load thread')
      setSelectedThread(null)
    } finally {
      setLoading(false)
    }
  }
    const handleCreateConversation = async (data: {
    participant_phone?: string
    participant_email?: string
    participant_emails?: string[]
    subject?: string
    study_id?: string
  }) => {
    try {
      setLoading(true)
      setError(null)
      const conversationData = {
        ...data,
        study_id: selectedStudyId || data.study_id,
        site_id: selectedSiteId
      }
      const response = await api.post('/conversations', conversationData)
      await loadConversations()
      setSelectedConversation(response.data)
      setShowCreateModal(false)
      setError(null)
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to create conversation'
      setError(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg))
    } finally {
      setLoading(false)
    }
  }

  const handleCreateThread = async (data: {
    conversation_id?: string
    title: string
    description?: string
    thread_type: string
    related_patient_id?: string
    related_study_id?: string
    priority: string
    created_by?: string
    participants?: Array<{
      participant_id: string
      participant_name?: string
      participant_email?: string
      role?: string
    }>
  }) => {
    try {
      setLoading(true)
      setError(null)
      const threadData = {
        ...data,
        related_study_id: selectedStudyId || data.related_study_id,
        site_id: selectedSiteId
      }
      const response = await api.post('/threads', threadData)
      await loadThreads()
      setSelectedThread(response.data)
      setShowCreateThreadModal(false)
      setError(null)
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to create thread'
      setError(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg))
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = () => {
    if (activeTab === 'conversations') {
      loadConversations()
      if (selectedConversation) handleSelectConversation(selectedConversation.id)
    } else {
      loadThreads()
      if (selectedThread) handleSelectThread(selectedThread.id)
    }
  }




  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Study/Site Selector shown only when nothing is selected */}
      {(!selectedStudyId || !selectedSiteId) && (
        <div className="bg-white border-b border-gray-200 shadow-sm flex-shrink-0 px-6 py-3">
          <StudySiteSelector />
        </div>
      )}

      {/* Only show content if both study and site are selected */}
      {!selectedStudyId || !selectedSiteId ? (
        <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
          {/* Hero Section with Animated Text */}
          <div className="max-w-4xl mx-auto px-6 py-12 text-center">
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-gray-900 mb-6 leading-tight">
              Bring your{' '}
              <span className="font-bold inline-block">
                <RotatingText 
                  items={[
                    'conversations',
                    'site status',
                    'logistics',
                    'monitoring',
                    'tasks',
                    'AI assistance'
                  ]}
                  intervalMs={4000}
                  className="font-bold"
                />
              </span>{' '}
              together in Dizzaroo CRM.
            </h1>
            
            <p className="text-lg md:text-xl text-gray-600 mb-8 max-w-2xl mx-auto leading-relaxed">
              Keep conversations, site tracking, logistics, monitoring and AI in one place so your team can move faster.
            </p>
            
            <p className="text-base text-gray-500">
              Select a study and site above to begin
            </p>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex flex-col min-h-0">

      {activeTab === 'conversations' ? (
        <div className="bg-white border-b border-gray-200 px-6 py-3 flex gap-4 items-center justify-between flex-shrink-0 shadow-sm">
          <div className="flex gap-4 items-center">
          <div className="flex items-center gap-2">
              <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide">Channel:</label>
            <select 
                className="px-3 py-2 border-2 border-gray-300 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue focus:border-dizzaroo-deep-blue transition-all"
              value={filters.channel} 
                onChange={(e) => setFilters({ ...filters, channel: e.target.value })}
            >
              <option value="all">All Channels</option>
                <option value="email">📧 Email</option>
            </select>
          </div>
          
          <div className="flex items-center gap-2">
              <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide">Confidential:</label>
              <select
                className="px-3 py-2 border-2 border-gray-300 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue focus:border-dizzaroo-deep-blue transition-all"
                value={filters.confidential}
                onChange={(e) => setFilters({ ...filters, confidential: e.target.value })}
              >
                <option value="all">All Conversations</option>
                <option value="confidential">🔐 Confidential Only</option>
                <option value="public">🌐 Public Only</option>
              </select>
            </div>

            <div className="flex items-center gap-2 max-w-xs">
              <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide">Search:</label>
            <input
              type="text"
                className="px-3 py-2 border-2 border-gray-300 rounded-xl text-sm w-48 focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue focus:border-dizzaroo-deep-blue transition-all"
                placeholder="🔍 Search conversations..."
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              />
            </div>
          </div>
          
          {/* Stats on the right */}
          {stats && (
            <div className="flex-shrink-0">
              <DashboardStats stats={stats} />
          </div>
          )}
        </div>
      ) : (
        <div className="bg-white border-b border-gray-200 px-6 py-3 flex gap-4 items-center flex-wrap flex-shrink-0 shadow-sm">
          <div className="flex items-center gap-2">
            <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide">Type:</label>
            <select 
              className="px-3 py-2 border-2 border-gray-300 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue focus:border-dizzaroo-deep-blue transition-all"
              value={threadFilters.thread_type} 
              onChange={(e) => setThreadFilters({ ...threadFilters, thread_type: e.target.value })}
            >
              <option value="all">All Types</option>
              <option value="general">General</option>
              <option value="issue">Issue</option>
              <option value="patient">Patient</option>
            </select>
          </div>
          
          <div className="flex items-center gap-2">
            <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide">Status:</label>
            <select 
              className="px-3 py-2 border-2 border-gray-300 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue focus:border-dizzaroo-deep-blue transition-all"
              value={threadFilters.status} 
              onChange={(e) => setThreadFilters({ ...threadFilters, status: e.target.value })}
            >
              <option value="all">All Statuses</option>
              <option value="open">Open</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </select>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 mx-5 mt-3 rounded">
          {typeof error === 'string' ? error : JSON.stringify(error)}
        </div>
      )}

      {activeTab === 'ask' ? (
        <div className="flex-1 overflow-hidden">
          <AskMeAnything apiBase={apiBase} />
        </div>
      ) : activeTab === 'site-status' ? (
        <div className="flex-1 overflow-hidden">
          <SiteControlTower apiBase={apiBase} />
        </div>
      ) : activeTab === 'logistics' ? (
        <div className="flex-1 overflow-hidden">
          <LogisticsTab />
        </div>
      ) : activeTab === 'monitoring' ? (
        <div className="flex-1 overflow-hidden">
          <MonitoringTab />
        </div>
      ) : activeTab === 'tasks' ? (
        <div className="flex-1 overflow-hidden">
          <TasksTab apiBase={apiBase} />
        </div>
      ) : activeTab === 'documents' ? (
        <div className="flex-1 overflow-hidden">
          <SiteDocumentsTab apiBase={apiBase} />
        </div>
      ) : activeTab === 'agreements' ? (
        <div className="flex-1 overflow-hidden">
          <AgreementTab apiBase={apiBase} />
        </div>
      ) : activeTab === 'study-setup' ? (
        <div className="flex-1 overflow-y-auto min-h-0">
          <StudyTemplateLibrary apiBase={apiBase} />
        </div>
      ) : activeTab === 'site-profile' ? (
        <div className="flex-1 overflow-hidden h-full">
          <SiteProfileTab apiBase={apiBase} />
        </div>
      ) : topLevelMode === 'sites' ? (
        // Show default site-status when sites is selected
        <div className="flex-1 overflow-hidden">
          <SiteControlTower apiBase={apiBase} />
        </div>
      ) : (
        <div className="flex flex-1 overflow-hidden w-full">
          <ResizableSidebar defaultWidth={280} minWidth={200} maxWidth={400}>
            <div className="bg-gray-50 border-r border-gray-200 flex flex-col overflow-hidden h-full w-full">
            <div className="px-4 py-3 border-b border-gray-200 bg-white flex-shrink-0 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-gray-800">
                {activeTab === 'conversations' 
                  ? `💬 Conversations (${conversations.length})`
                  : `🧵 Threads (${threads.length})`}
              </h2>
              {activeTab === 'conversations' && (
                <button
                  type="button"
                  onClick={() => setShowCreateModal(true)}
                  className="inline-flex items-center justify-center px-2.5 py-1.5 text-xs font-medium rounded-lg bg-[#168AAD] text-white hover:bg-[#1E73BE] shadow-sm transition-colors"
                  title="New Conversation"
                >
                  +
                </button>
              )}
            </div>
          {loading && (
              <div className="p-2 text-center text-gray-500 text-sm">Loading...</div>
          )}
            <div className="flex-1 overflow-y-auto min-h-0">
            {activeTab === 'conversations' ? (
                conversations.length > 0 ? (
              <ConversationList
                conversations={conversations}
                onSelect={handleSelectConversation}
                selectedId={selectedConversation?.id}
                apiBase={apiBase}
                    currentUserId={currentUserId}
              />
            ) : (
                  <div className="p-4 text-center text-gray-500 text-sm">
                    <p>No conversations found</p>
                    <p className="text-xs mt-1">Create a new conversation to get started</p>
                  </div>
                )
              ) : (
                <>
                  <div className="mb-4 px-2">
                    <ThreadCombinationSuggestions apiBase={apiBase} onCombined={loadThreads} />
                  </div>
                  {threads.length > 0 ? (
                    <ThreadList
                      threads={threads}
                      onSelect={handleSelectThread}
                      selectedId={selectedThread?.id}
                    />
                  ) : (
                    <div className="p-4 text-center text-gray-500 text-sm">
                      <p>No threads found</p>
                      <p className="text-xs mt-1">Create a new thread to get started</p>
                    </div>
                  )}
                </>
            )}
          </div>
            </div>
          </ResizableSidebar>

          <div className="flex-1 flex flex-col overflow-hidden bg-gray-50 pr-4">
          {activeTab === 'conversations' ? (
            selectedConversation ? (
                <div className="h-full bg-white rounded-l-lg shadow-sm">
              <ConversationDetail
                conversation={selectedConversation}
                onRefresh={handleRefresh}
                apiBase={apiBase}
                    currentUserId={currentUserId}
              />
                </div>
            ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-gray-500 p-8 bg-white rounded-l-lg shadow-sm">
                <h2 className="text-2xl font-semibold mb-2">Select a conversation</h2>
                <p>Choose a conversation from the list to view messages, or create a new one.</p>
              </div>
            )
          ) : (
            selectedThread ? (
                <div className="h-full bg-white rounded-l-lg shadow-sm">
              <ThreadDetail
                thread={selectedThread}
                onRefresh={handleRefresh}
                apiBase={apiBase}
                    currentUserId={currentUserId}
                    currentUserName={user?.name || user?.email || currentUserId}
              />
                </div>
            ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-gray-500 p-8 bg-white rounded-l-lg shadow-sm">
                <h2 className="text-2xl font-semibold mb-2">Select a thread</h2>
                <p>Choose a thread from the list to view messages, or create a new one.</p>
              </div>
            )
          )}
        </div>
      </div>
      )}
        </div>
      )}

      {showCreateModal && (
        <CreateConversationModal
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreateConversation}
          loading={loading}
          studyName={studies.find(s => s.id === selectedStudyId)?.name}
          siteName={filteredSites.find(s => s.site_id === selectedSiteId)?.name}
        />
      )}

      {showCreateThreadModal && (
        <CreateThreadModal
          onClose={() => setShowCreateThreadModal(false)}
          onSubmit={handleCreateThread}
          loading={loading}
          conversations={conversations}
          defaultConversationId={selectedConversation?.id}
        />
      )}
    </div>
  )
}

export default UnifiedInbox

