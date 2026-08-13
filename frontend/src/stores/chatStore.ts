import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { sendChat } from '@/api/assistantApi'
import { toErrorMessage } from '@/api/http'
import type { ChatMessage } from '@/api/types'

export const useChatStore = defineStore('chat', () => {
  const sessionId = ref<string | null>(null)
  const scenario = ref<string>('customer_service')
  const useTools = ref(true)
  const messages = ref<ChatMessage[]>([])
  const loading = ref(false)
  const error = ref('')

  const hasMessages = computed(() => messages.value.length > 0)

  async function send(message: string) {
    if (!message.trim()) return
    loading.value = true
    error.value = ''
    messages.value.push({ role: 'user', content: message })
    try {
      const response = await sendChat({
        message,
        session_id: sessionId.value,
        scenario: scenario.value,
        use_tools: useTools.value,
      })
      sessionId.value = response.session_id
      messages.value = response.messages
    } catch (err) {
      error.value = toErrorMessage(err)
      messages.value.push({ role: 'assistant', content: `请求失败：${error.value}` })
    } finally {
      loading.value = false
    }
  }

  function reset() {
    sessionId.value = null
    messages.value = []
    error.value = ''
  }

  return { sessionId, scenario, useTools, messages, loading, error, hasMessages, send, reset }
})
