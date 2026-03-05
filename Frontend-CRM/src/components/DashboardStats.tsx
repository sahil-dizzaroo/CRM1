import React from 'react'
import { Stats } from '../types'

interface DashboardStatsProps {
  stats: Stats
}

const DashboardStats: React.FC<DashboardStatsProps> = ({ stats }) => {
  if (!stats) return null

  const channelColors = {
    sms: '#1E73BE', // Dizzaroo Deep Blue
    whatsapp: '#25D366',
    email: '#168AAD' // Dizzaroo Blue Green
  }

  const statusColors = {
    queued: '#ffc107',
    sent: '#17a2b8',
    delivered: '#28a745',
    failed: '#dc3545'
  }

  return (
    <div className="flex gap-2 items-center">
      <div className="px-3 py-1.5 bg-gradient-to-br from-dizzaroo-deep-blue to-dizzaroo-blue-green text-white rounded-lg shadow-sm">
        <div className="text-lg font-bold">{stats.total_conversations}</div>
        <div className="text-[10px] uppercase font-semibold opacity-90">Conversations</div>
      </div>
      
      <div className="px-3 py-1.5 bg-gradient-to-br from-dizzaroo-deep-blue to-dizzaroo-blue-green text-white rounded-lg shadow-sm">
        <div className="text-lg font-bold">{stats.total_messages}</div>
        <div className="text-[10px] uppercase font-semibold opacity-90">Messages</div>
      </div>

      <div className="px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-lg shadow-sm">
        <div className="text-[10px] text-gray-600 uppercase font-bold mb-0.5">By Channel</div>
        <div className="flex gap-1.5">
          {Object.entries(stats.by_channel || {}).map(([channel, count]) => (
            <div key={channel} className="flex items-center gap-1">
              <span 
                className="px-1.5 py-0.5 rounded text-white text-[10px] font-bold"
                style={{ backgroundColor: channelColors[channel] || '#666' }}
              >
                {channel.toUpperCase()}
              </span>
              <span className="font-bold text-xs text-gray-800">{count}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-lg shadow-sm">
        <div className="text-[10px] text-gray-600 uppercase font-bold mb-0.5">By Status</div>
        <div className="flex gap-1.5">
          {Object.entries(stats.by_status || {}).map(([status, count]) => (
            <div key={status} className="flex items-center gap-1">
              <span 
                className="px-1.5 py-0.5 rounded text-white text-[10px] font-bold"
                style={{ backgroundColor: statusColors[status] || '#666' }}
              >
                {status}
              </span>
              <span className="font-bold text-xs text-gray-800">{count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default DashboardStats

