// import axios from 'axios'
import { api } from '../lib/api'

export interface AiTaskSuggestionInput {
  conversationId: string
  messageId: string
  messageText: string
  recentMessages?: { author: string; text: string; createdAt: string }[]
}

export interface AiTaskSuggestionResult {
  title: string
  description?: string
  suggestedStatus?: 'open' | 'in-progress' | 'done' | 'cancelled'
  suggestedDueDate?: string
}

/**
 * Get AI task suggestion from a conversation message.
 * Uses the same pattern as existing AI summary endpoints.
 */
export async function getAiTaskSuggestion(
  input: AiTaskSuggestionInput
): Promise<AiTaskSuggestionResult> {
  try {
    const response = await api.post(
      '/ai/task-suggestion',
      input
    )

    return response.data
  } catch (error: any) {
    console.error('Error getting AI task suggestion:', error)
    throw new Error(error.response?.data?.detail || 'Failed to get AI task suggestion')
  }
}

