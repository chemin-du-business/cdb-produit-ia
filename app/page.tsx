import Link from "next/link";
import { createSupabaseServerClient } from "@/lib/supabase/server";
import HeroOrbit from "@/components/HeroOrbit";
import ProductCardDemo from "@/components/ProductCardDemo";

type RiskItem = {
  note?: string;
  type?: string;
  level?: "high" | "medium" | "low" | string;
};

type Product = {
  id: string;
  title: string;
  slug: string;
  category: string;
  score: number;
  tags: string[];
  sources: string[];
  summary: string;
  image_url: string | null;
  video_storage_url?: string | null;
  analysis?: { risks?: RiskItem[] } | null;
};

export default async function HomePage() {
  const supabase = createSupabaseServerClient();

  const { data: latestRunRow } = await supabase
    .from("products")
    .select("run_date")
    .eq("is_hidden", false)
    .order("run_date", { ascending: false })
    .limit(1)
    .single();

  const latestRunDate = latestRunRow?.run_date ?? null;

  const productsQuery = supabase
    .from("products")
    .select("id,title,slug,category,score,tags,sources,summary,analysis,image_url,video_storage_url")
    .eq("is_hidden", false)
    .order("score", { ascending: false })
    .limit(3);

  if (latestRunDate) {
    productsQuery.eq("run_date", latestRunDate);
  }

  const { data: products } = await productsQuery;

  return (
    <div className="min-h-screen bg-[#06060a] text-white overflow-x-hidden">

      {/* ── Noise texture overlay ── */}
      <div
        className="pointer-events-none fixed inset-0 z-0 opacity-[0.025]"
        style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E\")", backgroundSize: "180px" }}
      />

      {/* ── Ambient glows ── */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
        <div className="absolute -top-40 left-1/2 h-[600px] w-[800px] -translate-x-1/2 rounded-full bg-violet-600/20 blur-[120px]" />
        <div className="absolute top-1/3 -right-40 h-[400px] w-[500px] rounded-full bg-orange-500/10 blur-[120px]" />
        <div className="absolute bottom-0 -left-40 h-[400px] w-[500px] rounded-full bg-indigo-600/15 blur-[120px]" />
      </div>

      {/* ── NAV ── */}
      <header className="fixed inset-x-0 top-0 z-50 border-b border-white/[0.06] bg-[#06060a]/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-orange-500">
              <span className="text-xs font-black text-white">CDB</span>
            </div>
            <span className="text-sm font-semibold tracking-tight text-white">Produit IA</span>
          </Link>

          <div className="flex items-center gap-2">
            <Link href="/login" className="hidden rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-white/80 hover:bg-white/10 sm:inline-flex">
              Connexion
            </Link>
            <Link href="/login" className="inline-flex rounded-xl bg-gradient-to-r from-violet-600 to-orange-500 px-4 py-2 text-sm font-semibold text-white shadow-[0_8px_30px_-8px_rgba(139,92,246,0.5)] hover:brightness-110">
              Démarrer gratuitement
            </Link>
          </div>
        </div>
      </header>

      {/* ── HERO ── */}
      <section className="relative z-10 mx-auto max-w-6xl px-5 pb-16 pt-32 sm:pt-40">
        <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">

          {/* Left */}
          <div>
            {/* Badge */}
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-violet-500/30 bg-violet-500/10 px-3 py-1.5 text-xs font-semibold text-violet-300">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-violet-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-violet-400" />
              </span>
              Radar mis à jour chaque lundi
            </div>

            <h1 className="text-4xl font-black leading-[1.05] tracking-tight sm:text-5xl lg:text-6xl">
              Trouve les{" "}
              <span
                className="bg-gradient-to-r from-violet-400 via-fuchsia-300 to-orange-400 bg-clip-text text-transparent"
                style={{ WebkitBackgroundClip: "text" }}
              >
                produits à vendre
              </span>{" "}
              <br className="hidden sm:block" />
              avant tout le monde.
            </h1>

            <p className="mt-5 max-w-sm text-base leading-relaxed text-white/50">
              Score IA, analyse marketing complète, radar mis à jour chaque semaine.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/login" className="inline-flex items-center gap-2 rounded-2xl bg-gradient-to-r from-violet-600 to-orange-500 px-6 py-3.5 text-sm font-bold text-white shadow-[0_15px_40px_-10px_rgba(139,92,246,0.5)] hover:brightness-110 transition">
                Accéder gratuitement
                <span>→</span>
              </Link>
              <a href="#demo" className="inline-flex items-center rounded-2xl border border-white/10 bg-white/5 px-6 py-3.5 text-sm font-semibold text-white/70 hover:bg-white/10 transition">
                Voir la démo
              </a>
            </div>

            {/* Source pills */}
            <div className="mt-10 flex flex-wrap items-center gap-2.5">
              <span className="text-xs font-medium text-white/30">Sources IA :</span>
              {[
                { name: "TikTok", color: "from-[#010101] to-[#2d2d2d]", glow: "shadow-[0_0_12px_rgba(255,255,255,0.08)]" },
                { name: "TikTok Shop", color: "from-[#EE1D52] to-[#c41542]", glow: "shadow-[0_0_12px_rgba(238,29,82,0.3)]" },
                { name: "Amazon", color: "from-[#FF9900] to-[#e08800]", glow: "shadow-[0_0_12px_rgba(255,153,0,0.3)]" },
                { name: "Meta Ads", color: "from-[#1877F2] to-[#1060cc]", glow: "shadow-[0_0_12px_rgba(24,119,242,0.3)]" },
                { name: "Google", color: "from-[#1f1f1f] to-[#2d2d2d]", glow: "shadow-[0_0_12px_rgba(255,255,255,0.08)]" },
                { name: "Trends", color: "from-emerald-600 to-emerald-800", glow: "shadow-[0_0_12px_rgba(16,185,129,0.3)]" },
              ].map((s) => (
                <span key={s.name} className={`inline-flex items-center rounded-xl bg-gradient-to-r ${s.color} ${s.glow} px-3 py-1.5 text-[11px] font-bold text-white`}>
                  {s.name}
                </span>
              ))}
            </div>
          </div>

          {/* Right: orbit */}
          <div className="flex justify-center lg:justify-end">
            <HeroOrbit />
          </div>
        </div>
      </section>

      {/* ── STATS BAND ── */}
      <section className="relative z-10 mx-auto max-w-6xl px-5 pb-16">
        <div className="grid grid-cols-3 gap-px overflow-hidden rounded-2xl border border-white/[0.07] bg-white/[0.07]">
          {[
            { n: "100%", label: "Gratuit" },
            { n: "6", label: "Sources d'IA" },
            { n: "20+", label: "Produits / semaine" },
          ].map((s) => (
            <div key={s.label} className="flex flex-col items-center justify-center bg-[#06060a] py-7">
              <div className="bg-gradient-to-r from-violet-400 to-orange-400 bg-clip-text text-2xl font-black text-transparent sm:text-3xl">
                {s.n}
              </div>
              <div className="mt-1 text-xs font-medium text-white/40">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section className="relative z-10 mx-auto max-w-6xl px-5 pb-20">
        <div className="mb-10 text-center">
          <h2 className="text-2xl font-black tracking-tight sm:text-3xl">Comment ça marche</h2>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {[
            { n: "01", title: "Détecte", desc: "Scan IA de 6 plateformes chaque lundi", icon: "🔎", glow: "rgba(139,92,246,0.15)", border: "rgba(139,92,246,0.3)" },
            { n: "02", title: "Score", desc: "Score /100 : viralité, pubs, marché", icon: "⚡", glow: "rgba(249,115,22,0.15)", border: "rgba(249,115,22,0.3)" },
            { n: "03", title: "Lance", desc: "Hooks, UGC, risques, fournisseurs", icon: "🚀", glow: "rgba(16,185,129,0.15)", border: "rgba(16,185,129,0.3)" },
          ].map((s) => (
            <div
              key={s.n}
              className="relative overflow-hidden rounded-2xl p-6 backdrop-blur transition"
              style={{ background: `linear-gradient(135deg, ${s.glow} 0%, rgba(6,6,10,0.8) 60%)`, border: `1px solid ${s.border}`, boxShadow: `0 0 30px ${s.glow}` }}
            >
              <div className="mb-5 flex items-center justify-between">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/10 text-2xl backdrop-blur">
                  {s.icon}
                </div>
                <span className="font-mono text-3xl font-black text-white/[0.07]">{s.n}</span>
              </div>
              <h3 className="text-lg font-black text-white">{s.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-white/55">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── DEMO PRODUCTS ── */}
      <section id="demo" className="relative z-10 mx-auto max-w-6xl px-5 pb-20">
        <div className="mb-8 flex items-end justify-between">
          <div>
            <h2 className="text-2xl font-black tracking-tight sm:text-3xl">Produits de la semaine</h2>
            <p className="mt-1 text-sm text-white/40">Aperçu public — analyse complète après connexion.</p>
          </div>
          <Link href="/login" className="hidden rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-white/70 hover:bg-white/10 sm:inline-flex">
            Tout voir →
          </Link>
        </div>

        {(products ?? []).length > 0 ? (
          <div className="grid gap-4 lg:grid-cols-3">
            {(products ?? []).map((p) => (
              <ProductCardDemo key={p.id} product={p} />
            ))}
          </div>
        ) : (
          <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-8 text-center text-sm text-white/40">
            Les produits de la semaine apparaîtront ici dès le prochain run.
          </div>
        )}
      </section>

      {/* ── SOURCE SECTIONS ── */}
      <section className="relative z-10 mx-auto max-w-6xl px-5 pb-24">
        <div className="mb-12 text-center">
          <h2 className="text-3xl font-black tracking-tight sm:text-4xl">On analyse partout pour toi</h2>
        </div>

        {/* Bento grid */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">

          {/* TikTok — large */}
          <div
            className="relative col-span-1 overflow-hidden rounded-3xl p-7 md:col-span-2 lg:col-span-1"
            style={{ background: "linear-gradient(135deg, rgba(10,10,15,0.95) 0%, rgba(20,10,30,0.9) 100%)", border: "1px solid rgba(255,255,255,0.12)", boxShadow: "0 0 60px rgba(255,255,255,0.04), inset 0 1px 0 rgba(255,255,255,0.06)" }}
          >
            <div className="absolute right-0 top-0 h-56 w-56 rounded-full bg-[#69C9D0]/10 blur-3xl" />
            <div className="absolute bottom-0 left-0 h-40 w-40 rounded-full bg-[#EE1D52]/10 blur-3xl" />
            <div className="relative">
              <div className="mb-5 flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-black shadow-[0_0_30px_rgba(105,201,208,0.3)]">
                  <svg viewBox="0 0 24 24" className="h-6 w-6 fill-white"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-2.88 2.5 2.89 2.89 0 0 1-2.89-2.89 2.89 2.89 0 0 1 2.89-2.89c.28 0 .54.04.79.1V9.01a6.33 6.33 0 0 0-.79-.05 6.34 6.34 0 0 0-6.34 6.34 6.34 6.34 0 0 0 6.34 6.34 6.34 6.34 0 0 0 6.33-6.34V8.69a8.19 8.19 0 0 0 4.79 1.53V6.77a4.85 4.85 0 0 1-1.02-.08z" /></svg>
                </div>
                <div>
                  <div className="text-xl font-black text-white">TikTok</div>
                  <div className="text-xs text-white/40">+ TikTok Shop US</div>
                </div>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {["Hashtags viraux", "Vues & engagement", "Shop US", "Tendances -4 sem"].map((t) => (
                  <span key={t} className="rounded-xl border border-[#69C9D0]/30 bg-[#69C9D0]/10 px-3 py-1 text-[11px] font-semibold text-[#69C9D0]">{t}</span>
                ))}
              </div>
            </div>
          </div>

          {/* Amazon */}
          <div
            className="relative overflow-hidden rounded-3xl p-7"
            style={{ background: "linear-gradient(135deg, rgba(255,153,0,0.12) 0%, rgba(10,10,15,0.9) 70%)", border: "1px solid rgba(255,153,0,0.25)", boxShadow: "0 0 40px rgba(255,153,0,0.08)" }}
          >
            <div className="absolute -right-8 -top-8 h-40 w-40 rounded-full bg-[#FF9900]/15 blur-2xl" />
            <div className="relative">
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#FF9900] shadow-[0_0_30px_rgba(255,153,0,0.4)]">
                <svg viewBox="0 0 24 24" className="h-6 w-6 fill-white"><path d="M13.958 10.09c0 1.232.029 2.256-.591 3.351-.502.891-1.301 1.438-2.186 1.438-1.214 0-1.922-.924-1.922-2.292 0-2.692 2.415-3.182 4.699-3.182v.685zm3.186 7.705c-.209.189-.512.201-.745.074-1.047-.872-1.233-1.276-1.814-2.106-1.734 1.767-2.962 2.297-5.209 2.297-2.66 0-4.731-1.641-4.731-4.925 0-2.565 1.391-4.309 3.37-5.164 1.715-.754 4.11-.891 5.942-1.098v-.41c0-.753.06-1.642-.383-2.294-.385-.578-1.124-.816-1.776-.816-1.207 0-2.284.618-2.548 1.9-.054.285-.264.567-.549.582l-3.061-.331c-.259-.058-.548-.266-.472-.66C5.516 2.636 8.246 1.5 10.864 1.5c1.344 0 3.099.359 4.158 1.378 1.344 1.258 1.218 2.939 1.218 4.769v4.323c0 1.299.539 1.869 1.047 2.57.179.251.219.551-.01.736l-2.133 1.519z"/></svg>
              </div>
              <h3 className="text-xl font-black text-white">Amazon</h3>
              <div className="mt-4 flex flex-wrap gap-2">
                {[".fr & .com", "Best-sellers", "Prix marché", "Classements"].map((t) => (
                  <span key={t} className="rounded-xl border border-[#FF9900]/30 bg-[#FF9900]/10 px-3 py-1 text-[11px] font-semibold text-[#FF9900]">{t}</span>
                ))}
              </div>
            </div>
          </div>

          {/* Meta */}
          <div
            className="relative overflow-hidden rounded-3xl p-7"
            style={{ background: "linear-gradient(135deg, rgba(24,119,242,0.12) 0%, rgba(10,10,15,0.9) 70%)", border: "1px solid rgba(24,119,242,0.25)", boxShadow: "0 0 40px rgba(24,119,242,0.08)" }}
          >
            <div className="absolute -right-8 -top-8 h-40 w-40 rounded-full bg-[#1877F2]/15 blur-2xl" />
            <div className="relative">
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#1877F2] shadow-[0_0_30px_rgba(24,119,242,0.4)]">
                <svg viewBox="0 0 24 24" className="h-6 w-6 fill-white"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
              </div>
              <h3 className="text-xl font-black text-white">Meta Ads</h3>
              <div className="mt-4 flex flex-wrap gap-2">
                {["Pubs actives", "E-commerce", "Signal ✓", "Ads Library"].map((t) => (
                  <span key={t} className="rounded-xl border border-[#1877F2]/30 bg-[#1877F2]/10 px-3 py-1 text-[11px] font-semibold text-[#4a9af5]">{t}</span>
                ))}
              </div>
            </div>
          </div>

          {/* Google Trends */}
          <div
            className="relative overflow-hidden rounded-3xl p-7"
            style={{ background: "linear-gradient(135deg, rgba(16,185,129,0.12) 0%, rgba(10,10,15,0.9) 70%)", border: "1px solid rgba(16,185,129,0.25)", boxShadow: "0 0 40px rgba(16,185,129,0.08)" }}
          >
            <div className="absolute -right-8 -top-8 h-40 w-40 rounded-full bg-emerald-500/15 blur-2xl" />
            <div className="relative">
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-white shadow-[0_0_30px_rgba(66,133,244,0.3)]">
                <svg viewBox="0 0 24 24" className="h-6 w-6">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
              </div>
              <h3 className="text-xl font-black text-white">Google Trends</h3>
              <div className="mt-4 flex flex-wrap gap-2">
                {["Tendances FR", "Tendances US", "Courbe temps", "Montée/déclin"].map((t) => (
                  <span key={t} className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-[11px] font-semibold text-emerald-400">{t}</span>
                ))}
              </div>
            </div>
          </div>

          {/* Google Shopping — large */}
          <div
            className="relative col-span-1 overflow-hidden rounded-3xl p-7 md:col-span-2 lg:col-span-1"
            style={{ background: "linear-gradient(135deg, rgba(66,133,244,0.12) 0%, rgba(10,10,15,0.9) 70%)", border: "1px solid rgba(66,133,244,0.25)", boxShadow: "0 0 40px rgba(66,133,244,0.08)" }}
          >
            <div className="absolute -right-8 -top-8 h-40 w-40 rounded-full bg-[#4285F4]/15 blur-2xl" />
            <div className="absolute bottom-0 left-0 h-32 w-32 rounded-full bg-[#EA4335]/10 blur-2xl" />
            <div className="relative">
              <div className="mb-5 flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white shadow-[0_0_30px_rgba(66,133,244,0.3)]">
                  <svg viewBox="0 0 24 24" className="h-6 w-6">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                </div>
                <div>
                  <div className="text-lg font-black text-white">Google Shopping</div>
                  <div className="text-xs text-white/40">Prix réels du marché</div>
                </div>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {["Prix du marché", "Marchands actifs", "Concurrence FR", "Shopping"].map((t) => (
                  <span key={t} className="rounded-xl border border-[#4285F4]/30 bg-[#4285F4]/10 px-3 py-1 text-[11px] font-semibold text-[#7aabf7]">{t}</span>
                ))}
              </div>
            </div>
          </div>

        </div>
      </section>

      {/* ── CTA FINAL ── */}
      <section className="relative z-10 mx-auto max-w-6xl px-5 pb-24">
        <div className="relative overflow-hidden rounded-3xl p-[1px]">
          <div className="absolute inset-0 bg-gradient-to-r from-violet-600 via-fuchsia-500 to-orange-500 opacity-60" />
          <div className="relative rounded-3xl bg-[#0d0d14] px-8 py-12 sm:px-14">
            <div className="grid gap-8 md:grid-cols-[1fr_auto] md:items-center">
              <div>
                <div className="mb-3 inline-flex rounded-full border border-violet-500/30 bg-violet-500/10 px-3 py-1 text-xs font-semibold text-violet-300">
                  100% gratuit pour commencer
                </div>
                <h3 className="text-3xl font-black tracking-tight sm:text-4xl">Commence maintenant.</h3>
                <p className="mt-3 max-w-md text-sm leading-relaxed text-white/50">
                  Radar hebdomadaire, analyses IA complètes, sources vérifiées. Zéro carte bancaire.
                </p>
              </div>
              <Link href="/login" className="inline-flex shrink-0 items-center gap-2 rounded-2xl bg-gradient-to-r from-violet-600 to-orange-500 px-7 py-4 text-sm font-bold text-white shadow-[0_15px_40px_-10px_rgba(139,92,246,0.6)] hover:brightness-110 transition">
                Créer mon compte gratuit
                <span>→</span>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="relative z-10 border-t border-white/[0.06] px-5 py-8">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500 to-orange-500">
              <span className="text-[10px] font-black text-white">CDB</span>
            </div>
            <span className="text-sm font-semibold text-white/60">Produit IA © {new Date().getFullYear()}</span>
          </div>
          <div className="flex flex-wrap gap-5 text-sm text-white/40">
            <Link className="hover:text-white/70 transition" href="/confidentialite">Confidentialité</Link>
            <Link className="hover:text-white/70 transition" href="/mentions-legales">Mentions légales</Link>
            <Link className="hover:text-white/70 transition" href="/contact">Contact</Link>
            <Link className="hover:text-white/70 transition" href="/login">Connexion</Link>
          </div>
        </div>
      </footer>

    </div>
  );
}
