// vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [
    // keep your existing React support
    react(),

    // then add our little CSS‐MIME workaround
    {
      name: 'css-mime-fix',
      configureServer(server) {
        server.middlewares.use((req, res, next) => {
          if (req.url.startsWith('/src/index.css')) {
            res.setHeader('Content-Type', 'text/css; charset=utf-8')
          }
          next()
        })
      }
    }
  ]
})