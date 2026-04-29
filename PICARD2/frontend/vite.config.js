import path from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    fs: {
      allow: [path.resolve(__dirname, '..')],
    },
    host: '0.0.0.0',
    proxy: {
      '/auth/': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/datasets/': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/scripts/': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/experiments/': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/media/': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
})
