<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { useAppStore } from '@/stores/appStore'
import { useChatStore } from '@/stores/chatStore'
import { useMediaStore } from '@/stores/mediaStore'
import { useSessionStore } from '@/stores/sessionStore'

type ViewKey = 'studio' | 'image' | 'video' | 'chat' | 'sessions' | 'deploy'

const appStore = useAppStore()
const chatStore = useChatStore()
const mediaStore = useMediaStore()
const sessionStore = useSessionStore()

const activeView = ref<ViewKey>('studio')
const chatInput = ref('Create a launch plan for an indie AI image product.')
const imagePrompt = ref('A crisp product mockup of a translucent AI image studio dashboard, clean desk, daylight, high detail')
const imageSize = ref('1024x1024')
const imageRefs = ref('')
const videoPrompt = ref('A smooth camera push-in across a futuristic creator dashboard, soft natural light, premium SaaS aesthetic')
const videoImage = ref('')
const videoExtraImages = ref('')
const videoMode = ref<'ti2vid' | 'keyframes' | ''>('')
const videoTaskId = ref('')

const navItems: Array<{ key: ViewKey; label: string }> = [
  { key: 'studio', label: 'Studio' },
  { key: 'image', label: 'Images' },
  { key: 'video', label: 'Videos' },
  { key: 'chat', label: 'Agent' },
  { key: 'sessions', label: 'Sessions' },
  { key: 'deploy', label: 'Deploy' },
]

const promptPacks = [
  {
    title: 'Product Launch',
    tag: 'SaaS',
    prompt: 'A launch hero image for an open source AI creator tool, real product UI on a laptop, clean lighting, editorial tech style',
  },
  {
    title: 'App Store Visuals',
    tag: 'Marketing',
    prompt: 'Four polished app store screenshots for an AI visual workflow app, readable UI, bright background, professional composition',
  },
  {
    title: 'YouTube Thumbnail',
    tag: 'Growth',
    prompt: 'A high-converting YouTube thumbnail about local AI image generation, bold composition, expressive dashboard, no text',
  },
  {
    title: 'Video Keyframe',
    tag: 'Motion',
    prompt: 'A cinematic keyframe of an AI design studio rendering images and videos, realistic screen glow, depth of field',
  },
]

const featureCards = [
  ['OpenAI-compatible API', 'Use /v1/chat/completions and /v1/images/generations with existing clients.'],
  ['Prompt template gallery', 'Ship practical examples that users can copy, fork, translate, and remix.'],
  ['Image and video workflows', 'Create images, start video jobs, poll status, and store local session history.'],
  ['Agent-ready CLI', 'JSON-first scripts for Codex, Claude Code, Cursor, shell automations, and CI demos.'],
]

const scenarioEntries = computed(() => Object.values(appStore.scenarios?.scenarios || {}))
const apiBase = computed(() => import.meta.env.VITE_API_BASE_URL || '/api')
const healthLabel = computed(() => appStore.health?.ok ? 'Online' : 'Offline')

onMounted(async () => {
  await appStore.bootstrap()
  if (appStore.scenarios?.default_scenario) {
    chatStore.scenario = appStore.scenarios.default_scenario
  }
})

function splitLines(value: string) {
  return value
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean)
}

function usePrompt(prompt: string, target: 'image' | 'video' = 'image') {
  if (target === 'image') {
    imagePrompt.value = prompt
    activeView.value = 'image'
  } else {
    videoPrompt.value = prompt
    activeView.value = 'video'
  }
}

async function submitChat() {
  const message = chatInput.value
  chatInput.value = ''
  await chatStore.send(message)
}

async function submitImage() {
  await mediaStore.generateImageAsset({
    prompt: imagePrompt.value,
    size: imageSize.value,
    model: null,
    image_urls: splitLines(imageRefs.value),
    return_base64: false,
    download: true,
    include_raw: false,
  })
}

async function submitVideo() {
  await mediaStore.createVideoTask({
    prompt: videoPrompt.value,
    model: null,
    image: videoImage.value || null,
    extra_images: splitLines(videoExtraImages.value),
    mode: videoMode.value || null,
    width: 1152,
    height: 768,
    num_frames: 121,
    frame_rate: 24,
    seed: null,
    negative_prompt: null,
    wait: false,
    poll_seconds: 10,
    timeout_seconds: 1800,
    download: false,
    include_raw: false,
  })
  videoTaskId.value = mediaStore.videoTask?.task_id || mediaStore.videoTask?.task?.task_id || ''
}

