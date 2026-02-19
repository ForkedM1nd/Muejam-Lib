import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";
import { securityHeadersPlugin } from "./vite-plugin-security-headers";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8080,
    hmr: {
      overlay: false,
    },
  },
  plugins: [
    react(),
    mode === "development" && componentTagger(),
    securityHeadersPlugin(),
  ].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          // Vendor chunks
          if (id.includes('node_modules')) {
            if (id.includes('react') || id.includes('react-dom') || id.includes('react-router')) {
              return 'react-vendor';
            }
            if (id.includes('@clerk/clerk-react')) {
              return 'clerk';
            }
            if (id.includes('@tanstack/react-query')) {
              return 'tanstack';
            }
            if (id.includes('@radix-ui')) {
              return 'ui';
            }
            if (id.includes('react-markdown') || id.includes('remark') || id.includes('rehype')) {
              return 'markdown';
            }
            if (id.includes('date-fns') || id.includes('clsx') || id.includes('tailwind-merge')) {
              return 'utils';
            }
            if (id.includes('recharts')) {
              return 'charts';
            }
            if (id.includes('lucide-react')) {
              return 'icons';
            }
            // Other node_modules go to vendor
            return 'vendor';
          }

          // Split heavy pages into separate chunks
          if (id.includes('/pages/AdminDashboard')) {
            return 'admin';
          }
          if (id.includes('/pages/AnalyticsDashboard')) {
            return 'analytics';
          }
          if (id.includes('/pages/ModerationQueue') || id.includes('/pages/ModerationReview')) {
            return 'moderation';
          }
          if (id.includes('/pages/StoryEditor') || id.includes('/pages/WriteDashboard')) {
            return 'editor';
          }
          if (id.includes('/pages/Reader')) {
            return 'reader';
          }
        },
      },
    },
    chunkSizeWarningLimit: 600,
    // Enable tree-shaking
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: mode === 'production',
        drop_debugger: mode === 'production',
      },
    },
    // Source maps for production debugging (can be disabled for smaller builds)
    sourcemap: mode !== 'production',
  },
}));
