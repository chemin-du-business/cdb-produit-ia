"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { supabase } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";

type Product = {
  id: string;
  run_date?: string;
  created_at?: string;
  title: string;
  slug: string;
  category: string;
  score: number;
  sources: string[];
  summary: string;
  image_url: string | null;
  source_url: string | null;
};

function Pill({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full border border-black/10 bg-white/70 px-3 py-1 text-xs font-medium text-black/70">
      {children}
    </span>
  );
}

/** --- Helpers TikTok / Video --- **/

function isTikTokUrl(url?: string | null) {
  if (!url) return false;
  try {
    const u = new URL(url);
    return u.hostname.includes("tiktok.com");
  } catch {
    return false;
  }
}

function isDirectMp4Url(url?: string | null) {
  if (!url) return false;
  return url.toLowerCase().includes(".mp4");
}

function extractTikTokVideoId(url?: string | null) {
  if (!url) return null;
  const m = url.match(/\/video\/(\d+)/);
  return m?.[1] ?? null;
}

/**
 * TikTok embed LAZY (charge seulement quand la card arrive à l'écran)
 * + preview instantanée (image_url)
 *
 * NOTE: on NE PEUT PAS forcer le loop d'un iframe TikTok.
 */
function TikTokEmbedLazy({ url, poster }: { url: string; poster?: string | null }) {
  const wrapRef = useRef<HTMLDivElement | null>(null);
  const [shouldLoad, setShouldLoad] = useState(false);

  const videoId = extractTikTokVideoId(url);
  const embedUrl = videoId ? `https://www.tiktok.com/embed/v2/${videoId}` : null;

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;

    const io = new IntersectionObserver(
      (entries) => {
        const e = entries[0];
        if (e?.isIntersecting) {
          setShouldLoad(true);
          io.disconnect();
        }
      },
      { rootMargin: "300px 0px", threshold: 0.01 }
    );

    io.observe(el);
    return () => io.disconnect();
  }, []);

  return (
    <div ref={wrapRef} className="relative h-full w-full bg-black">
      {/* preview instantanée */}
      {!shouldLoad && poster ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={poster} alt="" className="h-full w-full object-cover opacity-95" />
      ) : null}

      {/* loader pendant que l'iframe se prépare */}
      {!shouldLoad ? (
        <div className="absolute inset-0 grid place-items-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-white/30 border-t-white/90" />
        </div>
      ) : null}

      {shouldLoad && embedUrl ? (
        <iframe
          src={embedUrl}
          className="absolute inset-0 h-full w-full"
          loading="lazy"
          allow="autoplay; encrypted-media; fullscreen; picture-in-picture"
          sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
          title="TikTok video"
        />
      ) : null}
    </div>
  );
}

/**
 * Player mp4 (source_url direct mp4)
 * - autoplay muted + loop
 * - bouton play/pause
 */
function VideoPlayer({ src, title }: { src: string; title: string }) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(true);

  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;

    v.muted = true;
    v.playsInline = true;
    v.loop = true; // ✅ loop mp4
    v.preload = "metadata";

    const play = async () => {
      try {
        await v.play();
        setIsPlaying(true);
      } catch {
        setIsPlaying(false);
      }
    };

    play();
  }, []);

  const toggle = async () => {
    const v = videoRef.current;
    if (!v) return;

    if (v.paused) {
      try {
        await v.play();
        setIsPlaying(true);
      } catch {
        setIsPlaying(false);
      }
    } else {
      v.pause();
      setIsPlaying(false);
    }
  };

  return (
    <div className="relative h-full w-full">
      <video
        ref={videoRef}
        className="h-full w-full object-contain bg-black"
        src={src}
        muted
        playsInline
        loop
        autoPlay
      />

      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          toggle();
        }}
        className="absolute bottom-3 right-3 rounded-2xl bg-black/90 px-3 py-2 text-xs font-extrabold text-white hover:bg-black"
        aria-label={isPlaying ? "Pause" : "Lecture"}
        title={isPlaying ? "Pause" : "Lecture"}
      >
        {isPlaying ? "⏸" : "▶️"}
      </button>

      <div className="sr-only">{title}</div>
    </div>
  );
}

/**
 * MediaHero:
 * 1) mp4 direct => <video loop>
 * 2) TikTok => iframe lazy + anti-clic
 * 3) image fallback
 */
function MediaHero({ p }: { p: Product }) {
  if (isDirectMp4Url(p.source_url)) {
    return <VideoPlayer src={p.source_url!} title={p.title} />;
  }

  if (isTikTokUrl(p.source_url)) {
    const id = extractTikTokVideoId(p.source_url);
    if (!id) {
      if (p.image_url) {
        // eslint-disable-next-line @next/next/no-img-element
        return <img src={p.image_url} alt={p.title} className="h-full w-full object-cover" />;
      }
      return <div className="h-full w-full bg-black/10" />;
    }

    return (
      <div className="relative h-full w-full">
        <TikTokEmbedLazy url={p.source_url!} poster={p.image_url} />

        {/* anti-clic pour éviter de sortir vers TikTok */}
        <div
          className="absolute inset-0 z-10"
          onClick={(e) => e.stopPropagation()}
          onMouseDown={(e) => e.stopPropagation()}
          onTouchStart={(e) => e.stopPropagation()}
        />
      </div>
    );
  }

  if (p.image_url) {
    // eslint-disable-next-line @next/next/no-img-element
    return <img src={p.image_url} alt={p.title} className="h-full w-full object-cover" />;
  }

  return <div className="h-full w-full" />;
}

