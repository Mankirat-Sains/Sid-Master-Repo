<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative overflow-hidden">
    <!-- Animated background -->
    <div class="absolute inset-0 opacity-20">
      <div class="absolute inset-0" style="background-image: radial-gradient(circle at 2px 2px, rgba(255,255,255,0.1) 1px, transparent 0); background-size: 40px 40px;"></div>
    </div>

    <!-- Content -->
    <div class="relative z-10 text-center px-8">
      <!-- Welcome Message -->
      <h1 class="text-5xl md:text-7xl font-light text-white mb-16 tracking-tight">
        Welcome Back James...
      </h1>
      
      <p class="text-2xl md:text-3xl font-light text-white/90 mb-20 tracking-wide">
        Let's Build Together
      </p>

      <!-- Typing Messages -->
      <div class="space-y-6 min-h-[200px]">
        <div 
          v-for="(message, index) in messages" 
          :key="index"
          class="flex items-center justify-center"
        >
          <div class="text-2xl md:text-3xl font-light text-white/80 tracking-wide">
            <span v-html="displayedMessages[index]"></span>
            <span 
              v-if="message.index < message.fullText.length || (index === currentMessageIndex && message.index === message.fullText.length)"
              class="inline-block w-1 h-8 bg-white/80 ml-1 animate-pulse"
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
  navigateTo('/')
})

function startTypingSequence() {
  const typeNextMessage = (messageIndex: number) => {
    if (messageIndex >= messages.value.length) {
      // All messages typed, wait a moment then navigate
      setTimeout(() => {
        navigateTo('/')
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

