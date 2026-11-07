"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";
import Link from "next/link";

function GoogleIcon() {
  return (
    <svg aria-hidden viewBox="0 0 24 24" className="h-4 w-4">
      <path fill="#EA4335" d="M12 10.2v3.9h5.4c-.2 1.2-.9 2.3-1.9 3l3.1 2.4c1.8-1.7 2.9-4.1 2.9-6.9 0-.7-.1-1.5-.2-2.2H12Z"/>
      <path fill="#34A853" d="M12 21c2.6 0 4.8-.9 6.4-2.4l-3.1-2.4c-.9.6-2 .9-3.3.9-2.5 0-4.6-1.7-5.3-4H3.5v2.5C5.1 18.9 8.2 21 12 21Z"/>
      <path fill="#FBBC05" d="M6.7 13.1c-.2-.6-.3-1.2-.3-1.9s.1-1.3.3-1.9V6.8H3.5C2.9 8 2.5 9.3 2.5 10.6s.4 2.6 1 3.8l3.2-1.3Z"/>
      <path fill="#4285F4" d="M12 5.1c1.4 0 2.7.5 3.6 1.4l2.7-2.7C16.8 2.2 14.6 1.2 12 1.2c-3.8 0-6.9 2.1-8.5 5.2l3.2 2.5c.7-2.3 2.8-3.8 5.3-3.8Z"/>
    </svg>
  );
}

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState<"magic" | "password">("magic");
  const [msg, setMsg] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const redirectTo = typeof window !== "undefined"
    ? `${window.location.origin}/auth/callback`
    : undefined;

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (data.session) router.replace("/app");
    });
  }, [router]);

  async function loginGoogle() {
    setLoading(true); setMsg("");
    const { error } = await supabase.auth.signInWithOAuth({ provider: "google", options: { redirectTo } });
    if (error) setMsg(error.message);
    setLoading(false);
  }

  async function loginMagic(e: React.FormEvent) {
    e.preventDefault(); setLoading(true); setMsg("");
    if (mode === "password") {
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) setMsg(error.message);
      else router.replace("/app");
    } else {
      const { error } = await supabase.auth.signInWithOtp({ email, options: { emailRedirectTo: redirectTo } });
      if (error) setMsg(error.message);
      else setMsg("✅ Lien envoyé ! Vérifie ta boîte mail.");
    }
    setLoading(false);
  }

  return (
    <main className="min-h-screen bg-[#06060a] text-white">
      {/* Glows */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
        <div className="absolute -top-40 left-1/2 h-[500px] w-[700px] -translate-x-1/2 rounded-full bg-violet-600/20 blur-[120px]" />
        <div className="absolute bottom-0 right-0 h-[300px] w-[400px] rounded-full bg-orange-500/10 blur-[100px]" />
      </div>

      {/* Nav */}
      <header className="fixed inset-x-0 top-0 z-50 border-b border-white/[0.06] bg-[#06060a]/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-orange-500">
              <span className="text-xs font-black text-white">CDB</span>
            </div>
            <span className="text-sm font-semibold tracking-tight">Produit IA</span>
          </Link>
          <Link href="/" className="inline-flex h-9 items-center rounded-full border border-white/10 bg-white/5 px-4 text-sm font-semibold text-white/70 hover:bg-white/10 transition">
            Retour
          </Link>
        </div>
      </header>

      {/* Content */}
      <section className="relative z-10 mx-auto w-full max-w-6xl px-4 pb-16 pt-28 sm:px-5 sm:pt-36">
        <div className="grid gap-10 lg:grid-cols-[1fr_460px] lg:items-center">

          {/* Left */}
          <div className="text-center lg:text-left">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-violet-500/30 bg-violet-500/10 px-3 py-1.5 text-xs font-semibold text-violet-300">
              <span className="h-1.5 w-1.5 rounded-full bg-violet-400 motion-safe:animate-pulse" />
              100% gratuit
            </div>
            <h1 className="text-3xl font-black leading-[1.08] tracking-tight sm:text-5xl">
              Connecte-toi et accède{" "}
              <span className="bg-gradient-to-r from-violet-400 via-fuchsia-300 to-orange-400 bg-clip-text text-transparent" style={{ WebkitBackgroundClip: "text" }}>
                gratuitement
              </span>
            </h1>
            <p className="mx-auto mt-4 max-w-sm text-sm leading-relaxed text-white/50 lg:mx-0">
              Accède aux produits détectés, leur scoring IA et les analyses marketing pour choisir quoi lancer.
            </p>
          </div>

          {/* Card */}
          <div className="rounded-3xl border border-white/[0.08] bg-white/[0.03] p-6 backdrop-blur sm:p-8">
            <div className="text-lg font-black text-white">Connexion</div>
            <p className="mt-1 text-sm text-white/40">Choisis la méthode la plus simple.</p>

            <button
              onClick={loginGoogle}
              disabled={loading}
              className="mt-6 inline-flex h-11 w-full items-center justify-center gap-3 rounded-full border border-white/10 bg-white/5 text-sm font-semibold text-white hover:bg-white/10 disabled:opacity-60 transition"
            >
              <GoogleIcon />
              Continuer avec Google
            </button>

            <div className="my-5 flex items-center gap-3">
              <div className="h-px flex-1 bg-white/10" />
              <div className="text-xs font-semibold text-white/30">ou</div>
              <div className="h-px flex-1 bg-white/10" />
            </div>

            <div className="flex rounded-full border border-white/10 bg-white/[0.03] p-1 text-xs font-semibold">
              <button type="button" onClick={() => setMode("magic")} className={`flex-1 rounded-full py-2 transition-colors ${mode === "magic" ? "bg-white/10 text-white" : "text-white/40"}`}>
                Lien magique
              </button>
              <button type="button" onClick={() => setMode("password")} className={`flex-1 rounded-full py-2 transition-colors ${mode === "password" ? "bg-white/10 text-white" : "text-white/40"}`}>
                Email + mot de passe
              </button>
            </div>

            <form onSubmit={loginMagic} className="mt-4 space-y-3">
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                type="email" required
                placeholder="ton@email.com"
                className="h-11 w-full rounded-full border border-white/10 bg-white/5 px-4 text-sm text-white placeholder:text-white/30 outline-none focus:border-violet-500/50"
              />
              {mode === "password" && (
                <input
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  type="password" required
                  placeholder="Mot de passe"
                  className="h-11 w-full rounded-full border border-white/10 bg-white/5 px-4 text-sm text-white placeholder:text-white/30 outline-none focus:border-violet-500/50"
                />
              )}
              <button
                type="submit" disabled={loading}
                className="inline-flex h-11 w-full items-center justify-center rounded-full bg-gradient-to-r from-violet-600 to-orange-500 text-sm font-semibold text-white hover:brightness-110 disabled:opacity-60 transition"
              >
                {mode === "password" ? "Se connecter" : "Recevoir un lien de connexion"}
              </button>
            </form>

            {msg && (
              <div className="mt-4 rounded-2xl border border-white/10 bg-white/5 p-3 text-sm text-white/70">
                {msg}
              </div>
            )}

            <p className="mt-5 text-xs leading-relaxed text-white/25">
              En te connectant, tu acceptes nos{" "}
              <Link href="/mentions-legales" className="underline hover:text-white/50">conditions</Link>{" "}
              et notre{" "}
              <Link href="/confidentialite" className="underline hover:text-white/50">politique de confidentialité</Link>.
            </p>
          </div>
        </div>
      </section>

      <footer className="relative z-10 border-t border-white/[0.06] px-5 py-8">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <span className="text-sm text-white/30">© {new Date().getFullYear()} CDB Produit IA</span>
          <div className="flex flex-wrap gap-5 text-sm text-white/30">
            <Link className="hover:text-white/60 transition" href="/confidentialite">Confidentialité</Link>
            <Link className="hover:text-white/60 transition" href="/mentions-legales">Mentions légales</Link>
            <Link className="hover:text-white/60 transition" href="/contact">Contact</Link>
          </div>
        </div>
      </footer>
    </main>
  );
}
