"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase/client";

export default function CallbackPage() {
  const router = useRouter();
  const [msg, setMsg] = useState("Connexion en cours...");

  useEffect(() => {
    const run = async () => {
      // Récupère le "code" dans l'URL (OAuth / PKCE)
      const url = new URL(window.location.href);
      const code = url.searchParams.get("code");

      if (code) {
        const { error } = await supabase.auth.exchangeCodeForSession(code);
        if (error) {
          setMsg("Erreur OAuth: " + error.message);
          return;
        }
      }

      // Vérifie session
      const { data } = await supabase.auth.getSession();
      if (!data.session) {
        setMsg("Session introuvable, retour login...");
        router.replace("/login");
        return;
      }

      router.replace("/app");
    };

    run();
  }, [router]);

  return <p style={{ padding: 24 }}>{msg}</p>;
}