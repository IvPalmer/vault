import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5175,
    strictPort: true,
    host: true,
    open: false,
    allowedHosts: ['.local'],
    proxy: {
      // Apple Reminders → host-side sidecar (needs macOS EventKit)
      '/api/home/reminders': {
        target: 'http://127.0.0.1:5176',
        changeOrigin: true,
      },
      // Everything else (incl. Google Calendar) → Django in Docker
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
    },
  },
})
