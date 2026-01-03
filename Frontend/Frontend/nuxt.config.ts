// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  modules: [
    '@nuxt/eslint',
    '@nuxt/devtools',
    '@nuxtjs/tailwindcss'
  ],

  typescript: {
    strict: true,
    shim: false
  },

  runtimeConfig: {
    public: {
      orchestratorUrl: process.env.ORCHESTRATOR_URL || process.env.RAG_API_URL || 'http://localhost:8000',
      // Use public Speckle.systems instance (has CORS configured for browsers)
      // Can override with SPECKLE_URL env var if you want to use a different server
      speckleUrl: process.env.SPECKLE_URL || process.env.SPECKLE_SERVER_URL || 'https://app.speckle.systems',
      speckleToken: process.env.SPECKLE_TOKEN || ''
    }
  },

  tailwindcss: {
    // Basic Tailwind config - can add Speckle theme later
  },

  vite: {
    optimizeDeps: {
      include: ['@speckle/viewer']
    },
    server: {
      proxy: {
        // Note: Public Speckle.systems instance has CORS configured, so proxy may not be needed
      // Keeping this for reference in case you switch back to a custom server
      }
    }
  },

  css: ['~/assets/css/main.css'],

  app: {
    head: {
      title: 'SidOS - Engineering Operating System',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' }
      ]
    }
  }
})

