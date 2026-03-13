import React, { useState } from 'react'
console.log('VITE_API_BASE =', import.meta.env.VITE_API_BASE)
console.log('redeployed')
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { StudySiteProvider } from './contexts/StudySiteContext'
import { ThemeProvider } from './providers/ThemeProvider'
import AppLayout from './layouts/AppLayout'
import UnifiedInbox from './components/UnifiedInbox'
import UserDirectory from './components/UserDirectory'
import Login from './components/Login'
import Signup from './components/Signup'
import FeasibilityForm from './components/FeasibilityForm'
import CdaSign from './components/CdaSign'
import './App.css'

// Use relative path for Vite proxy, or absolute URL if explicitly set
//const API_BASE = import.meta.env.VITE_API_BASE || '/api'
const API_BASE = import.meta.env.VITE_API_BASE

type View = 'inbox' | 'users'
type Mode = 'conversations' | 'sites' | 'users' | 'ask'

const AppContent: React.FC = () => {
  const { user, loading } = useAuth()
  const [showSignup, setShowSignup] = useState(false)
  const [currentView, setCurrentView] = useState<View>('inbox')
  const [currentMode, setCurrentMode] = useState<Mode>('conversations')
  
  // Check if we're on public pages (no auth required)
  const isFeasibilityFormPage = window.location.pathname === '/feasibility/form'
  const isCdaSignPage = window.location.pathname === '/cda/sign'
  const [sidebarProps, setSidebarProps] = useState<{
    selectedConversationId?: string | null
    selectedThreadId?: string | null
    onSelectConversation?: (id: string) => void
    onSelectThread?: (id: string) => void
    onCreateConversation?: () => void
    onCreateThread?: () => void
  }>({})

  // Render public pages (no auth required)
  if (isFeasibilityFormPage) {
    return <FeasibilityForm />
  }

  if (isCdaSignPage) {
    return <CdaSign />
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-dizzaroo-deep-blue"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return showSignup ? (
      <Signup onSwitchToLogin={() => setShowSignup(false)} />
    ) : (
      <Login onSwitchToSignup={() => setShowSignup(true)} />
    )
  }

  const handleModeChange = (mode: string) => {
    setCurrentMode(mode as Mode)
    if (mode === 'users') {
      setCurrentView('users')
    } else {
      setCurrentView('inbox')
    }
  }

  const handleNavigateToUsers = () => {
    setCurrentView('users')
    setCurrentMode('users')
  }

  // Wrap everything in StudySiteProvider to preserve study/site selection across views
  return (
    <StudySiteProvider apiBase={API_BASE}>
      <AppLayout
        currentMode={currentMode}
        onModeChange={handleModeChange}
        onNavigateToUsers={handleNavigateToUsers}
        apiBase={API_BASE}
        sidebarProps={sidebarProps}
      >
        {currentView === 'users' ? (
          <UserDirectory apiBase={API_BASE} onBack={() => {
            setCurrentView('inbox')
            setCurrentMode('conversations')
          }} />
        ) : (
          <UnifiedInbox 
            apiBase={API_BASE} 
            onNavigateToUsers={handleNavigateToUsers}
            currentMode={currentMode}
            onModeChange={setCurrentMode}
            onSidebarPropsChange={setSidebarProps}
          />
        )}
      </AppLayout>


    </StudySiteProvider>
  )
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider apiBase={API_BASE}>
        <AppContent />
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App

