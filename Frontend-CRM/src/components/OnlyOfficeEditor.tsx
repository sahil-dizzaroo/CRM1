import React, { useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'

interface OnlyOfficeEditorProps {
  agreementId?: string  // For agreements
  templateId?: string   // For templates
  apiBase?: string
  canEdit: boolean
  onSave?: () => void
  configEndpoint?: string  // Optional: custom config endpoint path
}

const OnlyOfficeEditor: React.FC<OnlyOfficeEditorProps> = ({
  agreementId,
  templateId,
  apiBase = '/api',
  canEdit,
  onSave,
  configEndpoint,
}) => {
  const editorRef = useRef<HTMLDivElement>(null)
  const editorInstanceRef = useRef<any>(null)
  const scriptRef = useRef<HTMLScriptElement | null>(null)
  const containerRef = useRef<HTMLDivElement | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [config, setConfig] = useState<any>(null)
  // Note: Frontend locking hacks removed - structural DOCX-level locking is now used
  // Locked fields are protected via content controls in the DOCX itself

  useEffect(() => {
    const loadEditor = async () => {
      // Declare configUrl outside try block so it's accessible in catch block
      let configUrl: string = ''
      
      try {
        setLoading(true)
        setError(null)

        // Get ONLYOFFICE configuration from backend
        // Support both agreements and templates
        if (configEndpoint) {
          configUrl = `${apiBase}${configEndpoint}`
        } else if (templateId) {
          configUrl = `${apiBase}/templates/${templateId}/onlyoffice-config`
        } else if (agreementId) {
          configUrl = `${apiBase}/agreements/${agreementId}/onlyoffice-config`
        } else {
          throw new Error('Either agreementId, templateId, or configEndpoint must be provided')
        }
        
        const response = await api.get(configUrl)
        const { editorUrl, config: editorConfig } = response.data

        setConfig(editorConfig)
        
        // Note: Field-level locking is handled entirely at DOCX level via content controls
        // Frontend does not inspect or manage locked fields at all.

        // Check if script already exists
        const existingScript = document.querySelector(`script[src="${editorUrl}"]`)
        if (existingScript) {
          // Script already loaded, initialize editor directly (but only if not already initialized)
          if (window.DocsAPI && editorRef.current && !editorInstanceRef.current) {
            // Wait a bit to ensure element is connected (React StrictMode may cause timing issues)
            setTimeout(() => {
              if (editorRef.current && editorRef.current.isConnected && !editorInstanceRef.current) {
                initializeEditor(editorConfig)
              }
            }, 100)
          }
          return
        }

        // Load ONLYOFFICE script
        const script = document.createElement('script')
        script.src = editorUrl
        script.async = true
        scriptRef.current = script

        script.onload = () => {
          // Wait for container to be fully rendered with dimensions
          const waitForContainer = (attempts: number = 0) => {
            if (attempts > 50) { // Increased attempts to 50 (5 seconds total)
              console.error('Container not ready after 50 attempts')
              // Still try to initialize - sometimes ONLYOFFICE can work with minimal dimensions
              if (window.DocsAPI && editorRef.current) {
                const rect = editorRef.current.getBoundingClientRect()
                console.warn('Initializing editor despite container dimensions:', { width: rect.width, height: rect.height })
                initializeEditor(editorConfig)
              } else {
                setError('Editor container not ready after multiple attempts. Please refresh the page.')
                setLoading(false)
              }
              return
            }
            
            if (!window.DocsAPI) {
              console.log(`Waiting for DocsAPI (attempt ${attempts + 1})`)
              setTimeout(() => waitForContainer(attempts + 1), 100)
              return
            }
            
            if (!editorRef.current) {
              console.log(`Waiting for container ref (attempt ${attempts + 1})`)
              setTimeout(() => waitForContainer(attempts + 1), 100)
              return
            }
            
            const rect = editorRef.current.getBoundingClientRect()
            const computedStyle = window.getComputedStyle(editorRef.current)
            const inlineStyle = editorRef.current.style
            const parent = editorRef.current.parentElement
            const parentRect = parent ? parent.getBoundingClientRect() : null
            
            // Check if container or parent has dimensions
            const hasDimensions = rect.width > 0 && rect.height > 0
            const parentHasDimensions = parentRect ? (parentRect.width > 0 && parentRect.height > 0) : false
            
            // Check for minHeight in both computed style and inline style
            const computedMinHeight = parseInt(computedStyle.minHeight || '0', 10)
            const inlineMinHeight = parseInt(inlineStyle.minHeight || '0', 10)
            const hasMinHeight = computedMinHeight > 0 || inlineMinHeight > 0
            
            // Check if element is visible (not display: none)
            const isVisible = computedStyle.display !== 'none' && computedStyle.visibility !== 'hidden'
            
            const hasWidth = rect.width > 0
            
            // Proceed if:
            // 1. Container has both width and height, OR
            // 2. Element is visible and has minHeight set (ONLYOFFICE can work with minHeight), OR
            // 3. After 10 attempts, proceed if element exists and is visible (dimensions may compute later)
            const shouldProceed = hasDimensions || (isVisible && hasMinHeight) || (attempts >= 10 && isVisible && editorRef.current.isConnected)
            
            if (shouldProceed) {
              console.log('✅ Container ready:', { 
                width: rect.width, 
                height: rect.height,
                hasMinHeight,
                computedMinHeight: computedStyle.minHeight,
                inlineMinHeight: inlineStyle.minHeight,
                isVisible,
                isConnected: editorRef.current.isConnected,
                parentWidth: parentRect?.width,
                parentHeight: parentRect?.height,
                attempts: attempts + 1,
                reason: hasDimensions ? 'hasDimensions' : (isVisible && hasMinHeight) ? 'visibleWithMinHeight' : 'visibleAfterAttempts'
              })
              initializeEditor(editorConfig)
              return // Stop the loop once we've initialized
            } else {
              // Log detailed info for debugging
              if (attempts % 5 === 0) { // Log every 5th attempt to reduce spam
                console.log(`Container not ready (attempt ${attempts + 1}):`, {
                  containerWidth: rect.width,
                  containerHeight: rect.height,
                  parentWidth: parentRect?.width,
                  parentHeight: parentRect?.height,
                  hasMinHeight,
                  computedMinHeight: computedStyle.minHeight,
                  inlineMinHeight: inlineStyle.minHeight,
                  isVisible,
                  isConnected: editorRef.current.isConnected,
                  display: computedStyle.display,
                  visibility: computedStyle.visibility,
                  position: computedStyle.position
                })
              }
              setTimeout(() => waitForContainer(attempts + 1), 100)
            }
          }
          
          waitForContainer()
        }

        script.onerror = () => {
          setError('Failed to load ONLYOFFICE editor script')
          setLoading(false)
          scriptRef.current = null
        }

        document.head.appendChild(script)
      } catch (err: any) {
        console.error('Failed to load ONLYOFFICE config:', err)
        const errorMessage = err.response?.data?.detail || err.message || 'Failed to load editor configuration'
        console.error('ONLYOFFICE config load failed:', {
          errorMessage,
          agreementId,
          templateId,
          statusCode: err.response?.status,
          url: configUrl || 'not set',
          configEndpoint
        })
        setError(errorMessage)
        setLoading(false)
      }
    }

    const initializeEditor = (editorConfig: any) => {
      try {
        // Prevent duplicate initialization (React StrictMode can cause double renders)
        if (editorInstanceRef.current) {
          console.log('Editor already initialized, skipping duplicate initialization')
          setLoading(false) // Make sure loading is hidden if editor is already initialized
          return
        }
        
        if (!editorRef.current) {
          console.error('Editor ref is not available')
          return
        }

        if (!window.DocsAPI || !window.DocsAPI.DocEditor) {
          console.error('ONLYOFFICE DocsAPI not available')
          setError('ONLYOFFICE editor API not loaded. Please refresh the page.')
          setLoading(false)
          return
        }

        // Destroy existing editor instance if any (shouldn't happen due to check above, but just in case)
        if (editorInstanceRef.current) {
          try {
            if (typeof editorInstanceRef.current.destroy === 'function') {
              editorInstanceRef.current.destroy()
            }
          } catch (e) {
            console.debug('Error destroying previous editor:', e)
          }
          editorInstanceRef.current = null
        }

        // Log the config for debugging (without sensitive data)
        const configForLog = { ...editorConfig }
        if (configForLog.token) {
          configForLog.token = '[REDACTED]'
        }
        console.log('Initializing ONLYOFFICE editor', {
          containerId: editorRef.current?.id,
          documentUrl: editorConfig.document?.url,
          documentKey: editorConfig.document?.key,
          configKeys: Object.keys(editorConfig),
          hasToken: !!editorConfig.token
        })
        
        // Verify document URL is accessible
        if (editorConfig.document?.url) {
          console.log('Document URL for ONLYOFFICE:', editorConfig.document.url)
        }

        // Initialize ONLYOFFICE editor
        let docEditor: any
        try {
          const containerId = editorRef.current.id || 'onlyoffice-editor'
          if (!editorRef.current.id) {
            editorRef.current.id = containerId
          }
          
          // Store editor instance reference for locking functionality
          
          // Log the full config before creating editor (for debugging)
          console.log('Creating editor with config:', {
            containerId,
            documentUrl: editorConfig.document?.url,
            documentKey: editorConfig.document?.key,
            documentType: editorConfig.documentType,
            mode: editorConfig.editorConfig?.mode,
            hasToken: !!editorConfig.token,
            configString: JSON.stringify(editorConfig).substring(0, 500)
          })
          
          try {
            // Use the ref directly - it's more reliable than getElementById
            const containerElement = editorRef.current
            if (!containerElement) {
              throw new Error(`Container element ref is null`)
            }
            
            // Check if element is connected to DOM (warn but don't fail - React StrictMode may cause this)
            if (!containerElement.isConnected) {
              console.warn('⚠️ Container element is not connected to DOM yet - this may be due to React StrictMode. Retrying...')
              // In development, React StrictMode can cause this. Wait a bit and retry
              setTimeout(() => {
                if (editorRef.current && editorRef.current.isConnected && !editorInstanceRef.current) {
                  console.log('Retrying editor initialization after element connected')
                  initializeEditor(editorConfig)
                }
              }, 100)
              return // Exit early, will retry
            }
            
            // Ensure element has an ID (ONLYOFFICE requires it)
            if (!containerElement.id) {
              containerElement.id = containerId
            }
            
            const containerRect = containerElement.getBoundingClientRect()
            console.log('Container element check:', {
              exists: !!containerElement,
              isConnected: containerElement.isConnected,
              id: containerElement.id,
              width: containerRect.width,
              height: containerRect.height,
              hasDimensions: containerRect.width > 0 && containerRect.height > 0,
              containerId
            })
            
            if (containerRect.width === 0 || containerRect.height === 0) {
              console.warn('⚠️ Container has zero dimensions - ONLYOFFICE may not render!')
            }
            
            // Log full config for debugging (redact token)
            const configForDebug = JSON.parse(JSON.stringify(editorConfig))
            if (configForDebug.token) {
              configForDebug.token = '[REDACTED]'
            }
            console.log('Creating ONLYOFFICE editor with config:', JSON.stringify(configForDebug, null, 2))
            
            docEditor = new window.DocsAPI.DocEditor(containerId, editorConfig)
            editorInstanceRef.current = docEditor
            
            console.log('✅ Editor instance created successfully', {
              hasEvents: !!docEditor?.events,
              hasDestroy: typeof docEditor?.destroy === 'function',
              editorType: typeof docEditor,
              editorKeys: docEditor ? Object.keys(docEditor) : [],
              editorValue: docEditor
            })
            
            // Set loading to false after editor creation to hide loading spinner
            // This ensures loading is hidden even if events aren't available
            setTimeout(() => {
              if (editorRef.current) {
                const iframes = editorRef.current.querySelectorAll('iframe')
                if (iframes.length > 0 || editorRef.current.children.length > 0) {
                  console.log('✅ Editor iframe/content detected immediately - hiding loading')
                }
              }
              console.log('Hiding loading after editor creation')
              setLoading(false)
            }, 500)
            
            // Check for errors in the editor object
            if (docEditor && typeof docEditor === 'object') {
              // Check if there's an error property
              const errorProps = Object.keys(docEditor).filter(key => 
                key.toLowerCase().includes('error') || 
                key.toLowerCase().includes('fail') ||
                key.toLowerCase().includes('message')
              )
              if (errorProps.length > 0) {
                console.warn('Editor object has potential error properties:', errorProps)
                errorProps.forEach(prop => {
                  console.warn(`  ${prop}:`, docEditor[prop])
                })
              }
            }
          } catch (editorError: any) {
            console.error('Error during editor creation:', editorError)
            console.error('Editor error details:', {
              message: editorError?.message,
              stack: editorError?.stack,
              name: editorError?.name
            })
            setError(`Failed to create editor: ${editorError?.message || 'Unknown error'}`)
            setLoading(false)
            return
          }
          
          // Check if editor container has content after initialization
          // Check multiple times to catch delayed rendering
          const checkRendering = (attempt: number) => {
            if (editorRef.current) {
              const iframes = editorRef.current.querySelectorAll('iframe')
              const hasContent = editorRef.current.children.length > 0 || editorRef.current.innerHTML.trim().length > 0
              const hasIframe = iframes.length > 0
              
              console.log(`Editor container check (attempt ${attempt}):`, {
                hasChildren: editorRef.current.children.length,
                iframeCount: iframes.length,
                hasIframe: hasIframe,
                innerHTML: editorRef.current.innerHTML.substring(0, 200),
                hasContent: hasContent,
                containerDimensions: {
                  width: editorRef.current.offsetWidth,
                  height: editorRef.current.offsetHeight,
                  clientWidth: editorRef.current.clientWidth,
                  clientHeight: editorRef.current.clientHeight
                }
              })
              
              if (hasIframe) {
                console.log('✅ Editor iframe detected - editor is rendering!')
                setLoading(false)
              } else if (attempt < 5) {
                // Check again after delay
                setTimeout(() => checkRendering(attempt + 1), 1000)
              } else {
                console.warn('⚠️ No iframe detected after multiple checks - editor may not be rendering')
                setLoading(false) // Still hide loading to show container
              }
            }
          }
          
          // Start checking after initial delay
          setTimeout(() => checkRendering(1), 1000)
        } catch (initError: any) {
          console.error('Error creating editor instance:', initError)
          setError(`Failed to create editor: ${initError.message || 'Unknown error'}`)
          setLoading(false)
          return
        }

        // Check if editor was created
        if (!docEditor) {
          console.error('Editor instance is null or undefined')
          setError('Failed to create editor instance')
          setLoading(false)
          return
        }

        // Try to set up events immediately, with fallback
        const setupEvents = () => {
          // Check if events are available - try different ways to access events
          let events = docEditor.events
          
          // Some versions of ONLYOFFICE might have events in a different location
          if (!events && docEditor.constructor && docEditor.constructor.prototype) {
            events = docEditor.constructor.prototype.events
          }
          
          // Check if events are available
          if (events && typeof events.on === 'function') {
            try {
              events.on('documentReady', () => {
                setLoading(false)
                console.log('ONLYOFFICE editor ready')
              })

              events.on('documentStateChange', (event: any) => {
                console.log('Document state changed', event)
                // Status 1 = document ready for editing
                // Status 2 = document is being saved (autosave)
                // Status 6 = document is being force saved (manual save)
                // Status 7 = document save error
                
                // Trigger refresh when document is saved (status 2 or 6)
                if (event && (event === 2 || event === 6)) {
                  console.log('Document saved, triggering refresh')
                  if (onSave) {
                    onSave()
                  }
                }
              })

              events.on('onRequestSave', (event: any) => {
                console.log('Save requested', event)
                if (onSave) {
                  onSave()
                }
              })

              events.on('onError', (event: any) => {
                console.error('ONLYOFFICE error:', event)
                setError(`Editor error: ${event}`)
                setLoading(false)
              })
              
              console.log('Editor events registered successfully')
            } catch (eventError: any) {
              console.warn('Error registering editor events:', eventError)
              // Continue anyway - editor might still work
              setTimeout(() => setLoading(false), 2000)
            }
          } else {
            console.warn('Editor events not available', {
              hasEvents: !!docEditor.events,
              eventsType: typeof docEditor.events,
              eventsKeys: docEditor.events ? Object.keys(docEditor.events) : [],
              fullEditorKeys: Object.keys(docEditor),
              editorPrototype: Object.getPrototypeOf(docEditor) ? Object.keys(Object.getPrototypeOf(docEditor)) : []
            })
            
            // Check if editor is rendering even without events
            // The editor might still work, just without event callbacks
            setTimeout(() => {
              // Check if iframe or content was created
              if (editorRef.current) {
                const iframes = editorRef.current.querySelectorAll('iframe')
                const hasIframe = iframes.length > 0
                console.log('Editor rendering check:', {
                  hasIframe: hasIframe,
                  iframeCount: iframes.length,
                  containerHTML: editorRef.current.innerHTML.substring(0, 200)
                })
                
                if (hasIframe) {
                  console.log('✅ Editor iframe detected - editor is rendering!')
                  // Loading already set to false above, but set it again to be sure
                  setLoading(false)
                } else {
                  console.warn('⚠️ No iframe detected - but loading already hidden')
                  // Loading already set to false above
                }
              }
              // Loading already set to false above, no need to set here
            }, 2000)
          }
        }

        // Try to set up events immediately
        setupEvents()
        
        // Also try after a short delay in case events become available later
        setTimeout(setupEvents, 500)
      } catch (err: any) {
        console.error('Failed to initialize ONLYOFFICE editor:', err)
        setError(`Failed to initialize editor: ${err.message || 'Unknown error'}`)
        setLoading(false)
      }
    }

    loadEditor()

    return () => {
      // Cleanup editor instance
      if (editorInstanceRef.current) {
        try {
          editorInstanceRef.current.destroy()
          editorInstanceRef.current = null
        } catch (e) {
          console.debug('Error destroying editor:', e)
        }
      }

      // Cleanup script tag - only remove if we added it and it still exists
      if (scriptRef.current) {
        try {
          // Check if script is still in the DOM before removing
          const script = scriptRef.current
          if (script.parentNode) {
            // Use contains to verify it's actually a child
            if (script.parentNode.contains(script)) {
              script.parentNode.removeChild(script)
            }
          }
        } catch (e) {
          // Script may have already been removed, ignore error
          console.debug('Script cleanup: node already removed', e)
        }
        scriptRef.current = null
      }

      // Note: we intentionally do NOT manually clear editorRef children here.
      // ONLYOFFICE manages the DOM inside this container, and React should not
      // try to reconcile or manipulate those child nodes.
    }
  }, [agreementId, templateId, configEndpoint, apiBase])
  // NOTE: onSave is intentionally NOT in dependencies to prevent remounting
  // The onSave callback is stable and doesn't need to trigger editor reload

  if (error) {
    return (
      <div className="flex items-center justify-center h-full p-8">
        <div className="text-center">
          <div className="text-red-600 mb-2">⚠️ Error</div>
          <div className="text-sm text-gray-600">{error}</div>
        </div>
      </div>
    )
  }

  return (
    <div
      className="flex flex-col h-full w-full"
      // Ensure the editor area has enough vertical space and can scroll
      style={{ minHeight: '700px' }}
    >
      {loading && (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
            <div className="text-sm text-gray-600">Loading editor...</div>
          </div>
        </div>
      )}
      {!canEdit && (
        <div className="border-b border-yellow-200 p-2 bg-yellow-50 text-xs text-yellow-800 text-center">
          Editor is in read-only mode. Editing is not allowed for this status.
        </div>
      )}
      {/* ONLYOFFICE container - React should not manage children */}
      <div
        className="flex-1 w-full"
        style={{ 
          minHeight: '600px', 
          height: '100%',
          width: '100%', 
          position: 'relative', 
          display: 'flex', 
          flexDirection: 'column' 
        }}
      >
        <div
          // FIX: Make ID dynamic so React Strict Mode doesn't cause DOM collisions
          id={`onlyoffice-editor-${templateId || agreementId || 'fallback'}`}
          ref={editorRef}
          style={{ 
            width: '100%', 
            height: '100%', 
            minHeight: '600px',
            flex: '1 1 auto',
            position: 'relative',
            display: 'block',
            overflow: 'hidden'
          }}
        />
      </div>
    </div>
  )
}

// Extend Window interface for ONLYOFFICE
declare global {
  interface Window {
    DocsAPI: {
      DocEditor: new (id: string, config: any) => {
        events: {
          on: (event: string, callback: (data?: any) => void) => void
        }
      }
    }
  }
}

export default OnlyOfficeEditor
