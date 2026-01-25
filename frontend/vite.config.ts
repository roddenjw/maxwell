import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false, // Disable sourcemaps in production for smaller bundle
    rollupOptions: {
      output: {
        manualChunks(id) {
          // Check if module is from node_modules
          if (id.includes('node_modules')) {
            // Split React core
            if (id.includes('/react/') || id.includes('/react-dom/')) {
              return 'vendor-react';
            }
            // Split Lexical editor
            if (id.includes('/lexical/') || id.includes('/@lexical/')) {
              return 'vendor-lexical';
            }
            // Split graph visualization
            if (id.includes('/react-force-graph') || id.includes('/d3-force/')) {
              return 'vendor-graph';
            }
            // Split drag and drop
            if (id.includes('/@dnd-kit/')) {
              return 'vendor-dnd';
            }
            // Split misc utilities
            if (id.includes('/zustand/') || id.includes('/lodash/') || id.includes('/posthog-js/')) {
              return 'vendor-misc';
            }
          }
        },
      },
    },
  },
})