async function refreshVideo() {
  await mediaStore.refreshVideo(videoTaskId.value || null)
}

function stringify(value: unknown) {
  return JSON.stringify(value, null, 2)
}
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark">OVA</span>
        <div>
          <h1>Open Visual Agent</h1>
          <p>AI image, video, prompt packs, and an OpenAI-compatible API.</p>
        </div>
      </div>

      <nav class="nav-list" aria-label="Main views">
        <button
          v-for="item in navItems"
          :key="item.key"
          :class="{ active: activeView === item.key }"
          @click="activeView = item.key; item.key === 'sessions' && sessionStore.refresh()"
        >
          {{ item.label }}
        </button>
      </nav>

      <div class="status-box">
        <span :class="appStore.health?.ok ? 'ok-dot' : 'bad-dot'"></span>
        <strong>{{ healthLabel }}</strong>
        <small>{{ apiBase }}</small>
      </div>
    </aside>

    <main class="workspace">
      <header class="topbar">
        <div>
          <strong>Creator workbench</strong>
          <span>Forkable starter for visual AI products.</span>
        </div>
        <button class="ghost-button" @click="appStore.bootstrap">Refresh</button>
      </header>

      <p v-if="appStore.error" class="error">{{ appStore.error }}</p>

      <section v-if="activeView === 'studio'" class="studio-grid">
        <div class="hero-panel">
          <p class="eyebrow">Open source visual AI starter</p>
          <h2>Launch a local AI image and video studio in minutes.</h2>
          <p>
            A practical full-stack template for builders who want a polished demo,
            provider-agnostic prompts, OpenAI-compatible routes, and agent-friendly CLI scripts.
          </p>
          <div class="hero-actions">
            <button @click="activeView = 'image'">Generate image</button>
            <button class="secondary-button" @click="activeView = 'deploy'">Deploy guide</button>
          </div>
        </div>

        <div class="metrics-strip">
          <article>
            <strong>FastAPI</strong>
            <span>Backend API</span>
          </article>
          <article>
            <strong>Vue 3</strong>
            <span>Frontend studio</span>
          </article>
          <article>
            <strong>CLI</strong>
            <span>Agent automation</span>
          </article>
        </div>

        <div class="feature-grid">
          <article v-for="feature in featureCards" :key="feature[0]" class="feature-card">
            <strong>{{ feature[0] }}</strong>
            <p>{{ feature[1] }}</p>
          </article>
        </div>

        <section class="prompt-section">
          <div class="section-heading">
            <h3>Prompt packs</h3>
            <span>Copy-ready examples for demos, docs, and social posts.</span>
          </div>
          <div class="prompt-grid">
            <article v-for="pack in promptPacks" :key="pack.title" class="prompt-card">
              <span>{{ pack.tag }}</span>
              <strong>{{ pack.title }}</strong>
              <p>{{ pack.prompt }}</p>
              <button class="ghost-button" @click="usePrompt(pack.prompt)">Use prompt</button>
            </article>
          </div>
        </section>
      </section>

      <section v-if="activeView === 'image'" class="tool-layout">
        <div class="tool-panel">
          <div class="section-heading">
            <h2>Image generation</h2>
            <span>Create launch visuals, product mockups, thumbnails, and reference images.</span>
          </div>
          <label>Prompt<textarea v-model="imagePrompt" rows="7" /></label>
          <div class="form-row">
            <label>Size<input v-model="imageSize" /></label>
            <label>Reference image URLs<textarea v-model="imageRefs" rows="3" /></label>
          </div>
          <button :disabled="mediaStore.loading || !imagePrompt.trim()" @click="submitImage">
            Generate image
          </button>
          <p v-if="mediaStore.error" class="error">{{ mediaStore.error }}</p>
        </div>
        <div class="result-panel">
          <h3>Result</h3>
          <pre v-if="mediaStore.imageResult">{{ stringify(mediaStore.imageResult) }}</pre>
          <div v-else class="empty-state">Run a prompt to see provider output, local path, and URLs.</div>
        </div>
      </section>

      <section v-if="activeView === 'video'" class="tool-layout">
        <div class="tool-panel">
          <div class="section-heading">
            <h2>Video tasks</h2>
            <span>Start image-to-video, text-to-video, or keyframe jobs and poll results.</span>
          </div>
          <label>Prompt<textarea v-model="videoPrompt" rows="6" /></label>
          <label>First frame image URL<input v-model="videoImage" /></label>
          <label>Extra keyframe URLs<textarea v-model="videoExtraImages" rows="3" /></label>
          <label>
            Mode
            <select v-model="videoMode">
              <option value="">Auto</option>
              <option value="ti2vid">Text + image to video</option>
              <option value="keyframes">Keyframes</option>
            </select>
          </label>
          <button :disabled="mediaStore.loading || !videoPrompt.trim()" @click="submitVideo">Create task</button>
          <div class="poll-row">
            <input v-model="videoTaskId" placeholder="Task ID" />
            <button class="secondary-button" :disabled="mediaStore.loading || !videoTaskId" @click="refreshVideo">
              Poll
            </button>
          </div>
          <p v-if="mediaStore.error" class="error">{{ mediaStore.error }}</p>
        </div>
        <div class="result-panel">
          <h3>Task output</h3>
          <pre v-if="mediaStore.videoTask">{{ stringify(mediaStore.videoTask) }}</pre>
          <pre v-if="mediaStore.videoResult">{{ stringify(mediaStore.videoResult) }}</pre>
          <div v-if="!mediaStore.videoTask && !mediaStore.videoResult" class="empty-state">
            Create a task to see status, task id, video URL, and local file path.
          </div>
        </div>
      </section>

      <section v-if="activeView === 'chat'" class="chat-layout">
        <div class="toolbar">
          <label>
            Scenario
            <select v-model="chatStore.scenario">
              <option v-for="scenario in scenarioEntries" :key="scenario.name" :value="scenario.name">
                {{ scenario.name }}
              </option>
            </select>
          </label>
          <label class="inline-control">
            <input v-model="chatStore.useTools" type="checkbox" />
            Enable tools
          </label>
          <button class="ghost-button" @click="chatStore.reset">New session</button>
        </div>
        <div class="messages">
          <div v-if="!chatStore.hasMessages" class="empty-state">
            Ask the agent to plan a prompt pack, generate creative briefs, or turn product ideas into visual prompts.
          </div>
          <article v-for="(message, index) in chatStore.messages" :key="index" :class="['message', message.role]">
            <strong>{{ message.role }}</strong>
            <p>{{ typeof message.content === 'string' ? message.content : stringify(message.content) }}</p>
          </article>
        </div>
        <form class="composer" @submit.prevent="submitChat">
          <textarea v-model="chatInput" placeholder="Ask for a visual campaign, prompt rewrite, or product launch plan" />
          <button :disabled="chatStore.loading || !chatInput.trim()">Send</button>
        </form>
        <p v-if="chatStore.sessionId" class="hint">Session: {{ chatStore.sessionId }}</p>
        <p v-if="chatStore.error" class="error">{{ chatStore.error }}</p>
      </section>

      <section v-if="activeView === 'sessions'" class="tool-layout">
        <div class="tool-panel">
          <div class="section-heading">
            <h2>Session history</h2>
            <span>Local SQLite-backed conversations for demos and debugging.</span>
          </div>
          <button @click="sessionStore.refresh">Refresh sessions</button>
          <div class="session-list">
            <button v-for="session in sessionStore.sessions" :key="session.id" @click="sessionStore.load(session.id)">
              <strong>{{ session.id }}</strong>
              <span>{{ session.message_count }} messages</span>
            </button>
          </div>
          <p v-if="sessionStore.error" class="error">{{ sessionStore.error }}</p>
        </div>
        <div class="result-panel messages compact">
          <article v-for="(message, index) in sessionStore.selectedMessages" :key="index" :class="['message', message.role]">
            <strong>{{ message.role }}</strong>
            <p>{{ typeof message.content === 'string' ? message.content : stringify(message.content) }}</p>
          </article>
          <div v-if="!sessionStore.selectedMessages.length" class="empty-state">Select a session to inspect messages.</div>
        </div>
      </section>

      <section v-if="activeView === 'deploy'" class="deploy-grid">
        <article class="deploy-card">
          <h2>Quick start</h2>
          <pre>cp .env.example .env
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\uvicorn backend.app.main:app --reload --port 8007</pre>
        </article>
        <article class="deploy-card">
          <h2>Frontend</h2>
          <pre>cd frontend
npm install
npm run dev</pre>
        </article>
        <article class="deploy-card wide">
          <h2>Runtime config</h2>
          <pre>{{ stringify(appStore.runtime || {}) }}</pre>
        </article>
      </section>
    </main>
  </div>
</template>
