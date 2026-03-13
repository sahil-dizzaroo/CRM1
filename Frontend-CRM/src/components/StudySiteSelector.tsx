import React from 'react'
import { useStudySite } from '../contexts/StudySiteContext'

const StudySiteSelector: React.FC = () => {
  const {
    studies,
    filteredSites,
    selectedStudyId,
    selectedSiteId,
    setSelectedStudyId,
    setSelectedSiteId,
    loading
  } = useStudySite()

  return (
    <div className="flex flex-wrap items-center gap-4 p-4 bg-gradient-to-r from-dizzaroo-deep-blue/10 to-dizzaroo-blue-green/10 rounded-xl border-2 border-dizzaroo-deep-blue/20 shadow-lg">
      <div className="flex-1 min-w-[250px]">
        <label className="block text-sm font-semibold text-gray-800 mb-2">
          📊 Select Study
        </label>
        <select
          value={selectedStudyId || ''}
          onChange={(e) => setSelectedStudyId(e.target.value || null)}
          disabled={loading || studies.length === 0}
          className="w-full px-4 py-2.5 bg-white border-2 border-gray-300 rounded-xl text-gray-900 font-medium focus:ring-2 focus:ring-dizzaroo-deep-blue focus:border-dizzaroo-deep-blue disabled:bg-gray-200 disabled:cursor-not-allowed shadow-sm"
        >
          <option value="">-- Select Study --</option>
          {studies.map((study) => (
            <option key={study.id} value={study.id}>
              {study.name}
            </option>
          ))}
        </select>
        {studies.length === 0 && !loading && (
          <p className="text-xs text-gray-600 mt-1 italic">No studies available</p>
        )}
      </div>

      <div className="flex-1 min-w-[250px]">
        <label className="block text-sm font-semibold text-gray-800 mb-2">
          🏥 Select Site
        </label>
        <select
          value={selectedSiteId || ''}
          onChange={(e) => setSelectedSiteId(e.target.value || null)}
          disabled={loading || !selectedStudyId || filteredSites.length === 0}
          className="w-full px-4 py-2.5 bg-white border-2 border-gray-300 rounded-xl text-gray-900 font-medium focus:ring-2 focus:ring-dizzaroo-deep-blue focus:border-dizzaroo-deep-blue disabled:bg-gray-200 disabled:cursor-not-allowed shadow-sm"
        >
          <option value="">-- Select Site --</option>
          {filteredSites.map((site) => (
            <option key={site.id} value={site.site_id}>
              {site.name} {site.code ? `(${site.code})` : ''}
            </option>
          ))}
        </select>
        {!selectedStudyId && (
          <p className="text-xs text-gray-600 mt-1 italic">Select a study first</p>
        )}
        {selectedStudyId && filteredSites.length === 0 && !loading && (
          <p className="text-xs text-gray-600 mt-1 italic">No sites available for this study</p>
        )}
      </div>

      {!selectedStudyId || !selectedSiteId ? (
        <div className="w-full text-sm text-gray-800 font-medium mt-2 p-3 bg-yellow-100 border border-yellow-300 rounded-lg">
          ⚠️ Please select both a study and a site to view content
        </div>
      ) : (
        <div className="w-full text-sm text-green-800 font-medium mt-2 p-3 bg-green-100 border border-green-300 rounded-lg">
          ✅ Ready to view content for selected study and site
        </div>
      )}
    </div>
  )
}

export default StudySiteSelector

