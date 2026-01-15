// https://nuxt.com/docs/api/configuration/nuxt-config
import { readFileSync } from 'fs'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

// Load env files into process.env. Prefer repo root .env, fallback to Frontend/.env.
const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const envPaths = [
  resolve(__dirname, '..', '..', '.env'), // repo root
  resolve(__dirname, '..', '.env')        // Frontend/.env (fallback)
]

for (const envPath of envPaths) {
  try {
    const envContent = readFileSync(envPath, 'utf-8')
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
    console.info(`Loaded env from ${envPath}`)
    break
  } catch (error) {
    // Try next path
    continue
  }
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
      agentApiUrl: process.env.AGENT_API_URL || 'http://localhost:8001',
      // Use public Speckle.systems instance (has CORS configured for browsers)
      // Can override with SPECKLE_URL env var if you want to use a different server
      speckleUrl: process.env.SPECKLE_URL || process.env.SPECKLE_SERVER_URL || 'https://app.speckle.systems',
      speckleToken: process.env.SPECKLE_TOKEN || '',
      onlyofficeServerUrl: process.env.ONLYOFFICE_SERVER_URL || '',
      onlyofficeDocumentBaseUrl: process.env.ONLYOFFICE_DOCUMENT_BASE_URL || '',
      onlyofficeDocumentUrl: process.env.ONLYOFFICE_DOCUMENT_URL || '',
      onlyofficeCallbackUrl: process.env.ONLYOFFICE_CALLBACK_URL || '',
      onlyofficeUserName: process.env.ONLYOFFICE_USER_NAME || '',
      onlyofficeUserId: process.env.ONLYOFFICE_USER_ID || ''
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
