import { defineStore } from 'pinia'
import { ref } from 'vue'

import { clearSession, getSession, listSessions } from '@/api/assistantApi'
import { toErrorMessage } from '@/api/http'
import type { ChatMessage, SessionSummary } from '@/api/types'

export const useSessionStore = defineStore('session', () => {
  const sessions = ref<SessionSummary[]>([])
  const selectedMessages = ref<ChatMessage[]>([])
  const loading = ref(false)
  const error = ref('')

  async function refresh() {
    loading.value = true
    error.value = ''
    try {
      sessions.value = (await listSessions()).sessions
    } catch (err) {
      error.value = toErrorMessage(err)
    } finally {
      loading.value = false
    }
  }

  async function load(sessionId: string) {
    loading.value = true
    error.value = ''
    try {
      selectedMessages.value = (await getSession(sessionId)).messages
    } catch (err) {
      error.value = toErrorMessage(err)
    } finally {
      loading.value = false
    }
  }

  async function clear(sessionId: string) {
    await clearSession(sessionId)
    await refresh()
    selectedMessages.value = []
  }

  return { sessions, selectedMessages, loading, error, refresh, load, clear }
})
