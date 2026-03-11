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

function GoogleIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className="h-4 w-4"
    >
      <path
        fill="#EA4335"
        d="M12 10.2v3.9h5.4c-.2 1.2-.9 2.3-1.9 3l3.1 2.4c1.8-1.7 2.9-4.1 2.9-6.9 0-.7-.1-1.5-.2-2.2H12Z"
      />
      <path
        fill="#34A853"
        d="M12 21c2.6 0 4.8-.9 6.4-2.4l-3.1-2.4c-.9.6-2 .9-3.3.9-2.5 0-4.6-1.7-5.3-4H3.5v2.5C5.1 18.9 8.2 21 12 21Z"
      />
      <path
        fill="#FBBC05"
        d="M6.7 13.1c-.2-.6-.3-1.2-.3-1.9s.1-1.3.3-1.9V6.8H3.5C2.9 8 2.5 9.3 2.5 10.6s.4 2.6 1 3.8l3.2-1.3Z"
      />
      <path
        fill="#4285F4"
        d="M12 5.1c1.4 0 2.7.5 3.6 1.4l2.7-2.7C16.8 2.2 14.6 1.2 12 1.2c-3.8 0-6.9 2.1-8.5 5.2l3.2 2.5c.7-2.3 2.8-3.8 5.3-3.8Z"
      />
    </svg>
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
          </div>

          <div className="rounded-[32px] border border-black/10 bg-white/75 p-6 shadow-sm backdrop-blur">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-sm font-semibold text-black/70">Connexion</div>
                <div className="mt-1 text-xl font-extrabold tracking-tight">
                  Accéder à l’application
                </div>
              </div>
            </div>

            <p className="mt-3 text-sm leading-relaxed text-black/60">
              Choisis la méthode la plus simple pour entrer dans l’app et commencer.
            </p>

            <button
              onClick={loginGoogle}
              disabled={loading}
              className="mt-6 inline-flex w-full items-center justify-center gap-3 rounded-2xl bg-black px-4 py-3 text-sm font-semibold text-white hover:bg-black/90 disabled:opacity-60"
            >
              <GoogleIcon />
              <span>Continuer avec Google</span>
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