import { svelte } from "@sveltejs/vite-plugin-svelte";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [svelte()],
  optimizeDeps: {
    // MapLibre ships a separate worker module; excluding avoids a broken
    // rewrite to /node_modules/.vite/deps/maplibre-gl-worker.mjs (404).
    exclude: ["maplibre-gl"],
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
    watch: {
      usePolling: true,
    },
  },
});
