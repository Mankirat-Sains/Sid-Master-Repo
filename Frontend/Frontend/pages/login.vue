<template>
  <div class="min-h-screen flex">
    <!-- Left Panel - Login Form -->
    <div class="flex-1 flex flex-col justify-center items-center bg-[#1a1a1a] px-8 py-12">
      <!-- Header -->
      <div class="w-full max-w-md mb-12">
        <!-- Headline -->
        <h1 class="text-6xl font-serif font-bold text-white mb-6 leading-tight whitespace-nowrap">
          Welcome to Sid
        </h1>
        
        <!-- Tagline -->
        <p class="text-3xl text-white font-sans mb-12" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;">
          The Autonomous engineer..
        </p>
      </div>

      <!-- Login Card -->
      <div class="w-full max-w-lg">
        <div class="bg-[#2a2a2a] rounded-2xl p-10">
          <!-- Google Login Button -->
          <button
            @click="handleGoogleLogin"
            class="w-full flex items-center justify-center gap-3 px-6 py-4 bg-white border-0 rounded-xl hover:bg-gray-100 transition-all duration-200 font-medium text-black mb-6"
          >
            <svg class="w-5 h-5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            <span>Continue with Google</span>
          </button>

          <!-- Divider -->
          <div class="relative mb-6">
            <div class="absolute inset-0 flex items-center">
              <div class="w-full border-t border-gray-600"></div>
            </div>
            <div class="relative flex justify-center text-sm">
              <span class="px-4 bg-[#2a2a2a] text-white font-medium">OR</span>
            </div>
          </div>

          <!-- Email Input -->
          <div class="mb-6">
            <input
              v-model="email"
              type="email"
              placeholder="Enter your email"
              class="w-full px-4 py-4 bg-[#1a1a1a] border-2 border-gray-700 rounded-xl focus:outline-none focus:border-gray-500 focus:ring-2 focus:ring-gray-600 transition-all duration-200 text-white placeholder-gray-400"
              @keyup.enter="handleEmailLogin"
            />
          </div>

          <!-- Email Login Button -->
          <button
            @click="handleEmailLogin"
            class="w-full px-6 py-4 bg-white text-black rounded-xl hover:bg-gray-100 transition-all duration-200 font-medium"
          >
            Continue with email
          </button>
        </div>
      </div>
    </div>

    <!-- Right Panel - Speckle Model Viewer -->
    <div class="flex-1 bg-[#9333ea] flex items-center justify-center p-8 relative overflow-hidden">
      <!-- Speckle Iframe -->
      <div class="w-full h-full">
        <iframe
          title="Speckle"
          src="http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com/projects/1310d85aa9/models/80cbb42602?embedToken=09dbe9a6ad40cedc4ace9b4154e8cdaa8d1dab9bd3#embed=%7B%22isEnabled%22%3Atrue%7D"
          width="100%"
          height="100%"
          frameborder="0"
          class="w-full h-full"
        ></iframe>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: false
})

const email = ref('')

function handleGoogleLogin() {
  // TODO: Implement Google OAuth login
  console.log('Google login clicked')
  // Navigate to loading page first
  navigateTo('/loading')
}

function handleEmailLogin() {
  if (!email.value || !email.value.includes('@')) {
    alert('Please enter a valid email address')
    return
  }
  // TODO: Implement email login
  console.log('Email login:', email.value)
  // Navigate to loading page first
  navigateTo('/loading')
}
</script>

<style scoped>
/* Additional styling if needed */
</style>

