import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base matches the GitHub Pages path: https://<user>.github.io/MS-PR/
export default defineConfig({
  base: '/MS-PR/',
  plugins: [react()],
  worker: { format: 'es' }, // MapLibre starts its worker as an ES module
  test: {
    environment: 'node',
  },
})
