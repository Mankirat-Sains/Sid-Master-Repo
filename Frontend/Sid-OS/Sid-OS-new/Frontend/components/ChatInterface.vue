<template>
  <div class="flex h-full flex-col">
    <!-- Header -->
    <div class="border-b border-foundation-line bg-foundation p-4">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-xl font-semibold">SidOS Assistant</h1>
          <p class="text-sm text-foreground-muted">
            Ask questions about projects and BIM models
          </p>
        </div>
        <button
          v-if="viewerVisible"
          @click="$emit('toggle-viewer')"
          class="p-2 rounded-lg hover:bg-foundation-2 transition-colors"
          title="Toggle Viewer"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Messages -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-4">
      <div
        v-for="message in messages"
        :key="message.id"
        class="flex flex-col"
        :class="message.role === 'user' ? 'items-end' : 'items-start'"
      >
        <div
          class="max-w-[85%] rounded-lg p-3"
          :class="
            message.role === 'user'
              ? 'bg-primary text-primary-content'
              : 'bg-foundation-2 text-foreground'
          "
        >
          <p class="whitespace-pre-wrap">{{ message.content }}</p>
          <p v-if="message.timestamp" class="text-xs mt-1 opacity-70">
            {{ formatTime(message.timestamp) }}
          </p>
          <!-- Model loaded indicator -->
          <div
            v-if="message.modelInfo"
            class="mt-2 pt-2 border-t border-current/20"
          >
            <button
              @click="loadModelFromMessage(message.modelInfo)"
              class="text-xs flex items-center gap-1 hover:underline"
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"
                />
                <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
                <line x1="12" y1="22.08" x2="12" y2="12" />
              </svg>
              View BIM Model
            </button>
          </div>
        </div>
      </div>

      <div
        v-if="isLoading"
        class="flex items-center gap-2 text-foreground-muted"
      >
        <div
          class="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"
        />
        <span>Thinking...</span>
      </div>
    </div>

    <!-- Input -->
    <div class="border-t border-foundation-line bg-foundation p-4">
      <form @submit.prevent="sendMessage" class="flex gap-2">
        <input
          v-model="inputMessage"
          type="text"
          placeholder="Ask about a project or BIM model..."
          class="flex-1 px-4 py-2 rounded-lg border border-foundation-line bg-foundation-2 text-foreground placeholder-foreground-muted focus:outline-none focus:ring-2 focus:ring-primary"
          :disabled="isLoading"
        />
        <button
          type="submit"
          :disabled="!inputMessage.trim() || isLoading"
          class="px-6 py-2 rounded-lg bg-primary text-primary-content hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Send
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  modelInfo?: {
    projectId: string;
    modelId: string;
    commitId?: string;
    projectNumber?: string;
    projectName?: string;
  };
}

interface Props {
  viewerVisible?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  viewerVisible: false,
});

const emit = defineEmits<{
  loadModel: [model: { projectId: string; modelId: string; commitId?: string }];
  toggleViewer: [];
}>();

const { sendChatMessage } = useChat();
const { findProjectByNumber, findProjectByName, getAllMappings } = useProjectMapping();

const messages = ref<Message[]>([]);
const inputMessage = ref("");
const isLoading = ref(false);
const messagesContainer = ref<HTMLElement>();

function formatTime(date: Date): string {
  return new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

async function sendMessage() {
  if (!inputMessage.value.trim() || isLoading.value) return;

  const userMessage: Message = {
    id: Date.now().toString(),
    role: "user",
    content: inputMessage.value,
    timestamp: new Date(),
  };

  messages.value.push(userMessage);
  const question = inputMessage.value;
  inputMessage.value = "";
  isLoading.value = true;

  // Scroll to bottom
  await nextTick();
  scrollToBottom();

  try {
    // Send to orchestrator
    const response = await sendChatMessage(question);

    // Backend returns 'reply' not 'answer'
    const answerText = response.reply || response.answer || "No response";

    // Check if response includes model info from orchestrator
    let modelInfo = response.model_info
      ? {
          projectId: response.model_info.projectId,
          modelId: response.model_info.modelId,
          commitId: response.model_info.commitId,
          projectNumber: response.model_info.projectNumber,
        }
      : null;

    // If not in structured format, try to extract from answer text
    if (!modelInfo) {
      modelInfo = extractModelInfo(answerText);
    }

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: "assistant",
      content: answerText,
      timestamp: new Date(),
      modelInfo,
    };

    messages.value.push(assistantMessage);

    // If model info found, automatically load it
    if (modelInfo) {
      emit("loadModel", modelInfo);
    }
  } catch (error) {
    console.error("Chat error:", error);
    messages.value.push({
      id: (Date.now() + 1).toString(),
      role: "assistant",
      content: "Sorry, I encountered an error. Please try again.",
      timestamp: new Date(),
    });
  } finally {
    isLoading.value = false;
    await nextTick();
    scrollToBottom();
  }
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
}

function loadModelFromMessage(modelInfo: Message["modelInfo"]) {
  if (modelInfo) {
    emit("loadModel", modelInfo);
  }
}

function extractModelInfo(
  answer: string
): {
  projectId: string;
  modelId: string;
  commitId?: string;
  projectNumber?: string;
  projectName?: string;
} | null {
  // Method 1: Look for structured JSON in the answer
  try {
    const jsonMatch = answer.match(/\{[\s\S]*"projectId"[\s\S]*\}/);
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0]);
      if (parsed.projectId && parsed.modelId) {
        return {
          projectId: parsed.projectId,
          modelId: parsed.modelId,
          commitId: parsed.commitId,
          projectNumber: parsed.projectNumber,
        };
      }
    }
  } catch {
    // Not valid JSON, continue
  }

  // Method 2: Look for project number patterns (e.g., "25-08-127")
  const projectNumberMatch = answer.match(/\b(\d{2}-\d{2}-\d{3})\b/);
  if (projectNumberMatch) {
    const projectNumber = projectNumberMatch[1];
    const mapping = findProjectByNumber(projectNumber);
    if (mapping) {
      return {
        projectId: mapping.projectId,
        modelId: mapping.modelId,
        projectNumber,
        projectName: mapping.name,
      };
    }
  }

  // Method 3: Look for project names
  const allMappings = getAllMappings();
  const entries = Object.entries(allMappings);
  for (let i = 0; i < entries.length; i++) {
    const [key, mapping] = entries[i];
    if (answer.toLowerCase().indexOf(key.toLowerCase()) !== -1) {
      const numberMatch = key.match(/\d{2}-\d{2}-\d{3}/);
      return {
        projectId: mapping.projectId,
        modelId: mapping.modelId,
        projectNumber: numberMatch ? numberMatch[0] : undefined,
        projectName: mapping.name,
      };
    }
  }

  // Method 4: Look for Speckle URLs
  const urlMatch = answer.match(
    /speckle[^\s]*\/projects\/([a-zA-Z0-9]+)\/models\/([a-zA-Z0-9]+)/i
  );
  if (urlMatch) {
    return {
      projectId: urlMatch[1],
      modelId: urlMatch[2],
    };
  }

  // Method 5: Look for explicit project/model ID patterns
  const projectIdMatch = answer.match(
    /project[_\s]?id[:\s]+([a-zA-Z0-9]{10,})/i
  );
  const modelIdMatch = answer.match(/model[_\s]?id[:\s]+([a-zA-Z0-9]{10,})/i);

  if (projectIdMatch && modelIdMatch) {
    return {
      projectId: projectIdMatch[1],
      modelId: modelIdMatch[1],
    };
  }

  return null;
}
</script>
