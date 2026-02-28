"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { supabase } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";

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
};

function Pill({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full border border-black/10 bg-white/70 px-3 py-1 text-xs font-medium text-black/70">
      {children}
    </span>
  );
}

export default function DashboardPage() {
  const router = useRouter();

  const [email, setEmail] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [products, setProducts] = useState<Product[]>([]);
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("all");
  const [source, setSource] = useState("all");
  const [minScore, setMinScore] = useState(0);

  const categories = useMemo(() => {
    const set = new Set<string>();
    products.forEach((p) => set.add(p.category || "autre"));
    return ["all", ...Array.from(set).sort()];
  }, [products]);

  const sources = useMemo(() => {
    const set = new Set<string>();
    products.forEach((p) => (p.sources ?? []).forEach((s) => set.add(s)));
    return ["all", ...Array.from(set).sort()];
  }, [products]);

  const filtered = useMemo(() => {
    const query = q.trim().toLowerCase();
    return products
      .filter((p) => (category === "all" ? true : p.category === category))
      .filter((p) => (source === "all" ? true : (p.sources ?? []).includes(source)))
      .filter((p) => p.score >= minScore)
      .filter((p) => {
        if (!query) return true;
        const hay = `${p.title} ${(p.tags ?? []).join(" ")} ${p.category}`.toLowerCase();
        return hay.includes(query);
      })
      .sort((a, b) => b.score - a.score);
  }, [products, q, category, source, minScore]);

  useEffect(() => {
    let mounted = true;

    const init = async () => {
      // 1) Check session
      const { data: sessionData } = await supabase.auth.getSession();
      if (!sessionData.session) {
        router.replace("/login");
        return;
      }
      const user = sessionData.session.user;
      if (mounted) setEmail(user.email ?? null);

      // 2) Load settings (current_run_date)
      const { data: settingsRows } = await supabase
        .from("settings")
        .select("key,value")
        .in("key", ["current_run_date"]);

      const map = new Map<string, any>();
      (settingsRows ?? []).forEach((r) => map.set(r.key, r.value));
      const runDate = String(map.get("current_run_date")?.v ?? "");

      // 3) Load products (current run + within history is already handled by RLS)
      // If runDate exists, filter by run_date = current run for the main dashboard.
      let query = supabase
        .from("products")
        .select("id,title,slug,category,score,tags,sources,summary,image_url")
        .order("score", { ascending: false })
        .limit(50);

      if (runDate) query = query.eq("run_date", runDate);

      const { data: prod, error } = await query;
      if (error) {
        console.error(error);
      } else if (mounted) {
        setProducts((prod ?? []) as Product[]);
      }

      if (mounted) setLoading(false);
    };

    const { data: sub } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!session) router.replace("/login");
    });

    init();

    return () => {
      mounted = false;
      sub.subscription.unsubscribe();
    };
  }, [router]);

  async function logout() {
    await supabase.auth.signOut();
    router.replace("/");
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#f6f7fb] p-6">
        <div className="mx-auto max-w-6xl rounded-3xl border border-black/10 bg-white/70 p-6">
          Chargement…
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-[#f6f7fb] text-black">
      {/* top background */}
      <div className="pointer-events-none fixed inset-0">
        <div className="absolute -top-48 left-1/2 h-[420px] w-[820px] -translate-x-1/2 rounded-full bg-gradient-to-r from-indigo-300/30 via-sky-300/30 to-fuchsia-300/30 blur-3xl" />
      </div>

      <header className="relative mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6">
        <Link href="/" className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-2xl bg-black" />
          <div className="leading-tight">
            <div className="text-xs font-semibold tracking-wide text-black/60">CDB</div>
            <div className="text-lg font-extrabold tracking-tight">Produit IA</div>
          </div>
        </Link>

        <div className="flex items-center gap-3">
          <Pill>{email ?? "Connecté"}</Pill>
          <button
            onClick={logout}
            className="rounded-2xl border border-black/10 bg-white/70 px-4 py-2 text-sm font-semibold text-black/80 hover:bg-white"
          >
            Déconnexion
          </button>
        </div>
      </header>

      <section className="relative mx-auto w-full max-w-6xl px-6 pb-16">
        <div className="rounded-[32px] border border-black/10 bg-white/70 p-6 shadow-sm backdrop-blur">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h1 className="text-2xl font-extrabold tracking-tight">
                Dashboard — Top produits (semaine)
              </h1>
              <p className="mt-1 text-sm text-black/60">
                Filtre et clique sur un produit pour voir l’analyse complète.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Pill>🇫🇷 France</Pill>
              <Pill>🔁 Hebdo</Pill>
              <Pill>🤖 Analyse IA</Pill>
            </div>
          </div>

          {/* Filters */}
          <div className="mt-6 grid gap-3 md:grid-cols-4">
            <div className="md:col-span-2">
              <label className="text-xs font-semibold text-black/60">Recherche</label>
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Ex: brosse, cuisine, fitness…"
                className="mt-1 w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-black/10"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-black/60">Catégorie</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="mt-1 w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm outline-none"
              >
                {categories.map((c) => (
                  <option key={c} value={c}>
                    {c === "all" ? "Toutes" : c}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-black/60">Source</label>
              <select
                value={source}
                onChange={(e) => setSource(e.target.value)}
                className="mt-1 w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm outline-none"
              >
                {sources.map((s) => (
                  <option key={s} value={s}>
                    {s === "all" ? "Toutes" : s}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-4 flex items-center gap-3">
            <div className="text-xs font-semibold text-black/60">Score min</div>
            <input
              type="range"
              min={0}
              max={100}
              value={minScore}
              onChange={(e) => setMinScore(Number(e.target.value))}
              className="w-full"
            />
            <Pill>{minScore}</Pill>
          </div>

          {/* List */}
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map((p) => (
              <Link
                key={p.id}
                href={`/app/product/${p.slug}`}
                className="group overflow-hidden rounded-[32px] border border-black/10 bg-white/80 shadow-sm hover:bg-white"
              >
                <div className="relative h-44 bg-black/5">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  {p.image_url ? (
                    <img
                      src={p.image_url}
                      alt={p.title}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <div className="h-full w-full" />
                  )}

                  <div className="absolute right-3 top-3 rounded-2xl bg-black px-3 py-2 text-xs font-extrabold text-white">
                    {p.score}/100
                  </div>
                </div>

                <div className="p-5">
                  <div className="text-xs font-semibold text-black/50">{p.category}</div>
                  <div className="mt-1 line-clamp-2 text-lg font-extrabold tracking-tight text-black/90">
                    {p.title}
                  </div>

                  <div className="mt-3 flex flex-wrap gap-2">
                    {(p.tags ?? []).slice(0, 4).map((t) => (
                      <span
                        key={t}
                        className="rounded-full border border-black/10 bg-black/5 px-3 py-1 text-xs font-medium text-black/70"
                      >
                        {t}
                      </span>
                    ))}
                  </div>

                  <p className="mt-4 line-clamp-2 text-sm text-black/60">
                    {p.summary}
                  </p>

                  <div className="mt-4 text-xs text-black/45">
                    Sources : {(p.sources ?? []).join(", ")}
                  </div>
                </div>
              </Link>
            ))}

            {filtered.length === 0 && (
              <div className="rounded-3xl border border-black/10 bg-white/70 p-6 text-sm text-black/60">
                Aucun produit avec ces filtres.
              </div>
            )}
          </div>
        </div>
      </section>
    </main>
  );
}