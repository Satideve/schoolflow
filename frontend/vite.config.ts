/* C:\coding_projects\dev\schoolflow\frontend\vite.config.ts */
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from "url";
import path from "path";

/**
 * ESM-compatible __dirname replacement
 */
const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // convenient alias to import from '@/...'
      "@": path.resolve(__dirname, "src"),
    },
  },
  server: {
    port: 5173,
    // Proxy API calls to backend to avoid CORS during local development.
    // Any request starting with /api will be forwarded to http://localhost:8000
    // preserving the path (e.g. /api/v1/auth/login -> http://localhost:8000/api/v1/auth/login).
    proxy: {
      "^/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path, // no rewrite needed, kept explicit
      },
      // Optional: proxy /pdf or other backend static paths if needed:
      "^/static": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
