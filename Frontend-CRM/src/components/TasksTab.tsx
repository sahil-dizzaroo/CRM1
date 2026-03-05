import React, { useState, useEffect, useMemo } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useStudySite } from '../contexts/StudySiteContext'
import { api } from '../lib/api'
import { MonitoringTask, TaskStatus, TaskLinks } from '../types'
import TaskFormModal from './TaskFormModal'

const TasksTab: React.FC<{ apiBase: string }> = ({ apiBase }) => {
  const { selectedStudyId, selectedSiteId } = useStudySite()
  const { token, user } = useAuth()
  const [tasks, setTasks] = useState<MonitoringTask[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<TaskStatus | 'all'>('all')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedTask, setSelectedTask] = useState<MonitoringTask | null>(null)

  useEffect(() => {
    loadTasks()
  }, [selectedStudyId, selectedSiteId, statusFilter, token])

  const loadTasks = async () => {
    if (!selectedStudyId || !selectedSiteId) {
      setTasks([])
      return
    }

    setLoading(true)
    setError(null)

    try {
      const params: any = {
        siteId: selectedSiteId,
        limit: 100
      }

      if (statusFilter !== 'all') {
        params.status = statusFilter
      }

      const response = await api.get(`${apiBase}/tasks`, { params })
      setTasks(response.data || [])
    } catch (err: any) {
      console.error('Failed to load tasks:', err)
      setError(err.response?.data?.detail || 'Failed to load tasks')
      setTasks([])
    } finally {
      setLoading(false)
    }
  }

  const handleTaskCreated = (task: MonitoringTask) => {
    setTasks(prev => [task, ...prev])
    setShowCreateModal(false)
  }

  const handleTaskUpdated = async () => {
    await loadTasks()
    setSelectedTask(null)
  }

  const handleDeleteTask = async (taskId: string) => {
    if (!confirm('Are you sure you want to delete this task?')) {
      return
    }

    try {
      await api.delete(`${apiBase}/tasks/${taskId}`)
      setTasks(prev => prev.filter(t => t.id !== taskId))
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete task')
    }
  }

  const getStatusColor = (status: TaskStatus) => {
    switch (status) {
      case 'open':
        return 'bg-blue-100 text-blue-800 border-blue-300'
      case 'in-progress':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'done':
        return 'bg-green-100 text-green-800 border-green-300'
      case 'cancelled':
        return 'bg-gray-100 text-gray-800 border-gray-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const formatDate = (date: string | Date | undefined) => {
    if (!date) return 'No due date'
    return new Date(date).toLocaleDateString()
  }

  const filteredTasks = useMemo(() => {
    return tasks.filter(task => {
      if (task.links?.siteId === selectedSiteId) return true
      if (task.siteId === selectedSiteId) return true
      return false
    })
  }, [tasks, selectedSiteId])

  const tasksByStatus = useMemo(() => {
    const grouped: Record<TaskStatus, MonitoringTask[]> = {
      open: [],
      'in-progress': [],
      done: [],
      cancelled: []
    }

    filteredTasks.forEach(task => {
      if (task.status in grouped) {
        grouped[task.status as TaskStatus].push(task)
      }
    })

    return grouped
  }, [filteredTasks])

  if (!selectedStudyId || !selectedSiteId) {
    return (
      <div className="flex items-center justify-center h-full p-8">
        <div className="text-center">
          <div className="text-6xl mb-4">✓</div>
          <h2 className="text-2xl font-semibold text-gray-800 mb-2">Tasks</h2>
          <p className="text-gray-600">
            Please select a Study and Site to view Tasks.
          </p>
        </div>
      </div>
    )
  }



  return (
    <div className="flex flex-col h-full bg-gray-50 overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6" style={{ minHeight: 0 }}>
        {/* Header */}
        <div className="mb-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Tasks</h1>
            <p className="text-gray-600">
              Manage tasks and action items for this site.
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-dizzaroo-deep-blue text-white rounded-lg font-semibold hover:bg-dizzaroo-blue-green transition"
          >
            + Create Task
          </button>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-6 border border-gray-200">
          <div className="flex items-center gap-4">
            <label className="text-sm font-semibold text-gray-700">Filter by Status:</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as TaskStatus | 'all')}
              className="px-3 py-2 border-2 border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue focus:border-dizzaroo-deep-blue transition-all"
            >
              <option value="all">All Tasks</option>
              <option value="open">Open</option>
              <option value="in-progress">In Progress</option>
              <option value="done">Done</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-dizzaroo-deep-blue"></div>
            <span className="ml-3 text-gray-600">Loading tasks...</span>
          </div>
        )}

        {/* Tasks List */}
        {!loading && (
          <>
            {filteredTasks.length === 0 ? (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
                <div className="text-4xl mb-2">✓</div>
                <p className="text-gray-600">No tasks found</p>
                <p className="text-sm text-gray-500 mt-1">
                  Create a task to get started
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredTasks.map((task) => (
                  <div
                    key={task.id}
                    className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition cursor-pointer"
                    onClick={() => setSelectedTask(task)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="text-lg font-semibold text-gray-900">{task.title}</h3>
                          <span className={`px-2 py-1 rounded-full text-xs font-semibold border ${getStatusColor(task.status)}`}>
                            {task.status}
                          </span>
                        </div>
                        {task.description && (
                          <p className="text-sm text-gray-600 mb-2">{task.description}</p>
                        )}
                        <div className="flex items-center gap-4 text-xs text-gray-500">
                          {task.dueDate && (
                            <span>Due: {formatDate(task.dueDate)}</span>
                          )}
                          {task.assigneeName && (
                            <span>Assigned to: {task.assigneeName}</span>
                          )}
                          {task.links?.conversationId && (
                            <span className="text-blue-600">Linked to conversation</span>
                          )}
                          {task.links?.monitoringVisitId && (
                            <span className="text-purple-600">Linked to monitoring visit</span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedTask(task)
                          }}
                          className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition"
                        >
                          Edit
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDeleteTask(task.id)
                          }}
                          className="px-3 py-1 text-xs bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {/* Create Task Modal */}
      {showCreateModal && (
        <TaskFormModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onTaskCreated={handleTaskCreated}
          defaultLinks={{
            siteId: selectedSiteId
          }}
          enableAiAssist={false}
          apiBase={apiBase}
        />
      )}

      {/* Edit Task Modal */}
      {selectedTask && (
        <TaskEditModal
          task={selectedTask}
          onClose={() => setSelectedTask(null)}
          onUpdated={handleTaskUpdated}
          apiBase={apiBase}
        />
      )}
    </div>
  )
}

// Task Edit Modal Component
const TaskEditModal: React.FC<{
  task: MonitoringTask
  onClose: () => void
  onUpdated: () => void
  apiBase: string
}> = ({ task, onClose, onUpdated, apiBase }) => {
  const { token } = useAuth()
  const [title, setTitle] = useState(task.title)
  const [description, setDescription] = useState(task.description || '')
  const [status, setStatus] = useState<TaskStatus>(task.status)
  const [dueDate, setDueDate] = useState<string>(task.dueDate ? new Date(task.dueDate).toISOString().split('T')[0] : '')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      await axios.put(
        `${apiBase}/tasks/${task.id}`,
        {
          title,
          description: description || undefined,
          status,
          dueDate: dueDate || undefined
        },
        {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        }
      )

      onUpdated()
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update task')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Edit Task</h2>
          <button className="text-2xl text-gray-500 hover:text-gray-700" onClick={onClose}>×</button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Title *</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue"
              disabled={isSubmitting}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue resize-y"
              disabled={isSubmitting}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as TaskStatus)}
                className="w-full px-3 py-2 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue"
                disabled={isSubmitting}
              >
                <option value="open">Open</option>
                <option value="in-progress">In Progress</option>
                <option value="done">Done</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Due Date</label>
              <input
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-dizzaroo-deep-blue"
                disabled={isSubmitting}
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300 disabled:opacity-50 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !title.trim()}
              className="px-4 py-2 bg-dizzaroo-deep-blue text-white rounded-xl font-semibold hover:bg-dizzaroo-blue-green disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {isSubmitting ? 'Updating...' : 'Update Task'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default TasksTab

