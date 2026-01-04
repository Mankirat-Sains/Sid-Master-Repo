/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./components/**/*.{js,vue,ts}",
    "./layouts/**/*.vue",
    "./pages/**/*.vue",
    "./plugins/**/*.{js,ts}",
    "./app.vue",
    "./error.vue",
  ],
  theme: {
    extend: {
      colors: {
        'foundation-page': 'var(--foundation-page)',
        'foundation': 'var(--foundation)',
        'foundation-2': 'var(--foundation-2)',
        'foundation-line': 'var(--foundation-line)',
        'foreground': 'var(--foreground)',
        'foreground-muted': 'var(--foreground-muted)',
        'primary': 'var(--primary)',
        'primary-content': 'var(--primary-content)',
      },
    },
  },
  plugins: [],
}

