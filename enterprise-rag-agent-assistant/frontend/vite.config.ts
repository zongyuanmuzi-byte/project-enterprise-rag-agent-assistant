import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  base: "/enterprise-rag-frontend/",
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/health": "http://localhost:8010",
      "/documents": "http://localhost:8010",
      "/chat": "http://localhost:8010",
      "/agent": "http://localhost:8010",
      "/feedback": "http://localhost:8010",
    },
  },
});
