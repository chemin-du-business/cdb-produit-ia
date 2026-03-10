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

function Check() {
  return <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-600/70" />;
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
      <div className="pointer-events-none fixed inset-0">
        <div className="absolute -top-48 left-1/2 h-[520px] w-[900px] -translate-x-1/2 rounded-full bg-gradient-to-r from-indigo-300/40 via-sky-300/40 to-fuchsia-300/40 blur-3xl" />
        <div className="absolute bottom-0 left-0 h-[320px] w-[520px] rounded-full bg-gradient-to-r from-sky-200/50 to-indigo-200/20 blur-3xl" />
      </div>

      <header className="sticky top-0 z-50 border-b border-black/10 bg-white/70 backdrop-blur">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-5">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-black/10 bg-black/[0.03]">
              <span className="text-sm font-semibold text-black">CDB</span>
            </div>
            <span className="text-sm font-semibold tracking-tight text-black">
              CDB Produit IA
            </span>
          </Link>

          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="rounded-2xl border border-black/10 bg-white/80 px-4 py-2 text-sm font-semibold text-black/80 hover:bg-white"
            >
              Retour
            </Link>
          </div>
        </div>
      </header>

      <section className="relative mx-auto w-full max-w-6xl px-6 pb-16 pt-8">
        <div className="grid gap-8 lg:grid-cols-[1fr_460px] lg:items-center">
          <div>
            <div className="flex flex-wrap gap-2">
              <Pill>100% gratuit</Pill>
              <Pill>Connexion rapide</Pill>
              <Pill>Accès immédiat à l’app</Pill>
            </div>

            <h1 className="mt-5 text-4xl font-extrabold leading-[1.04] tracking-tight md:text-5xl">
              Connecte-toi et accède gratuitement à
              <br className="hidden md:block" />
              <span className="text-black/60">l’application CDB Produit IA.</span>
            </h1>

            <p className="mt-4 max-w-xl text-base leading-relaxed text-black/60">
              En quelques secondes, tu accèdes à l’application pour découvrir les
              produits détectés, leur scoring, et les analyses IA qui t’aident à
              choisir plus vite quoi lancer.
            </p>

            <div className="mt-8 rounded-[28px] border border-black/10 bg-white/70 p-5 shadow-sm backdrop-blur">
              <div className="text-sm font-semibold text-black/80">
                Ce que tu débloques dans l’application
              </div>
              <ul className="mt-4 space-y-3 text-sm text-black/60">
                <li className="flex gap-2">
                  <Check />
                  <span>Les produits gagnants détectés par l’IA</span>
                </li>
                <li className="flex gap-2">
                  <Check />
                  <span>Le scoring produit selon plusieurs signaux</span>
                </li>
                <li className="flex gap-2">
                  <Check />
                  <span>Les analyses marketing pour passer plus vite au lancement</span>
                </li>
              </ul>
            </div>

            <div className="mt-6 flex flex-wrap items-center gap-3 text-sm text-black/55">
              <span className="font-semibold text-black/70">Application gratuite</span>
              <span className="text-black/20">•</span>
              <span>Connexion en 1 minute</span>
              <span className="text-black/20">•</span>
              <span>Accès direct à l’app</span>
            </div>
          </div>

          <div className="rounded-[32px] border border-black/10 bg-white/75 p-6 shadow-sm backdrop-blur">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-sm font-semibold text-black/70">Connexion</div>
                <div className="mt-1 text-xl font-extrabold tracking-tight">
                  Accéder à l’application
                </div>
              </div>
              <div className="rounded-2xl bg-black px-3 py-2 text-xs font-bold text-white">
                Gratuit
              </div>
            </div>

            <p className="mt-3 text-sm leading-relaxed text-black/60">
              Choisis la méthode la plus simple pour entrer dans l’app et commencer.
            </p>

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

            <p className="mt-5 text-xs leading-relaxed text-black/45">
              En te connectant, tu acceptes nos conditions d’utilisation et notre politique de confidentialité.
            </p>
          </div>
        </div>

        <footer className="mt-14 border-t border-black/10 pt-6 text-sm text-black/55">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="font-semibold text-black/80">© {new Date().getFullYear()} CDB Produit IA</div>
              <div className="mt-1 text-xs text-black/45">
                Accès gratuit à l’application, au scoring et aux analyses IA.
              </div>
            </div>

            <div className="flex flex-wrap gap-4">
              <Link className="hover:text-black" href="/mentions-legales">
                Mentions légales
              </Link>
              <Link className="hover:text-black" href="/confidentialite">
                Confidentialité
              </Link>
              <Link className="hover:text-black" href="/contact">
                Contact
              </Link>
            </div>
          </div>
        </footer>
      </section>
    </main>
  );
}
