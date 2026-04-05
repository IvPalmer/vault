import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

const certDir = path.resolve(__dirname, 'certs')
const certFile = path.join(certDir, 'raphaels-mac-studio.tail5d4d09.ts.net.crt')
const keyFile = path.join(certDir, 'raphaels-mac-studio.tail5d4d09.ts.net.key')
const hasCerts = fs.existsSync(certFile) && fs.existsSync(keyFile)

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5175,
    strictPort: true,
    host: true,
    open: false,
    allowedHosts: ['.local', 'vault.local', '.ts.net'],
    ...(hasCerts && {
      https: {
        cert: fs.readFileSync(certFile),
        key: fs.readFileSync(keyFile),
      },
    }),
    proxy: {
      // Apple Reminders → host-side sidecar (needs macOS EventKit/osascript)
      '/api/home/reminders': {
        target: 'http://127.0.0.1:5177',
        changeOrigin: true,
      },
      // Everything else → Django in Docker
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
    },
  },
})
