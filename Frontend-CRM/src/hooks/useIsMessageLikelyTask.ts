import { useMemo } from 'react'

/**
 * Hook to detect if a message looks like a task/action item.
 * Uses simple keyword-based heuristics (no AI call for performance).
 */
export function useIsMessageLikelyTask(messageText: string): boolean {
  return useMemo(() => {
    if (!messageText || messageText.trim().length === 0) {
      return false
    }

    const text = messageText.toLowerCase().trim()

    // Task-indicating keywords/phrases
    const taskKeywords = [
      'follow up',
      'follow-up',
      'followup',
      'schedule',
      'set up a call',
      'setup a call',
      'we need to',
      'we should',
      'please check',
      'needs checking',
      'monitoring visit',
      'site visit',
      'action required',
      'action needed',
      'todo',
      'to do',
      'remind',
      'reminder',
      'deadline',
      'due date',
      'assign',
      'task',
      'complete',
      'finish',
      'review',
      'verify',
      'confirm',
      'update',
      'send',
      'prepare',
      'arrange',
      'organize',
      'coordinate',
    ]

    // Check if message contains any task keywords
    return taskKeywords.some(keyword => text.includes(keyword))
  }, [messageText])
}

