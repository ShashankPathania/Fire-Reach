import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/run-agent': 'http://localhost:8000',
      '/batch-analyze': 'http://localhost:8000',
      '/history': 'http://localhost:8000',
      '/status': 'http://localhost:8000',
      '/record': 'http://localhost:8000',
      '/stats': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
      '/send-email': 'http://localhost:8000',
      '/auth': 'http://localhost:8000',
    },
  },
})
