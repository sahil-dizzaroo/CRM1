import React, { createContext, useContext, useState, useEffect, useMemo } from 'react'
// import axios from 'axios'
import { api } from '../lib/api'

import { useAuth } from './AuthContext'

interface Study {
  id: string
  study_id: string
  name: string
  description?: string
  status?: string
}

interface Site {
  id: string
  site_id: string
  study_id: string
  name: string
  code?: string
  location?: string
  principal_investigator?: string
  address?: string
  city?: string
  country?: string
  status?: string
}

interface StudySiteContextValue {
  studies: Study[]
  sites: Site[]
  selectedStudyId: string | null
  selectedSiteId: string | null
  setSelectedStudyId: (id: string | null) => void
  setSelectedSiteId: (id: string | null) => void
  filteredSites: Site[]
  loading: boolean
}

const StudySiteContext = createContext<StudySiteContextValue | undefined>(undefined)

export const useStudySite = () => {
  const context = useContext(StudySiteContext)
  if (!context) {
    throw new Error('useStudySite must be used within StudySiteProvider')
  }
  return context
}

// interface StudySiteProviderProps {
//   children: React.ReactNode
//   apiBase: string
// }
interface StudySiteProviderProps {
  children: React.ReactNode
}


export const StudySiteProvider: React.FC<StudySiteProviderProps> = ({ children }) => {
  const { token } = useAuth()
  const [studies, setStudies] = useState<Study[]>([])
  const [sites, setSites] = useState<Site[]>([])
  const [selectedStudyId, setSelectedStudyId] = useState<string | null>(null)
  const [selectedSiteId, setSelectedSiteId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  // const axiosInstance = useMemo(() => {
  //   return api.create({
  //     baseURL: apiBase,
  //     headers: {
  //       Authorization: `Bearer ${token}`
  //     }
  //   })
  // }, [apiBase, token])

  useEffect(() => {
    if (token) {
      loadStudies()
    }
  }, [token])

  useEffect(() => {
    if (token && selectedStudyId) {
      loadSites(selectedStudyId)
    } else {
      setSites([])
      setSelectedSiteId(null)
    }
  }, [token, selectedStudyId])

  const loadStudies = async () => {
    try {
      setLoading(true)
      const response = await api.get<Study[]>('/studies')
      setStudies(response.data)
    } catch (error) {
      console.error('Error loading studies:', error)
      setStudies([])
    } finally {
      setLoading(false)
    }
  }

  const loadSites = async (studyId: string) => {
    try {
      setLoading(true)
      // Backend now accepts both UUID (id) and study_id string
      const response = await api.get<Site[]>('/sites', {
        params: { study_id: studyId }
      })
      setSites(response.data)
      // Reset site selection if current site is not in the new list
      if (selectedSiteId) {
        const siteExists = response.data.some(s => s.id === selectedSiteId)
        if (!siteExists) {
          setSelectedSiteId(null)
        }
      }
    } catch (error) {
      console.error('Error loading sites:', error)
      setSites([])
    } finally {
      setLoading(false)
    }
  }

  const filteredSites = useMemo(() => {
    if (!selectedStudyId) return []
    // Find the selected study to get its study_id string identifier
    const selectedStudy = studies.find(s => s.id === selectedStudyId)
    if (!selectedStudy) return []
    
    // Backend returns site.study_id as study.study_id (string identifier, not UUID)
    // So we need to compare site.study_id with selectedStudy.study_id
    return sites.filter(site => {
      const siteStudyId = String(site.study_id || '')
      const studyIdString = String(selectedStudy.study_id || '')
      return siteStudyId === studyIdString
    })
  }, [sites, selectedStudyId, studies])

  const value: StudySiteContextValue = {
    studies,
    sites,
    selectedStudyId,
    selectedSiteId,
    setSelectedStudyId,
    setSelectedSiteId,
    filteredSites,
    loading
  }

  return <StudySiteContext.Provider value={value}>{children}</StudySiteContext.Provider>
}

