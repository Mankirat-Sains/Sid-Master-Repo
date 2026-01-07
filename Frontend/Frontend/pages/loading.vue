<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#04060d] via-[#090c1a] to-[#0d0820] relative overflow-hidden text-white">
    <!-- Animated background -->
    <div class="absolute inset-0 opacity-20">
      <div class="absolute inset-0" style="background-image: radial-gradient(circle at 2px 2px, rgba(255,255,255,0.1) 1px, transparent 0); background-size: 40px 40px;"></div>
    </div>
    <div class="pointer-events-none absolute inset-0">
      <div class="absolute -left-24 -top-24 h-80 w-80 rounded-full bg-purple-600/25 blur-[120px]"></div>
      <div class="absolute right-[-12rem] top-6 h-[26rem] w-[26rem] rounded-full bg-purple-400/18 blur-[160px]"></div>
      <div class="absolute left-1/3 bottom-[-4rem] h-72 w-72 rounded-full bg-indigo-400/12 blur-[140px]"></div>
    </div>

    <!-- Content -->
    <div class="relative z-10 text-center px-8">
      <!-- Welcome Message -->
      <h1 class="text-5xl md:text-7xl font-semibold text-white drop-shadow-[0_10px_40px_rgba(0,0,0,0.45)] mb-10 tracking-tight">
        Welcome Back James...
      </h1>
      
      <p class="text-2xl md:text-3xl font-medium text-white/90 drop-shadow-[0_8px_30px_rgba(0,0,0,0.35)] mb-16 tracking-wide">
        Let's Build Together
      </p>

      <!-- Typing Messages -->
      <div class="space-y-6 min-h-[200px]">
        <div 
          v-for="(message, index) in messages" 
          :key="index"
          class="flex items-center justify-center"
        >
          <div class="text-2xl md:text-3xl font-medium text-white drop-shadow-[0_6px_24px_rgba(0,0,0,0.35)] tracking-wide">
            <span class="text-white/90" v-html="displayedMessages[index]"></span>
            <span 
              v-if="message.index < message.fullText.length || (index === currentMessageIndex && message.index === message.fullText.length)"
              class="inline-block w-1.5 h-8 bg-purple-300 ml-2 animate-pulse rounded-full"
            ></span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: false
})

const messages = ref([
  { fullText: 'Write a report...', index: 0 },
  { fullText: 'Create a column...', index: 0 },
  { fullText: 'Build a bridge...', index: 0 }
])

const displayedMessages = ref(['', '', ''])
const currentMessageIndex = ref(0)
const isTyping = ref(false)

onMounted(() => {
  // Immediately navigate to main app (welcome screen will show there)
  navigateTo('/workspace')
})

function startTypingSequence() {
  const typeNextMessage = (messageIndex: number) => {
      if (messageIndex >= messages.value.length) {
        // All messages typed, wait a moment then navigate
        setTimeout(() => {
          navigateTo('/workspace')
        }, 800)
        return
      }

    const message = messages.value[messageIndex]
    currentMessageIndex.value = messageIndex
    isTyping.value = true
    displayedMessages.value[messageIndex] = ''

    let charIndex = 0
    const typingInterval = setInterval(() => {
      if (charIndex < message.fullText.length) {
        displayedMessages.value[messageIndex] = message.fullText.substring(0, charIndex + 1)
        charIndex++
        message.index = charIndex
      } else {
        clearInterval(typingInterval)
        isTyping.value = false
        // Wait a bit before typing next message
        setTimeout(() => {
          typeNextMessage(messageIndex + 1)
        }, 600)
      }
    }, 80) // Typing speed
  }

  // Start typing first message after a brief delay
  setTimeout(() => {
    typeNextMessage(0)
  }, 500)
}
</script>

<style scoped>
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}

.animate-pulse {
  animation: pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>
