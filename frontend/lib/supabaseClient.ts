// This file is deprecated. Use lib/supabase/client.ts or lib/supabase/server.ts instead
import { createBrowserClient } from '@supabase/ssr'

export const createSupabaseBrowserClient = () =>
  createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
