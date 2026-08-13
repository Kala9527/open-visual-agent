import { http } from './http'
import type {
  ChatRequest,
  ChatResponse,
  ImageRequest,
  ImageResponse,
  ScenarioResponse,
  SessionSummary,
  VideoRequest,
  VideoResultResponse,
  VideoTaskResponse,
} from './types'

export async function getHealth() {
  const { data } = await http.get('/health')
  return data as { ok: boolean; service: string }
}

export async function getScenarios() {
  const { data } = await http.get('/v1/config/scenarios')
  return data as ScenarioResponse
}

export async function getRuntime() {
  const { data } = await http.get('/v1/config/runtime')
  return data as Record<string, unknown>
}

export async function sendChat(payload: ChatRequest) {
  const { data } = await http.post('/v1/chat', payload)
  return data as ChatResponse
}

export async function generateImage(payload: ImageRequest) {
  const { data } = await http.post('/v1/images/generations', payload)
  return data as ImageResponse
}

export async function createVideo(payload: VideoRequest) {
  const { data } = await http.post('/v1/videos', payload)
  return data as VideoTaskResponse
}

export async function getVideo(taskId: string, videoId?: string | null) {
  const { data } = await http.get(`/v1/videos/${encodeURIComponent(taskId)}`, {
    params: { video_id: videoId || undefined },
  })
  return data as VideoResultResponse
}

export async function getLocalVideoTask(taskId: string) {
  const { data } = await http.get(`/v1/videos/${encodeURIComponent(taskId)}/local`)
  return data as { ok: boolean; task: Record<string, unknown> | null }
}

export async function listSessions() {
  const { data } = await http.get('/v1/sessions')
  return data as { sessions: SessionSummary[] }
}

export async function getSession(sessionId: string) {
  const { data } = await http.get(`/v1/sessions/${encodeURIComponent(sessionId)}`)
  return data as { session_id: string; messages: ChatResponse['messages'] }
}

export async function clearSession(sessionId: string) {
  const { data } = await http.delete(`/v1/sessions/${encodeURIComponent(sessionId)}`)
  return data as { ok: boolean; session_id: string }
}
