import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::", // Allows access from network
    port: 8080, // Frontend dev server port
    proxy: {
      // Proxy API requests to the backend server
      '/api/v1': { // Match requests starting with /api/v1
        target: 'http://localhost:1212', // Your FastAPI backend URL (exposed by Docker)
        changeOrigin: true, // Needed for virtual hosted sites
        // secure: false, // Uncomment if your backend is not HTTPS (common in dev)
        // No rewrite needed here if frontend calls /api/v1/... and backend expects /api/v1/...
      },
    },
  },
  plugins: [
    react(),
    mode === 'development' &&
    componentTagger(),
  ].filter(Boolean),
  resolve: {
    alias: {
      // "@": path.resolve(__dirname, "./src"), // Original
      "@": path.resolve(new URL('.', import.meta.url).pathname, "./src"), // ESM-friendly way
    },
  },
}));
