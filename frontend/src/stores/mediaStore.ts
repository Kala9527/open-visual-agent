import { defineStore } from 'pinia'
import { ref } from 'vue'

import { createVideo, generateImage, getLocalVideoTask, getVideo } from '@/api/assistantApi'
import { toErrorMessage } from '@/api/http'
import type { ImageRequest, ImageResponse, VideoRequest, VideoResultResponse, VideoTaskResponse } from '@/api/types'

export const useMediaStore = defineStore('media', () => {
  const imageResult = ref<ImageResponse | null>(null)
  const videoTask = ref<VideoTaskResponse | null>(null)
  const videoResult = ref<VideoResultResponse | null>(null)
  const localVideoTask = ref<Record<string, unknown> | null>(null)
  const loading = ref(false)
  const error = ref('')

  async function generateImageAsset(payload: ImageRequest) {
    loading.value = true
    error.value = ''
    try {
      imageResult.value = await generateImage(payload)
    } catch (err) {
      error.value = toErrorMessage(err)
    } finally {
      loading.value = false
    }
  }

  async function createVideoTask(payload: VideoRequest) {
    loading.value = true
    error.value = ''
    try {
      videoTask.value = await createVideo(payload)
      videoResult.value = null
    } catch (err) {
      error.value = toErrorMessage(err)
    } finally {
      loading.value = false
    }
  }

  async function refreshVideo(taskId?: string | null, videoId?: string | null) {
    const id = taskId || videoTask.value?.task_id || videoTask.value?.task?.task_id
    if (!id) return
    loading.value = true
    error.value = ''
    try {
      videoResult.value = await getVideo(id, videoId || videoTask.value?.video_id || videoTask.value?.task?.video_id)
      localVideoTask.value = (await getLocalVideoTask(id)).task
    } catch (err) {
      error.value = toErrorMessage(err)
    } finally {
      loading.value = false
    }
  }

  return {
    imageResult,
    videoTask,
    videoResult,
    localVideoTask,
    loading,
    error,
    generateImageAsset,
    createVideoTask,
    refreshVideo,
  }
})
