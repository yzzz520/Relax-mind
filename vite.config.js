import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const supabaseTarget = env.VITE_SUPABASE_TARGET_URL

  return {
    plugins: [vue()],
    server: supabaseTarget
      ? {
          proxy: {
            '/sb': {
              target: supabaseTarget,
              changeOrigin: true,
              secure: true,
              rewrite: (path) => path.replace(/^\/sb/, ''),
            },
          },
        }
      : undefined,
  }
})
