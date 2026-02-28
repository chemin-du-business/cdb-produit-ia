"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";
import Link from "next/link";

function Pill({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full border border-black/10 bg-white/70 px-3 py-1 text-xs font-medium text-black/70 backdrop-blur">
      {children}
    </span>
  );
}

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [msg, setMsg] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const redirectTo =
    typeof window !== "undefined"
      ? `${window.location.origin}/auth/callback`
      : undefined;

  // ✅ Si déjà connecté, on envoie direct vers /app
  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (data.session) router.replace("/app");
    });
  }, [router]);

  async function loginGoogle() {
    setLoading(true);
    setMsg("");
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo },
    });
    if (error) setMsg(error.message);
    setLoading(false);
  }

  async function loginMagic(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMsg("");
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: redirectTo },
    });
    if (error) setMsg(error.message);
    else setMsg("✅ Lien envoyé ! Vérifie ta boîte mail.");
    setLoading(false);
  }

  return (
    <main className="min-h-screen bg-[#f6f7fb] text-black">
      {/* Background glow */}
      <div className="pointer-events-none fixed inset-0">
        <div className="absolute -top-48 left-1/2 h-[520px] w-[900px] -translate-x-1/2 rounded-full bg-gradient-to-r from-indigo-300/40 via-sky-300/40 to-fuchsia-300/40 blur-3xl" />
        <div className="absolute bottom-0 left-0 h-[320px] w-[520px] rounded-full bg-gradient-to-r from-sky-200/50 to-indigo-200/20 blur-3xl" />
      </div>

      {/* Header */}
      <header className="relative mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6">
        <Link href="/" className="flex items-center gap-3">
          <div className="h-11 w-11 rounded-2xl bg-black shadow-sm" />
          <div className="leading-tight">
            <div className="text-xs font-semibold tracking-wide text-black/60">
              CDB
            </div>
            <div className="text-lg font-extrabold tracking-tight">
              Produit IA
            </div>
          </div>
        </Link>

        <Link
          href="/"
          className="rounded-2xl border border-black/10 bg-white/70 px-4 py-2 text-sm font-semibold text-black/80 hover:bg-white"
        >
          Retour
        </Link>
      </header>

      {/* Content */}
      <section className="relative mx-auto w-full max-w-6xl px-6 pb-16 pt-4">
        <div className="grid gap-8 lg:grid-cols-2 lg:items-center">
          {/* Left */}
          <div>
            <div className="flex flex-wrap gap-2">
              <Pill>Google OAuth</Pill>
              <Pill>Magic Link</Pill>
              <Pill>Session mémorisée</Pill>
            </div>

            <h1 className="mt-5 text-4xl font-extrabold leading-[1.05] tracking-tight md:text-5xl">
              Accède gratuitement au <span className="text-black">Top Produits</span>
              <br className="hidden md:block" />
              <span className="text-black/60">et aux angles IA.</span>
            </h1>

            <p className="mt-4 max-w-xl text-base leading-relaxed text-black/60">
              Connecte-toi pour débloquer l’analyse complète : hooks, objections,
              risques et recommandations. Ta session est mémorisée : tu ne te
              reconnectes pas à chaque fois.
            </p>

            <div className="mt-8 rounded-[28px] border border-black/10 bg-white/70 p-5 shadow-sm backdrop-blur">
              <div className="text-sm font-semibold text-black/80">
                ✅ Pourquoi se connecter ?
              </div>
              <ul className="mt-3 space-y-2 text-sm text-black/60">
                <li>• Voir le Top complet (pas seulement le teaser)</li>
                <li>• Accéder à l’historique (2 semaines)</li>
                <li>• Sauvegarder l’accès et éviter les abus</li>
              </ul>
            </div>
          </div>

          {/* Right: Login card */}
          <div className="rounded-[32px] border border-black/10 bg-white/70 p-6 shadow-sm backdrop-blur">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-sm font-semibold text-black/70">Connexion</div>
                <div className="mt-1 text-xl font-extrabold tracking-tight">
                  CDB Produit IA
                </div>
              </div>
              <div className="rounded-2xl bg-black px-3 py-2 text-xs font-bold text-white">
                Gratuit
              </div>
            </div>

            <button
              onClick={loginGoogle}
              disabled={loading}
              className="mt-6 inline-flex w-full items-center justify-center rounded-2xl bg-black px-4 py-3 text-sm font-semibold text-white hover:bg-black/90 disabled:opacity-60"
            >
              Continuer avec Google
            </button>

            <div className="my-5 flex items-center gap-3">
              <div className="h-px flex-1 bg-black/10" />
              <div className="text-xs font-semibold text-black/40">ou</div>
              <div className="h-px flex-1 bg-black/10" />
            </div>

            <form onSubmit={loginMagic} className="space-y-3">
              <label className="block text-xs font-semibold text-black/60">
                Email (lien magique)
              </label>
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                type="email"
                required
                placeholder="ton@email.com"
                className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm outline-none ring-black/10 focus:ring-2"
              />
              <button
                type="submit"
                disabled={loading}
                className="inline-flex w-full items-center justify-center rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm font-semibold text-black/80 hover:bg-white/90 disabled:opacity-60"
              >
                Recevoir un lien de connexion
              </button>
            </form>

            {msg && (
              <div className="mt-4 rounded-2xl border border-black/10 bg-black/5 p-3 text-sm text-black/70">
                {msg}
              </div>
            )}

            <p className="mt-5 text-xs text-black/45">
              En te connectant, tu acceptes nos conditions d’utilisation et la
              politique de confidentialité.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}