/**
 * Supabase Cloud Client for Sari-Sari / Coldcut POS
 * ==================================================
 * Provides direct cloud data access for standalone Xiaomi Pad terminals,
 * allowing full POS operations (catalog, checkout, utang, GCash) without
 * requiring a counter PC or local Python server.
 */

import { createClient } from '@supabase/supabase-js'

// Load credentials from Vite environment variables with safe project defaults
const SUPABASE_URL =
  (import.meta.env.VITE_SUPABASE_URL as string) ||
  'https://dveufoeavxegvcgityax.supabase.co'

const SUPABASE_PUBLISHABLE_KEY =
  (import.meta.env.VITE_SUPABASE_ANON_KEY as string) ||
  (import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY as string) ||
  'sb_publishable_XspkEupLtXXn9soU9vBOLw_XGfLyof8'

export const supabase = createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: false
  }
})

export function isCloudConfigured(): boolean {
  return Boolean(SUPABASE_URL && SUPABASE_PUBLISHABLE_KEY)
}

/**
 * Ensures a session is active (attempts anonymous sign-in if enabled,
 * otherwise utilizes the public client credentials).
 */
export async function ensureCashierSession(): Promise<void> {
  try {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) {
      // Try anonymous sign-in if enabled on the Supabase project
      await supabase.auth.signInAnonymously().catch(() => {
        // Safe to ignore if anonymous sign-in is disabled; public RLS policies still apply
      })
    }
  } catch (err) {
    console.warn('[Supabase] Session initialization check:', err)
  }
}
