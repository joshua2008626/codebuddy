import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev proxy keeps the browser on a single origin, so auth cookies work without extra CORS setup.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
});
