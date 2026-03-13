
// import { defineConfig } from 'vite'
// import react from '@vitejs/plugin-react'
// import path from 'path'

// export default defineConfig({
//   plugins: [react()],

//   resolve: {
//     alias: {
//       '@': path.resolve(process.cwd(), 'src'),
//     },
//   },

//   server: {
//     host: '0.0.0.0',
//     port: 3000,
//     proxy: {
//       '/api': {
//         target: 'https://backend-crm-beh3f6fvcfhjbxbt.canadacentral-01.azurewebsites.net',
//         changeOrigin: true,
//         ws: true,
//       },
//     },
//   },
// })

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],

  resolve: {
    alias: {
      '@': path.resolve(process.cwd(), 'src'),
    },
  },

  server: {
    host: '0.0.0.0',
    port: 3000,
  },
})
