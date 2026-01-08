// https://nuxt.com/docs/api/configuration/nuxt-config
import { readFileSync } from 'fs'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

// Load .env from parent directory (Frontend/.env) and merge into process.env
const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const parentEnvPath = resolve(__dirname, '..', '.env')
try {
  const envContent = readFileSync(parentEnvPath, 'utf-8')
  envContent.split('\n').forEach(line => {
    const trimmed = line.trim()
    if (trimmed && !trimmed.startsWith('#')) {
      const [key, ...valueParts] = trimmed.split('=')
      if (key && valueParts.length > 0) {
        const value = valueParts.join('=').replace(/^["']|["']$/g, '')
        if (!process.env[key]) {
          process.env[key] = value
        }
      }
    }
  })
} catch (error) {
  console.warn(`Could not load .env from parent directory: ${parentEnvPath}`)
}

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
      hmr: {
        port: 24679,
        host: '127.0.0.1'
      },
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
      ],
      script: [
        {
          src: 'https://polyfill.io/v3/polyfill.min.js?features=es6',
          defer: true
        },
        {
          innerHTML: `
            window.MathJax = {
              tex: {
                inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
                processEscapes: true,
                processEnvironments: true
              },
              options: {
                skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre']
              }
            };
          `,
          type: 'text/javascript'
        },
        {
          src: 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js',
          defer: true,
          id: 'MathJax-script'
        }
      ],
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' }
      ]
    }
  }
})
