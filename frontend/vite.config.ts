/* C:\coding_projects\dev\schoolflow\frontend\vite.config.ts */
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: false
  },
  preview: { port: 5174 }
});
