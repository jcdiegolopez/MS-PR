import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { setWorkerUrl } from 'maplibre-gl'
// MapLibre finds its worker relative to its own file, which breaks once Vite bundles it.
// Let Vite bundle the worker (with its imports) and hand MapLibre the final URL.
import maplibreWorkerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import 'maplibre-gl/dist/maplibre-gl.css'
import './style.css'
import App from './App.jsx'

setWorkerUrl(maplibreWorkerUrl)

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
