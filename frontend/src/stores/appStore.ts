import { defineStore } from 'pinia'
import { ref } from 'vue'

import { getHealth, getRuntime, getScenarios } from '@/api/assistantApi'
import { toErrorMessage } from '@/api/http'
import type { ScenarioResponse } from '@/api/types'

export const useAppStore = defineStore('app', () => {
  const loading = ref(false)
  const error = ref('')
  const health = ref<{ ok: boolean; service: string } | null>(null)
  const scenarios = ref<ScenarioResponse | null>(null)
  const runtime = ref<Record<string, unknown> | null>(null)

  async function bootstrap() {
    loading.value = true
    error.value = ''
    try {
      const [healthData, scenarioData, runtimeData] = await Promise.all([
        getHealth(),
        getScenarios(),
        getRuntime(),
      ])
      health.value = healthData
      scenarios.value = scenarioData
      runtime.value = runtimeData
    } catch (err) {
      error.value = toErrorMessage(err)
    } finally {
      loading.value = false
    }
  }

  return { loading, error, health, scenarios, runtime, bootstrap }
})
