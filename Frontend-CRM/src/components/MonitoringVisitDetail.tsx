import React, { useState, useMemo, useEffect } from 'react'
import { api } from '../lib/api'
import {
  MonitoringVisit,
  MonitoringIssue,
  MonitoringChecklistItem,
  MonitoringReport,
} from '../types'

interface MonitoringVisitDetailProps {
  visit: MonitoringVisit
  onBack: () => void
}

const MonitoringVisitDetail: React.FC<MonitoringVisitDetailProps> = ({
  visit,
  onBack,
}) => {
  const [activeSection, setActiveSection] = useState<
    'overview' | 'issues' | 'checklist' | 'notes' | 'report'
  >('overview')
  const [reportStatus, setReportStatus] = useState<string>('draft')
  const [reportData, setReportData] = useState<MonitoringReport | null>(null)
  const [visitNotes, setVisitNotes] = useState<string>(visit.notes || '')
  const [checklistItems, setChecklistItems] = useState<MonitoringChecklistItem[]>([])
  const [showAddChecklistModal, setShowAddChecklistModal] = useState(false)
  const [newChecklistTitle, setNewChecklistTitle] = useState('')
  const [newChecklistDescription, setNewChecklistDescription] = useState('')

  const [linkedIssues, setLinkedIssues] = useState<MonitoringIssue[]>([])

  // Load data for this visit
  useEffect(() => {
    const fetchData = async () => {
      // Load linked issues
      if (visit.linkedIssueIds && visit.linkedIssueIds.length > 0) {
        try {
          const issuesResponse = await api.get('/api/monitoring/issues')
          const allIssues = issuesResponse.data || []
          const linked = allIssues.filter((issue: MonitoringIssue) =>
            visit.linkedIssueIds?.includes(issue.id)
          )
          setLinkedIssues(linked)
        } catch (err) {
          console.warn('Failed to fetch linked issues:', err)
          setLinkedIssues([])
        }
      } else {
        setLinkedIssues([])
      }

      // Load checklist items
      try {
        const checklistResponse = await api.get(`/api/monitoring/visits/${visit.id}/checklist`)
        setChecklistItems(checklistResponse.data || [])
      } catch (err) {
        console.warn('Failed to fetch checklist items:', err)
        setChecklistItems([])
      }

      // Load report if exists
      if (visit.reportId) {
        try {
          const reportResponse = await api.get(`/api/monitoring/reports/${visit.reportId}`)
          const report = reportResponse.data
          if (report) {
            setReportData(report)
            setReportStatus(report.status)
          }
        } catch (err) {
          console.warn('Failed to fetch report:', err)
        }
      }
    }

    fetchData()
  }, [visit])

  // Tasks are now managed in the separate Tasks tab

  const formatDate = (date: string | Date) => {
    return new Date(date).toLocaleDateString()
  }

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

  const handleStartVisit = () => {
    // TODO: Update visit status to 'in-progress' via API
    alert('Visit started - TODO: Implement API call')
  }

  const handleCreateReport = () => {
    const newReport: MonitoringReport = {
      id: `report-${Date.now()}`,
      visitId: visit.id,
      siteId: visit.siteId,
      status: 'draft',
      overview: '',
      dataQualityFindings: '',
      protocolDeviations: '',
      patientSafetyFindings: '',
      otherNotes: '',
      createdAt: new Date().toISOString(),
    }
    setReportData(newReport)
    setReportStatus('draft')
    setActiveSection('report')
  }

  const handleSubmitReport = () => {
    if (reportData) {
      setReportStatus('submitted')
      // TODO: Update report via API
      alert('Report submitted - TODO: Implement API call')
    }
  }

  const handleApproveReport = () => {
    if (reportData) {
      setReportStatus('approved')
      // TODO: Update report via API
      alert('Report approved - TODO: Implement API call')
    }
  }

  const handleRequestChanges = () => {
    if (reportData) {
      setReportStatus('needs-changes')
      // TODO: Update report via API
      alert('Changes requested - TODO: Implement API call')
    }
  }

  const handleAddChecklistItem = () => {
    if (!newChecklistTitle.trim()) return

    const newItem: MonitoringChecklistItem = {
      id: `checklist-${Date.now()}`,
      visitId: visit.id,
      title: newChecklistTitle,
      description: newChecklistDescription || undefined,
      status: 'pending',
    }

    setChecklistItems([...checklistItems, newItem])
    setNewChecklistTitle('')
    setNewChecklistDescription('')
    setShowAddChecklistModal(false)
    // TODO: Save to API
  }

  const handleAddChecklistFromIssue = (issueId: string) => {
    const issue = linkedIssues.find((i) => i.id === issueId)
    if (!issue) return

    const newItem: MonitoringChecklistItem = {
      id: `checklist-${Date.now()}`,
      visitId: visit.id,
      title: `${issue.category}: ${issue.description.substring(0, 50)}`,
      description: issue.description,
      sourceIssueId: issueId,
      status: 'pending',
    }

    setChecklistItems([...checklistItems, newItem])
    // TODO: Save to API
  }

  const handleUpdateChecklistStatus = (itemId: string, newStatus: string) => {
    setChecklistItems(
      checklistItems.map((item) =>
        item.id === itemId ? { ...item, status: newStatus as any } : item
      )
    )
    // TODO: Update via API
  }

  const handleSaveNotes = () => {
    // TODO: Save notes via API
    alert('Notes saved - TODO: Implement API call')
  }

  return (
    <div className="flex flex-col h-full bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-3">
        <button
          onClick={onBack}
          className="text-dizzaroo-deep-blue hover:text-dizzaroo-blue-green mb-1 text-xs font-medium flex items-center gap-1"
        >
          ← Back to Monitoring
        </button>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-base font-semibold text-gray-900">
              {visit.siteName} - Visit {visit.visitNumber}
            </h1>
            <span className="text-xs text-gray-600">
              📅 {formatDate(visit.plannedDate)}
            </span>
            {visit.actualDate && (
              <span className="text-xs text-gray-600">
                ✅ {formatDate(visit.actualDate)}
              </span>
            )}
            {visit.craName && (
              <span className="text-xs text-gray-600">👤 {visit.craName}</span>
            )}
            <span
              className={`px-1.5 py-0.5 rounded text-xs font-medium border ${getStatusColor(
                visit.status
              )}`}
            >
              {visit.status.replace('-', ' ')}
            </span>
          </div>
          <div className="flex gap-2">
            {visit.status === 'planned' && (
              <button
                onClick={handleStartVisit}
                className="px-2.5 py-1 bg-dizzaroo-deep-blue text-white rounded-lg hover:bg-dizzaroo-blue-green transition text-xs font-medium"
              >
                Start Visit
              </button>
            )}
            {visit.status === 'in-progress' && (
              <button
                onClick={() => setActiveSection('report')}
                className="px-2.5 py-1 bg-dizzaroo-deep-blue text-white rounded-lg hover:bg-dizzaroo-blue-green transition text-xs font-medium"
              >
                Open Report
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Section Tabs */}
      <div className="flex gap-1 mb-4 border-b border-gray-200 overflow-x-auto">
        {[
          { id: 'overview', label: 'Overview' },
          { id: 'issues', label: 'Issues' },
          { id: 'checklist', label: 'Checklist' },
          { id: 'notes', label: 'Notes' },
          { id: 'report', label: 'Report' },
        ].map((section) => (
          <button
            key={section.id}
            onClick={() => setActiveSection(section.id as any)}
            className={`px-2 py-1 font-medium text-xs transition-colors whitespace-nowrap ${
              activeSection === section.id
                ? 'text-dizzaroo-deep-blue border-b-2 border-dizzaroo-deep-blue'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {section.label}
          </button>
        ))}
      </div>

      {/* Content Sections */}
      <div className="flex-1 overflow-y-auto">
        {activeSection === 'overview' && (
          <div className="space-y-4">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4">Visit Summary</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-1">
                    Linked Issues
                  </div>
                  <div className="text-2xl font-bold text-blue-800">
                    {linkedIssues.length}
                  </div>
                </div>
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="text-xs font-semibold text-green-600 uppercase tracking-wide mb-1">
                    Checklist Items
                  </div>
                  <div className="text-2xl font-bold text-green-800">
                    {checklistItems.length}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeSection === 'issues' && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">Linked Issues</h2>
            {linkedIssues.length === 0 ? (
              <p className="text-gray-500">No issues linked to this visit.</p>
            ) : (
              <div className="space-y-3">
                {linkedIssues.map((issue) => (
                  <div
                    key={issue.id}
                    className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-2 py-1 rounded text-xs font-medium border ${getSeverityColor(
                            issue.severity
                          )}`}
                        >
                          {issue.severity}
                        </span>
                        <span className="text-sm font-semibold text-gray-800">
                          {issue.category}
                        </span>
                      </div>
                      <button
                        onClick={() => handleAddChecklistFromIssue(issue.id)}
                        className="px-3 py-1 bg-dizzaroo-deep-blue text-white rounded-lg hover:bg-dizzaroo-blue-green transition text-xs font-medium"
                      >
                        Add to Checklist
                      </button>
                    </div>
                    <p className="text-sm text-gray-700 mb-2">{issue.description}</p>
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span>Detected: {formatDate(issue.detectedAt)}</span>
                      <span
                        className={`px-2 py-0.5 rounded ${
                          issue.status === 'open'
                            ? 'bg-red-100 text-red-800'
                            : issue.status === 'resolved'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}
                      >
                        {issue.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeSection === 'checklist' && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-800">Checklist</h2>
              <button
                onClick={() => setShowAddChecklistModal(true)}
                className="px-4 py-2 bg-dizzaroo-deep-blue text-white rounded-lg hover:bg-dizzaroo-blue-green transition font-medium"
              >
                + Add Checklist Item
              </button>
            </div>
            {checklistItems.length === 0 ? (
              <p className="text-gray-500">No checklist items yet.</p>
            ) : (
              <div className="space-y-3">
                {checklistItems.map((item) => (
                  <div
                    key={item.id}
                    className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold text-gray-800">{item.title}</h3>
                          {item.sourceIssueId && (
                            <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs">
                              From issue
                            </span>
                          )}
                        </div>
                        {item.description && (
                          <p className="text-sm text-gray-600 mb-2">{item.description}</p>
                        )}
                        <select
                          value={item.status}
                          onChange={(e) =>
                            handleUpdateChecklistStatus(item.id, e.target.value)
                          }
                          className="px-2 py-1 border border-gray-300 rounded text-sm"
                        >
                          <option value="pending">Pending</option>
                          <option value="in-progress">In Progress</option>
                          <option value="done">Done</option>
                        </select>
                        {item.note && (
                          <div className="mt-2 p-2 bg-gray-50 rounded text-sm text-gray-700">
                            {item.note}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeSection === 'notes' && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">Visit Notes</h2>
            <textarea
              value={visitNotes}
              onChange={(e) => setVisitNotes(e.target.value)}
              className="w-full h-64 px-4 py-3 border-2 border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue focus:border-dizzaroo-deep-blue transition-all"
              placeholder="Enter visit notes here..."
            />
            <button
              onClick={handleSaveNotes}
              className="mt-4 px-4 py-2 bg-dizzaroo-deep-blue text-white rounded-lg hover:bg-dizzaroo-blue-green transition font-medium"
            >
              Save Notes
            </button>
          </div>
        )}

        {activeSection === 'report' && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            {!reportData ? (
              <div className="text-center py-8">
                <p className="text-gray-600 mb-4">No report created yet for this visit.</p>
                <button
                  onClick={handleCreateReport}
                  className="px-4 py-2 bg-dizzaroo-deep-blue text-white rounded-lg hover:bg-dizzaroo-blue-green transition font-medium"
                >
                  Create Report Draft
                </button>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-bold text-gray-800">Monitoring Report</h2>
                  <span
                    className={`px-3 py-1 rounded text-sm font-medium border ${getStatusColor(
                      reportStatus
                    )}`}
                  >
                    {reportStatus.replace('-', ' ')}
                  </span>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Overview
                    </label>
                    <textarea
                      value={reportData.overview}
                      onChange={(e) =>
                        setReportData({ ...reportData, overview: e.target.value })
                      }
                      disabled={reportStatus === 'approved' || reportStatus === 'submitted'}
                      className="w-full h-32 px-4 py-3 border-2 border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue focus:border-dizzaroo-deep-blue transition-all disabled:bg-gray-100"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Data Quality Findings
                    </label>
                    <textarea
                      value={reportData.dataQualityFindings}
                      onChange={(e) =>
                        setReportData({
                          ...reportData,
                          dataQualityFindings: e.target.value,
                        })
                      }
                      disabled={reportStatus === 'approved' || reportStatus === 'submitted'}
                      className="w-full h-32 px-4 py-3 border-2 border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue focus:border-dizzaroo-deep-blue transition-all disabled:bg-gray-100"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Protocol Deviations
                    </label>
                    <textarea
                      value={reportData.protocolDeviations}
                      onChange={(e) =>
                        setReportData({
                          ...reportData,
                          protocolDeviations: e.target.value,
                        })
                      }
                      disabled={reportStatus === 'approved' || reportStatus === 'submitted'}
                      className="w-full h-32 px-4 py-3 border-2 border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue focus:border-dizzaroo-deep-blue transition-all disabled:bg-gray-100"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Patient Safety Findings
                    </label>
                    <textarea
                      value={reportData.patientSafetyFindings}
                      onChange={(e) =>
                        setReportData({
                          ...reportData,
                          patientSafetyFindings: e.target.value,
                        })
                      }
                      disabled={reportStatus === 'approved' || reportStatus === 'submitted'}
                      className="w-full h-32 px-4 py-3 border-2 border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue focus:border-dizzaroo-deep-blue transition-all disabled:bg-gray-100"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Other Notes
                    </label>
                    <textarea
                      value={reportData.otherNotes || ''}
                      onChange={(e) =>
                        setReportData({ ...reportData, otherNotes: e.target.value })
                      }
                      disabled={reportStatus === 'approved' || reportStatus === 'submitted'}
                      className="w-full h-32 px-4 py-3 border-2 border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue focus:border-dizzaroo-deep-blue transition-all disabled:bg-gray-100"
                    />
                  </div>
                </div>

                <div className="flex gap-3 pt-4 border-t border-gray-200">
                  {reportStatus === 'draft' && (
                    <button
                      onClick={handleSubmitReport}
                      className="px-4 py-2 bg-dizzaroo-deep-blue text-white rounded-lg hover:bg-dizzaroo-blue-green transition font-medium"
                    >
                      Submit for Approval
                    </button>
                  )}
                  {reportStatus === 'submitted' && (
                    <>
                      <button
                        onClick={handleApproveReport}
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium"
                      >
                        Approve
                      </button>
                      <button
                        onClick={handleRequestChanges}
                        className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition font-medium"
                      >
                        Request Changes
                      </button>
                    </>
                  )}
                  {reportStatus === 'needs-changes' && (
                    <button
                      onClick={handleSubmitReport}
                      className="px-4 py-2 bg-dizzaroo-deep-blue text-white rounded-lg hover:bg-dizzaroo-blue-green transition font-medium"
                    >
                      Re-submit
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

      </div>

      {/* Add Checklist Modal */}
      {showAddChecklistModal && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => setShowAddChecklistModal(false)}
        >
          <div
            className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-bold text-gray-800 mb-4">Add Checklist Item</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Title *
                </label>
                <input
                  type="text"
                  value={newChecklistTitle}
                  onChange={(e) => setNewChecklistTitle(e.target.value)}
                  className="w-full px-3 py-2 border-2 border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue focus:border-dizzaroo-deep-blue transition-all"
                  placeholder="Enter checklist item title"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={newChecklistDescription}
                  onChange={(e) => setNewChecklistDescription(e.target.value)}
                  className="w-full px-3 py-2 border-2 border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue focus:border-dizzaroo-deep-blue transition-all"
                  placeholder="Enter description (optional)"
                  rows={3}
                />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={handleAddChecklistItem}
                className="flex-1 px-4 py-2 bg-dizzaroo-deep-blue text-white rounded-lg hover:bg-dizzaroo-blue-green transition font-medium"
              >
                Add Item
              </button>
              <button
                onClick={() => setShowAddChecklistModal(false)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition font-medium"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default MonitoringVisitDetail

