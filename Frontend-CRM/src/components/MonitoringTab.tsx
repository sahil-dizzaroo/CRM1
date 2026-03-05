import React, { useState, useMemo, useEffect } from 'react'
import { useStudySite } from '../contexts/StudySiteContext'
import { api } from '../lib/api'
import {
  MonitoringVisit,
  MonitoringIssue,
  MonitoringTask,
} from '../types'
import MonitoringVisitDetail from './MonitoringVisitDetail'

type TabType = 'visits' | 'issues'

const MonitoringTab: React.FC = () => {
  const { selectedStudyId, selectedSiteId, filteredSites } = useStudySite()
  const [activeTab, setActiveTab] = useState<TabType>('visits')
  const [selectedVisit, setSelectedVisit] = useState<MonitoringVisit | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [siteFilter, setSiteFilter] = useState<string>('')
  const [visits, setVisits] = useState<MonitoringVisit[]>([])
  const [issues, setIssues] = useState<MonitoringIssue[]>([])
  const [tasks, setTasks] = useState<MonitoringTask[]>([])
  const [loading, setLoading] = useState(false)

  // Fetch data from API
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        // Fetch visits
        try {
          const visitsResponse = await api.get('/api/monitoring/visits')
          setVisits(visitsResponse.data || [])
        } catch (err) {
          console.warn('Monitoring visits API not available:', err)
          setVisits([])
        }

        // Fetch issues
        try {
          const issuesParams: any = {}
          if (selectedStudyId) issuesParams.study_id = selectedStudyId
          if (selectedSiteId) issuesParams.site_id = selectedSiteId
          const issuesResponse = await api.get('/api/monitoring/issues', {
            params: issuesParams,
          })
          setIssues(issuesResponse.data || [])
        } catch (err) {
          console.warn('Monitoring issues API not available:', err)
          setIssues([])
        }

        // Fetch tasks
        try {
          const tasksResponse = await api.get('/api/monitoring/tasks')
          setTasks(tasksResponse.data || [])
        } catch (err) {
          console.warn('Monitoring tasks API not available:', err)
          setTasks([])
        }
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [selectedStudyId, selectedSiteId])

  // Filter visits data
  const filteredVisits = useMemo(() => {
    let data = visits

    // Filter by selected site if available
    if (selectedSiteId) {
      data = data.filter((item) => item.siteId === selectedSiteId)
    }

    // Apply site filter
    if (siteFilter) {
      data = data.filter((item) => item.siteId === siteFilter)
    }

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      data = data.filter((item) =>
        item.siteName.toLowerCase().includes(query)
      )
    }

    // Apply status filter
    if (statusFilter) {
      data = data.filter((item) => item.status === statusFilter)
    }

    return data
  }, [visits, selectedSiteId, searchQuery, statusFilter, siteFilter])

  // Filter issues data
  const filteredIssues = useMemo(() => {
    let data = issues

    // Filter by selected site if available
    if (selectedSiteId) {
      data = data.filter((item) => item.siteId === selectedSiteId)
    }

    // Apply site filter
    if (siteFilter) {
      data = data.filter((item) => item.siteId === siteFilter)
    }

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      data = data.filter(
        (item) =>
          item.siteName.toLowerCase().includes(query) ||
          item.description.toLowerCase().includes(query) ||
          item.category.toLowerCase().includes(query)
      )
    }

    return data
  }, [issues, selectedSiteId, searchQuery, siteFilter])

  // Calculate summary statistics
  const summaryStats = useMemo(() => {
    const now = new Date()
    const upcomingVisits = filteredVisits.filter(
      (v) =>
        v.status === 'planned' &&
        new Date(v.plannedDate) >= now
    ).length

    const pendingReports = filteredVisits.filter(
      (v) => v.status === 'report-pending'
    ).length

    const openIssues = filteredIssues.filter(
      (i) => i.status === 'open'
    ).length

    const openTasks = tasks.filter(
      (t) => t.status === 'open' || t.status === 'in-progress'
    ).length

    return {
      upcomingVisits,
      pendingReports,
      openIssues,
      openTasks,
    }
  }, [filteredVisits, filteredIssues, tasks])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'planned':
        return 'bg-blue-100 text-blue-800 border-blue-300'
      case 'in-progress':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'report-pending':
        return 'bg-orange-100 text-orange-800 border-orange-300'
      case 'submitted':
        return 'bg-purple-100 text-purple-800 border-purple-300'
      case 'approved':
        return 'bg-green-100 text-green-800 border-green-300'
      case 'needs-changes':
        return 'bg-red-100 text-red-800 border-red-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-300'
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-300'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'low':
        return 'bg-blue-100 text-blue-800 border-blue-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const formatDate = (date: string | Date) => {
    return new Date(date).toLocaleDateString()
  }

  if (!selectedStudyId || !selectedSiteId) {
    return (
      <div className="flex items-center justify-center h-full p-8">
        <div className="text-center">
          <div className="text-6xl mb-4">🔍</div>
          <h2 className="text-2xl font-semibold text-gray-800 mb-2">Monitoring</h2>
          <p className="text-gray-600">
            Please select a Study and Site to view Monitoring.
          </p>
        </div>
      </div>
    )
  }

  if (selectedVisit) {
    return (
      <MonitoringVisitDetail
        visit={selectedVisit}
        onBack={() => setSelectedVisit(null)}
      />
    )
  }

  return (
    <div className="flex flex-col h-full bg-gray-50 p-6">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Monitoring</h1>
        <p className="text-gray-600">
          Plan and track on-site monitoring visits, issues, and reports.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-4 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('visits')}
          className={`px-2 py-1 font-medium text-xs transition-colors ${
            activeTab === 'visits'
              ? 'text-dizzaroo-deep-blue border-b-2 border-dizzaroo-deep-blue'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Visits
        </button>
        <button
          onClick={() => setActiveTab('issues')}
          className={`px-2 py-1 font-medium text-xs transition-colors ${
            activeTab === 'issues'
              ? 'text-dizzaroo-deep-blue border-b-2 border-dizzaroo-deep-blue'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Incoming Issues
        </button>
      </div>

      {/* Filter Bar */}
      <div className="bg-white rounded-lg shadow-sm p-4 mb-6 border border-gray-200">
        <div className="flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
              Search
            </label>
            <input
              type="text"
              placeholder="🔍 Search by site name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3 py-2 border-2 border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue focus:border-dizzaroo-deep-blue transition-all"
            />
          </div>
          {activeTab === 'visits' && (
            <div className="min-w-[200px]">
              <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
                Status
              </label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-3 py-2 border-2 border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue focus:border-dizzaroo-deep-blue transition-all"
              >
                <option value="">All Statuses</option>
                <option value="planned">Planned</option>
                <option value="in-progress">In Progress</option>
                <option value="report-pending">Report Pending</option>
                <option value="submitted">Submitted</option>
                <option value="approved">Approved</option>
                <option value="needs-changes">Needs Changes</option>
              </select>
            </div>
          )}
          {filteredSites.length > 0 && (
            <div className="min-w-[200px]">
              <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
                Site
              </label>
              <select
                value={siteFilter}
                onChange={(e) => setSiteFilter(e.target.value)}
                className="w-full px-3 py-2 border-2 border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue focus:border-dizzaroo-deep-blue transition-all"
              >
                <option value="">All Sites</option>
                {filteredSites.map((site) => (
                  <option key={site.id} value={site.site_id}>
                    {site.name}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-gradient-to-br from-dizzaroo-deep-blue to-dizzaroo-blue-green text-white rounded-lg shadow-sm p-4">
          <div className="text-2xl font-bold">{summaryStats.upcomingVisits}</div>
          <div className="text-xs uppercase font-semibold opacity-90 mt-1">
            Upcoming Visits
          </div>
        </div>
        <div className="bg-gradient-to-br from-dizzaroo-deep-blue to-dizzaroo-blue-green text-white rounded-lg shadow-sm p-4">
          <div className="text-2xl font-bold">{summaryStats.pendingReports}</div>
          <div className="text-xs uppercase font-semibold opacity-90 mt-1">
            Pending Reports
          </div>
        </div>
        <div className="bg-gradient-to-br from-dizzaroo-deep-blue to-dizzaroo-blue-green text-white rounded-lg shadow-sm p-4">
          <div className="text-2xl font-bold">{summaryStats.openIssues}</div>
          <div className="text-xs uppercase font-semibold opacity-90 mt-1">
            Open Issues
          </div>
        </div>
        <div className="bg-gradient-to-br from-dizzaroo-deep-blue to-dizzaroo-blue-green text-white rounded-lg shadow-sm p-4">
          <div className="text-2xl font-bold">{summaryStats.openTasks}</div>
          <div className="text-xs uppercase font-semibold opacity-90 mt-1">
            Open Tasks
          </div>
        </div>
      </div>

      {/* Content Area */}
      {activeTab === 'visits' ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Site
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Visit #
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Planned Date
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Actual Date
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Open Issues
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Action Items
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredVisits.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                      <div className="text-4xl mb-2">📭</div>
                      <p>No monitoring visits found</p>
                      <p className="text-sm mt-1">
                        {searchQuery || statusFilter || siteFilter
                          ? 'Try adjusting your filters'
                          : 'No visits available for the selected site'}
                      </p>
                    </td>
                  </tr>
                ) : (
                  filteredVisits.map((visit) => (
                    <tr
                      key={visit.id}
                      onClick={() => setSelectedVisit(visit)}
                      className="hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">
                        {visit.siteName}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        Visit {visit.visitNumber}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {formatDate(visit.plannedDate)}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {visit.actualDate ? formatDate(visit.actualDate) : '—'}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <span
                          className={`px-2 py-1 rounded text-xs font-medium border ${getStatusColor(
                            visit.status
                          )}`}
                        >
                          {visit.status.replace('-', ' ')}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {visit.linkedIssueIds.length}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {visit.openActionItemsCount || 0}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Site
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Severity
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Detected At
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredIssues.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                      <div className="text-4xl mb-2">📭</div>
                      <p>No monitoring issues found</p>
                      <p className="text-sm mt-1">
                        {searchQuery || siteFilter
                          ? 'Try adjusting your filters'
                          : 'No issues available for the selected site'}
                      </p>
                    </td>
                  </tr>
                ) : (
                  filteredIssues.map((issue) => (
                    <tr key={issue.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">
                        {issue.siteName}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {issue.category}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <span
                          className={`px-2 py-1 rounded text-xs font-medium border ${getSeverityColor(
                            issue.severity
                          )}`}
                        >
                          {issue.severity}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 max-w-md">
                        <div className="truncate" title={issue.description}>
                          {issue.description.length > 60
                            ? `${issue.description.substring(0, 60)}...`
                            : issue.description}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {formatDate(issue.detectedAt)}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <span
                          className={`px-2 py-1 rounded text-xs font-medium border ${
                            issue.status === 'open'
                              ? 'bg-red-100 text-red-800 border-red-300'
                              : issue.status === 'in-progress'
                              ? 'bg-yellow-100 text-yellow-800 border-yellow-300'
                              : issue.status === 'resolved'
                              ? 'bg-green-100 text-green-800 border-green-300'
                              : 'bg-gray-100 text-gray-800 border-gray-300'
                          }`}
                        >
                          {issue.status.replace('-', ' ')}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            // TODO: Implement link to visit / create visit
                            alert('Link to visit / create visit - TODO: Implement')
                          }}
                          className="px-3 py-1 bg-dizzaroo-deep-blue text-white rounded-lg hover:bg-dizzaroo-blue-green transition text-xs font-medium"
                        >
                          Link to Visit
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

export default MonitoringTab

