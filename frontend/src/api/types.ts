export type ChatRole = 'system' | 'user' | 'assistant' | 'tool'

export type ChatMessage = {
  role: ChatRole
  content: unknown
}

export type ScenarioConfig = {
  name: string
  description: string
  skills_doc_paths: string[]
}

export type ScenarioResponse = {
  identity: string
  default_scenario: string
  skills_doc_paths: string[]
  scenarios: Record<string, ScenarioConfig>
}

export type ChatRequest = {
  message: string
  session_id?: string | null
  scenario?: string | null
  history?: ChatMessage[]
  use_tools?: boolean
}

export type ChatResponse = {
  ok: boolean
  session_id: string
  scenario: string
  answer: string
  messages: ChatMessage[]
  tool_calls: Record<string, unknown>[]
  raw: Record<string, unknown>
}

export type ImageRequest = {
  prompt: string
  size: string
  model?: string | null
  image_urls: string[]
  return_base64: boolean
  download: boolean
  include_raw: boolean
  n?: number | null
  response_format?: 'url' | 'b64_json' | null
  quality?: string | null
  background?: string | null
  output_format?: string | null
  output_compression?: number | null
  moderation?: string | null
  user?: string | null
}

export type ImageResponse = {
  ok: boolean
  type: 'image'
  created?: number
  data?: Array<Record<string, unknown>>
  url?: string | null
  local_path?: string | null
  has_b64_json?: boolean
  model?: string
  raw?: Record<string, unknown>
}

export type VideoRequest = {
  prompt: string
  model?: string | null
  image?: string | null
  extra_images: string[]
  mode?: 'ti2vid' | 'keyframes' | null
  width: number
  height: number
  num_frames: number
  frame_rate: number
  seed?: number | null
  negative_prompt?: string | null
  wait: boolean
  poll_seconds: number
  timeout_seconds: number
  download: boolean
  include_raw: boolean
}

export type VideoTaskResponse = {
  ok: boolean
  type: string
  task_id?: string | null
  video_id?: string | null
  status?: string | null
  model?: string
  task?: VideoTaskResponse
  result?: VideoResultResponse | null
}

export type VideoResultResponse = {
  ok: boolean
  type: 'video_result'
  status?: string | null
  progress?: number | null
  video_url?: string | null
  local_path?: string | null
  error?: unknown
  terminal?: boolean
}

export type SessionSummary = {
  id: string
  scenario?: string | null
  created_at: string
  updated_at: string
  message_count: number
}