/** --- Date helpers (semaine ISO en Europe/Paris) --- **/

const TZ = "Europe/Paris";

function formatYMDInTZ(date: Date, timeZone: string) {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
}

function addDays(date: Date, days: number) {
  const d = new Date(date);
  d.setDate(d.getDate() + days);
  return d;
}

function getWeekBoundsParis(offsetWeeks: number) {
  const todayParisYMD = formatYMDInTZ(new Date(), TZ);
  const base = new Date(`${todayParisYMD}T00:00:00`);

  const day = base.getDay();
  const diffToMonday = (day + 6) % 7;
  const monday = addDays(base, -diffToMonday + offsetWeeks * -7);
  const sunday = addDays(monday, 6);

  const startYMD = formatYMDInTZ(monday, TZ);
  const endYMD = formatYMDInTZ(sunday, TZ);

  const startISO = `${startYMD}T00:00:00.000Z`;
  const endISO = `${endYMD}T23:59:59.999Z`;

  return { startYMD, endYMD, startISO, endISO };
}

async function fetchProductsByCreatedAtRange(startISO: string, endISO: string) {
  const { data, error } = await supabase
    .from("products")
    .select(
      "id,run_date,created_at,title,slug,category,score,sources,summary,image_url,source_url,is_hidden,mode"
    )
    .gte("created_at", startISO)
    .lte("created_at", endISO)
    .eq("is_hidden", false)
    .order("score", { ascending: false })
    .limit(120);

  if (error) throw error;
  return (data ?? []) as Product[];
}

export default function DashboardPage() {
  const router = useRouter();

  const [email, setEmail] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [currentWeekLabel, setCurrentWeekLabel] = useState<string>("—");
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
        const hay = `${p.title} ${p.category}`.toLowerCase();
        return hay.includes(query);
      })
      .sort((a, b) => b.score - a.score);
  }, [products, q, category, source, minScore]);

  useEffect(() => {
    let mounted = true;

    const init = async () => {
      try {
        setLoadError(null);

        const { data: sessionData, error: sessErr } = await supabase.auth.getSession();
        if (sessErr) console.error(sessErr);

        if (!sessionData.session) {
          router.replace("/login");
          return;
        }
        const user = sessionData.session.user;
        if (mounted) setEmail(user.email ?? null);

        const w0 = getWeekBoundsParis(0);
        const weekLabel = `${w0.startYMD} → ${w0.endYMD}`;
        if (mounted) setCurrentWeekLabel(weekLabel);

        const weekProducts = await fetchProductsByCreatedAtRange(w0.startISO, w0.endISO);
        if (mounted) {
          setProducts(weekProducts.slice(0, 60));
          setLoading(false);
        }
      } catch (e: any) {
        console.error(e);
        if (mounted) {
          setLoadError(e?.message ?? "Erreur inconnue");
          setLoading(false);
        }
      }
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
      <div className="pointer-events-none fixed inset-0">
        <div className="absolute -top-48 left-1/2 h-[420px] w-[820px] -translate-x-1/2 rounded-full bg-gradient-to-r from-indigo-300/30 via-sky-300/30 to-fuchsia-300/30 blur-3xl" />
      </div>

      <header className="relative mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6">
        <div className="flex cursor-pointer items-center gap-3" onClick={() => router.push("/")}>
          <div className="h-10 w-10 rounded-2xl bg-black" />
          <div className="leading-tight">
            <div className="text-xs font-semibold tracking-wide text-black/60">CDB</div>
            <div className="text-lg font-extrabold tracking-tight">Produit IA</div>
          </div>
        </div>

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
                Semaine actuelle (created_at) :{" "}
                <span className="font-semibold text-black/80">{currentWeekLabel}</span>
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Pill>🇫🇷 France</Pill>
              <Pill>🔁 Hebdo</Pill>
              <Pill>🤖 Analyse IA</Pill>
            </div>
          </div>

          {loadError && (
            <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
              Erreur Supabase : {loadError}
            </div>
          )}

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
              <div
                key={p.id}
                role="link"
                tabIndex={0}
                onClick={() => router.push(`/app/product/${p.slug}`)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    router.push(`/app/product/${p.slug}`);
                  }
                }}
                className="group cursor-pointer overflow-hidden rounded-[32px] border border-black/10 bg-white/80 shadow-sm hover:bg-white focus:outline-none focus:ring-2 focus:ring-black/10"
              >
                <div className="relative aspect-[9/16] w-full bg-black/5">
                  <MediaHero p={p} />
                  <div className="absolute right-3 top-3 rounded-2xl bg-black px-3 py-2 text-xs font-extrabold text-white">
                    {p.score}/100
                  </div>
                </div>

                <div className="p-5">
                  <div className="text-xs font-semibold text-black/50">{p.category}</div>
                  <div className="mt-1 line-clamp-2 text-lg font-extrabold tracking-tight text-black/90">
                    {p.title}
                  </div>

                  <p className="mt-4 line-clamp-2 text-sm text-black/60">{p.summary}</p>

                  <div className="mt-4 text-xs text-black/45">
                    Sources : {(p.sources ?? []).join(", ")}
                  </div>
                </div>
              </div>
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