import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The API runs on :8000 (`uv run dep-watch-agent`). Proxying /api keeps the browser on one
// origin in development, so no CORS setup is needed.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: process.env.DEP_WATCH_API ?? 'http://127.0.0.1:8000',
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
