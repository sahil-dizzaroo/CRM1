import React from 'react'
import Navbar from '../components/Navbar'

interface AppLayoutProps {
  children: React.ReactNode
  currentMode?: string
  onModeChange?: (mode: string) => void
  onNavigateToUsers?: () => void
  sidebarProps?: {
    selectedConversationId?: string | null
    selectedThreadId?: string | null
    onSelectConversation?: (id: string) => void
    onSelectThread?: (id: string) => void
    onCreateConversation?: () => void
    onCreateThread?: () => void
  }
}

export const AppLayout: React.FC<AppLayoutProps> = ({
  children,
  currentMode,
  onModeChange,
  onNavigateToUsers,
  sidebarProps
}) => {
  return (
    <div className="h-screen flex flex-col bg-gray-50 overflow-x-hidden">
      <Navbar 
        currentMode={currentMode}
        onModeChange={onModeChange}
        onNavigateToUsers={onNavigateToUsers}
        sidebarProps={sidebarProps}
      />
      <div className="flex-1 flex flex-row min-h-0 overflow-hidden">
        <main className="flex-1 overflow-y-auto overflow-x-hidden min-h-0">
          {children}
        </main>
      </div>
    </div>
  )
}

export default AppLayout

