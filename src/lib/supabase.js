import { createClient } from '@supabase/supabase-js'

const proxyBase = `${window.location.origin}/sb`
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

export const dataMode =
  import.meta.env.VITE_DATA_MODE === 'mock' ? 'mock' : 'api'

export const isMockMode = dataMode === 'mock'

export const supabase = createClient(proxyBase, anonKey || 'missing-anon-key', {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: false,
  },
})
