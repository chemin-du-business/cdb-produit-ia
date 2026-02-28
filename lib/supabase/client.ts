import { createClient } from "@supabase/supabase-js";

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  {
    auth: {
      persistSession: true,     // ✅ garde la session
      autoRefreshToken: true,   // ✅ rafraîchit le token
      detectSessionInUrl: true, // ✅ récupère la session après OAuth/Magic link
    },
  }
);