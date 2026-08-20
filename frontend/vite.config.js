import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/ask': {
        target: 'https://hh26-t2-608791195197.us-east1.run.app',
        changeOrigin: true,
        secure: true,
      },
      '/health': {
        target: 'https://hh26-t2-608791195197.us-east1.run.app',
        changeOrigin: true,
        secure: true,
      },
    },
  },
});
