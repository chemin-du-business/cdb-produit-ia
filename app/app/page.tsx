"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { supabase } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";

type RiskItem = {
  note?: string;
  type?: string;
  level?: "high" | "medium" | "low" | string;
};

type ProductAnalysis = {
  risks?: RiskItem[];
};

type Product = {
  id: string;
  run_date?: string;
  created_at?: string;
  title: string;
  slug: string;
  category: string;
  score: number;
  status?: string;
  sources: string[];
  summary: string;
  image_url: string | null;
  source_url: string | null;
  video_storage_url: string | null;
  analysis?: ProductAnalysis | null;
  score_breakdown?: {
    tiktok?: number;
    amazon?: number;
    google_trends?: number;
    google_shopping?: number;
    meta_ads?: number;
    tiktok_shop?: number;
  } | null;
};

function Pill({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full border border-black/10 bg-white/70 px-3 py-1 text-xs font-medium text-black/70">
      {children}
    </span>
  );
}

const STATUS_CONFIG: Record<string, { label: string; bg: string; text: string; dot: string }> = {
  "Émergent":    { label: "Émergent",    bg: "bg-violet-100",  text: "text-violet-700", dot: "bg-violet-500" },
  "En tendance": { label: "En tendance", bg: "bg-orange-100",  text: "text-orange-700", dot: "bg-orange-500" },
  "Populaire":   { label: "Populaire",   bg: "bg-emerald-100", text: "text-emerald-700", dot: "bg-emerald-500" },
  "En regain":   { label: "En regain",   bg: "bg-sky-100",     text: "text-sky-700",    dot: "bg-sky-500" },
  "En déclin":   { label: "En déclin",   bg: "bg-red-100",     text: "text-red-600",    dot: "bg-red-500" },
};

function StatusBadge({ status }: { status?: string }) {
  const cfg = STATUS_CONFIG[status ?? ""] ?? { label: status ?? "—", bg: "bg-black/5", text: "text-black/50", dot: "bg-black/30" };
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold ${cfg.bg} ${cfg.text}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${cfg.dot}`} />
      {cfg.label}
    </span>
  );
}

const SOURCE_COLORS: Record<string, { bar: string; label: string }> = {
  tiktok:          { bar: "bg-black",         label: "TikTok" },
  amazon:          { bar: "bg-orange-400",    label: "Amazon" },
  google_trends:   { bar: "bg-blue-400",      label: "G. Trends" },
  google_shopping: { bar: "bg-indigo-400",    label: "G. Shopping" },
  meta_ads:        { bar: "bg-sky-500",       label: "Meta" },
  tiktok_shop:     { bar: "bg-pink-500",      label: "TikTok Shop" },
};

const SOURCE_MAX: Record<string, number> = {
  tiktok: 40, amazon: 20, google_trends: 10, google_shopping: 10, meta_ads: 10, tiktok_shop: 10,
};

const V2_SOURCES = ["tiktok", "amazon", "google_trends", "google_shopping", "meta_ads", "tiktok_shop"];

function ScoreBreakdown({ breakdown }: { breakdown: Product["score_breakdown"] }) {
  if (!breakdown) return null;
  const entries = Object.entries(breakdown).filter(([k, v]) => V2_SOURCES.includes(k) && v !== undefined && v !== null);
  if (!entries.length) return null;
  return (
    <div className="mt-3 space-y-1.5">
      {entries.map(([key, val]) => {
        const cfg = SOURCE_COLORS[key] ?? { bar: "bg-black/40", label: key };
        const max = SOURCE_MAX[key] ?? 20;
        const pct = Math.min(100, Math.round(((val as number) / max) * 100));
        return (
          <div key={key} className="flex items-center gap-2">
            <div className="w-20 shrink-0 text-[10px] text-black/50 truncate">{cfg.label}</div>
            <div className="flex-1 h-1.5 rounded-full bg-black/[0.07] overflow-hidden">
              <motion.div
                className={`h-full rounded-full ${cfg.bar}`}
                initial={{ width: 0 }}
                animate={{ width: `${pct}%` }}
                transition={{ duration: 0.6, ease: "easeOut" }}
              />
            </div>
            <div className="w-5 shrink-0 text-right text-[10px] font-semibold text-black/60">{val as number}</div>
          </div>
        );
      })}
    </div>
  );
}

function LogoutIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className="h-4 w-4"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <path d="M16 17l5-5-5-5" />
      <path d="M21 12H9" />
    </svg>
  );
}

function CPFBadge() {
  return (
    <span className="inline-flex items-center rounded-full border border-white/20 bg-white px-2 py-0.5 text-[10px] font-extrabold uppercase tracking-wide text-black">
      CPF
    </span>
  );
}

function riskColor(level?: string) {
  switch ((level ?? "").toLowerCase()) {
    case "high":
      return "bg-red-500";
    case "medium":
      return "bg-blue-500";
    case "low":
      return "bg-emerald-500";
    default:
      return "bg-black/30";
  }
}

function riskLabel(level?: string) {
  switch ((level ?? "").toLowerCase()) {
    case "high":
      return "High";
    case "medium":
      return "Medium";
    case "low":
      return "Low";
    default:
      return "Info";
  }
}

function RiskPill({
  level,
  type,
}: {
  level?: string;
  type?: string;
}) {
  return (
    <span className="inline-flex min-w-0 max-w-full items-center gap-1.5 rounded-full border border-black/10 bg-white px-2 py-1 text-[10px] font-medium text-black/65">
      <span
        className={["h-1.5 w-1.5 shrink-0 rounded-full", riskColor(level)].join(
          " "
        )}
      />
      <span className="shrink-0">{riskLabel(level)}</span>
      {type ? (
        <span className="min-w-0 truncate">
          {type.charAt(0).toUpperCase() + type.slice(1)}
        </span>
      ) : null}
    </span>
  );
}

function RiskBlock({ risks }: { risks?: RiskItem[] }) {
  if (!risks || risks.length === 0) return null;

  const visibleRisks = risks.slice(0, 3);

  return (
    <div className="mt-3 rounded-2xl border border-black/10 bg-black/[0.025] px-3 py-2.5">
      <div className="flex items-start gap-2">
        <span className="pt-1 text-[11px] font-semibold text-black/65">
          Risques
        </span>
        <div className="min-w-0 flex-1 space-y-2">
          {visibleRisks.map((r, idx) => (
            <RiskPill
              key={`${r.type ?? "risk"}-${idx}`}
              level={r.level}
              type={r.note ?? r.type}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

/** --- Helpers TikTok + Media --- **/

function isTikTokUrl(url?: string | null) {
  if (!url) return false;
  try {
    const u = new URL(url);
    return u.hostname.includes("tiktok.com");
  } catch {
    return false;
  }
}

function extractTikTokVideoId(url?: string | null) {
  if (!url) return null;
  const m = url.match(/\/video\/(\d+)/);
  return m?.[1] ?? null;
}

function TikTokEmbed({ url }: { url: string }) {
  const videoId = extractTikTokVideoId(url);

  if (!videoId) {
    return (
      <div className="flex h-full w-full items-center justify-center text-xs text-black/60">
        Vidéo TikTok (lien non standard)
      </div>
    );
  }

  const embedUrl = `https://www.tiktok.com/embed/v2/${videoId}`;

  return (
    <iframe
      src={embedUrl}
      className="h-full w-full"
      allow="autoplay; encrypted-media"
      sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
      title="TikTok video"
    />
  );
}

function VideoPlayer({
  src,
  title,
  imageUrl,
  sourceUrl,
}: {
  src: string;
  title: string;
  imageUrl?: string | null;
  sourceUrl?: string | null;
}) {
  const [muted, setMuted] = useState(true);
  const [videoError, setVideoError] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || videoError) return;

    let cancelled = false;

    const syncVideoState = async () => {
      try {
        video.muted = muted;
        video.volume = muted ? 0 : 1;

        const playPromise = video.play();
        if (playPromise && typeof playPromise.then === "function") {
          await playPromise;
        }
      } catch (err: any) {
        if (
          cancelled ||
          err?.name === "AbortError" ||
          err?.message?.includes("media was removed from the document")
        ) {
          return;
        }
        console.error("video play error:", err);
      }
    };

    syncVideoState();

    return () => {
      cancelled = true;
    };
  }, [muted, src, videoError]);

  if (videoError) {
    if (imageUrl) {
      return (
        <div className="relative h-full w-full bg-black">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={imageUrl}
            alt={title}
            className="h-full w-full object-cover"
          />
          {sourceUrl && (
            <a
              href={sourceUrl}
              target="_blank"
              rel="noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="absolute bottom-3 right-3 rounded-2xl bg-black/90 px-3 py-2 text-xs font-extrabold text-white hover:bg-black"
            >
              Ouvrir
            </a>
          )}
        </div>
      );
    }

    return (
      <div className="relative flex h-full w-full items-center justify-center bg-black text-xs text-white/70">
        Vidéo indisponible
        {sourceUrl && (
          <a
            href={sourceUrl}
            target="_blank"
            rel="noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="absolute bottom-3 right-3 rounded-2xl bg-white/90 px-3 py-2 text-xs font-extrabold text-black hover:bg-white"
          >
            Ouvrir
          </a>
        )}
      </div>
    );
  }

  return (
    <div className="relative h-full w-full bg-black">
      <video
        ref={videoRef}
        className="h-full w-full object-cover"
        playsInline
        autoPlay
        loop
        preload="metadata"
        muted={muted}
        controls={false}
        onError={() => {
          console.error("video source unsupported or failed:", src);
          setVideoError(true);
        }}
      >
        <source src={src} type="video/mp4" />
      </video>

      <button
        type="button"
        onClick={async (e) => {
          e.stopPropagation();
          e.preventDefault();

          const video = videoRef.current;
          if (!video) return;

          const nextMuted = !video.muted;

          try {
            video.muted = nextMuted;
            video.volume = nextMuted ? 0 : 1;
            setMuted(nextMuted);

            const playPromise = video.play();
            if (playPromise && typeof playPromise.then === "function") {
              await playPromise;
            }
          } catch (err: any) {
            if (
              err?.name === "AbortError" ||
              err?.message?.includes("media was removed from the document")
            ) {
              return;
            }
            console.error("toggle mute error:", err);
          }
        }}
        className="absolute bottom-3 right-3 z-20 rounded-2xl bg-black/90 px-3 py-2 text-xs font-extrabold text-white hover:bg-black"
        aria-label={muted ? "Démuter" : "Muter"}
        title={muted ? "Démuter" : "Muter"}
      >
        {muted ? "🔇" : "🔊"}
      </button>

      <div className="sr-only">{title}</div>
    </div>
  );
}

function MediaHero({ p }: { p: Product }) {
  if (p.video_storage_url) {
    return (
      <VideoPlayer
        src={p.video_storage_url}
        title={p.title}
        imageUrl={p.image_url}
        sourceUrl={p.source_url}
      />
    );
  }

  if (isTikTokUrl(p.source_url)) {
    return (
      <div className="relative h-full w-full bg-black/5">
        <TikTokEmbed url={p.source_url!} />
        <a
          href={p.source_url!}
          target="_blank"
          rel="noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="absolute bottom-3 right-3 rounded-2xl bg-black/90 px-3 py-2 text-xs font-extrabold text-white hover:bg-black"
        >
          Ouvrir
        </a>
      </div>
    );
  }

  if (p.image_url) {
    // eslint-disable-next-line @next/next/no-img-element
    return (
      <img
        src={p.image_url}
        alt={p.title}
        className="h-full w-full object-cover"
      />
    );
  }

  return <div className="h-full w-full" />;
}

/** --- DB helpers based on run_date --- **/

async function fetchRecentRunDates(limitUniq = 2) {
  const { data, error } = await supabase
    .from("products")
    .select("run_date")
    .eq("is_hidden", false)
    .order("run_date", { ascending: false })
    .limit(300);

  if (error) throw error;

  const uniq: string[] = [];
  for (const row of data ?? []) {
    const d = String((row as { run_date?: string | null }).run_date ?? "");
    if (!d) continue;
    if (!uniq.includes(d)) uniq.push(d);
    if (uniq.length >= limitUniq) break;
  }

  return uniq;
}

async function fetchProductsByRunDate(runDate: string) {
  const { data, error } = await supabase
    .from("products")
    .select(
      "id,run_date,created_at,title,slug,category,score,status,sources,summary,analysis,score_breakdown,image_url,source_url,video_storage_url,is_hidden,mode"
    )
    .eq("run_date", runDate)
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

  const [currentRunDate, setCurrentRunDate] = useState<string>("—");
  const [products, setProducts] = useState<Product[]>([]);

  const [lastRunDate, setLastRunDate] = useState<string>("—");
  const [lastWeekProducts, setLastWeekProducts] = useState<Product[]>([]);

  const [q, setQ] = useState("");
  const [category, setCategory] = useState("all");
  const [source, setSource] = useState("all");
  const [status, setStatus] = useState("all");
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
      .filter((p) =>
        source === "all" ? true : (p.sources ?? []).includes(source)
      )
      .filter((p) => status === "all" ? true : (p.status ?? "Émergent") === status)
      .filter((p) => p.score >= minScore)
      .filter((p) => {
        if (!query) return true;
        const hay = `${p.title} ${p.category}`.toLowerCase();
        return hay.includes(query);
      })
      .sort((a, b) => b.score - a.score);
  }, [products, q, category, source, status, minScore]);

  useEffect(() => {
    let mounted = true;

    const init = async () => {
      try {
        setLoadError(null);

        const { data: sessionData } = await supabase.auth.getSession();
        if (!sessionData.session) {
          router.replace("/login");
          return;
        }
        if (mounted) setEmail(sessionData.session.user.email ?? null);

        const runDates = await fetchRecentRunDates(2);
        const current = runDates[0] ?? "";
        const previous = runDates[1] ?? "";

        if (mounted) {
          setCurrentRunDate(current || "—");
          setLastRunDate(previous || "—");
        }

        if (current) {
          const currentProducts = await fetchProductsByRunDate(current);
          if (mounted) setProducts(currentProducts.slice(0, 60));
        } else if (mounted) {
          setProducts([]);
        }

        if (previous) {
          const previousProducts = await fetchProductsByRunDate(previous);
          if (mounted) setLastWeekProducts(previousProducts.slice(0, 12));
        } else if (mounted) {
          setLastWeekProducts([]);
        }

        if (mounted) setLoading(false);
      } catch (e: any) {
        console.error(e);
        if (mounted) {
          setLoadError(e?.message ?? "Erreur inconnue");
          setLoading(false);
        }
      }
    };

    const { data: sub } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        if (!session) router.replace("/login");
      }
    );

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

      <header className="relative mx-auto w-full max-w-6xl px-6 py-6">
        <div className="relative flex items-start justify-between gap-4">
          <div
            className="flex cursor-pointer items-center gap-3"
            onClick={() => router.push("/")}
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-black/10 bg-black/[0.03]">
              <span className="text-sm font-semibold text-black">CDB</span>
            </div>

            <div className="leading-tight">
              <div className="text-sm font-semibold tracking-tight text-black">
                CDB Produit IA
              </div>
            </div>
          </div>

          <div className="shrink-0">
            <button
              onClick={logout}
              className="hidden rounded-2xl border border-black/10 bg-white/70 px-4 py-2 text-sm font-semibold text-black/80 hover:bg-white sm:inline-flex"
            >
              Déconnexion
            </button>

            <button
              onClick={logout}
              className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-black/10 bg-white/70 text-black/80 hover:bg-white sm:hidden"
              aria-label="Déconnexion"
              title="Déconnexion"
            >
              <LogoutIcon />
            </button>
          </div>
        </div>

        <div className="mt-4 flex w-full flex-col gap-2 sm:flex-row sm:flex-wrap">
          <a
            href="https://www.chemindubusiness.fr/"
            className="inline-flex items-center justify-center gap-2 rounded-2xl bg-black px-4 py-2 text-sm font-semibold text-white hover:bg-black/90"
          >
            <span>Découvrir la formation</span>
            <CPFBadge />
          </a>
          <a
            href="https://cdbvideoia.com/"
            className="inline-flex items-center justify-center rounded-2xl bg-black px-4 py-2 text-sm font-semibold text-white hover:bg-black/90"
          >
            Découvrir CDB Video IA
          </a>
        </div>
      </header>

      <section className="relative mx-auto w-full max-w-6xl px-6 pb-16">
        <div className="rounded-[32px] border border-black/10 bg-white/70 p-6 shadow-sm backdrop-blur">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h1 className="text-2xl font-extrabold tracking-tight">
                Dashboard — Top produits de la semaine
              </h1>
              <p className="mt-1 text-sm text-black/60">
                Mise à jour :{" "}
                <span className="font-semibold text-black/80">
                  {currentRunDate}
                </span>
              </p>
            </div>
            <div className="flex flex-wrap gap-2" />
          </div>

          {loadError && (
            <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
              Erreur Supabase : {loadError}
            </div>
          )}

          <div className="mt-6 grid gap-3 md:grid-cols-4">
            <div className="md:col-span-2">
              <label className="text-xs font-semibold text-black/60">
                Recherche
              </label>
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Ex: brosse, cuisine, fitness…"
                className="mt-1 w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-black/10"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-black/60">
                Catégorie
              </label>
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
              <label className="text-xs font-semibold text-black/60">
                Source
              </label>
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

          <div className="mt-3 flex flex-wrap gap-2">
            {["all", "Émergent", "En tendance", "Populaire", "En regain", "En déclin"].map((s) => {
              const cfg = STATUS_CONFIG[s];
              const active = status === s;
              return (
                <button
                  key={s}
                  type="button"
                  onClick={() => setStatus(s)}
                  className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold transition-all ${
                    active
                      ? cfg ? `${cfg.bg} ${cfg.text} shadow-sm` : "bg-black text-white"
                      : "bg-black/[0.04] text-black/55 hover:bg-black/[0.08]"
                  }`}
                >
                  {cfg && active && <span className={`h-1.5 w-1.5 rounded-full ${cfg.dot}`} />}
                  {s === "all" ? "Tous" : s}
                </button>
              );
            })}
          </div>

          <div className="mt-4 flex items-center gap-3">
            <div className="text-xs font-semibold text-black/60">
              Score min
            </div>
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

          <motion.div
            className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
            initial="hidden"
            animate="visible"
            variants={{ visible: { transition: { staggerChildren: 0.07 } } }}
          >
            <AnimatePresence mode="popLayout">
              {filtered.map((p) => (
                <motion.div
                  key={p.id}
                  layout
                  variants={{
                    hidden: { opacity: 0, y: 24, scale: 0.97 },
                    visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.35, ease: "easeOut" } },
                  }}
                  exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2 } }}
                  whileHover={{ y: -4, transition: { duration: 0.2 } }}
                  className="group overflow-hidden rounded-[32px] border border-black/10 bg-white/80 shadow-sm"
                >
                  <div className="relative aspect-[9/16] w-full bg-black/5">
                    <MediaHero p={p} />

                    <div className="absolute right-3 top-3 rounded-2xl bg-black px-3 py-2 text-xs font-extrabold text-white">
                      {p.score}/100
                    </div>

                    {p.status && (
                      <div className="absolute left-3 top-3">
                        <StatusBadge status={p.status} />
                      </div>
                    )}
                  </div>

                  <div className="p-5">
                    <div className="text-xs font-semibold text-black/50">
                      {p.category}
                    </div>
                    <div className="mt-1 line-clamp-2 text-lg font-extrabold tracking-tight text-black/90">
                      {p.title}
                    </div>

                    <p className="mt-3 line-clamp-2 text-sm text-black/60">
                      {p.summary}
                    </p>

                    <ScoreBreakdown breakdown={p.score_breakdown} />

                    <RiskBlock risks={p.analysis?.risks} />

                    <button
                      type="button"
                      onClick={() => router.push(`/app/product/${p.slug}`)}
                      className="mt-4 inline-flex w-full items-center justify-center rounded-[28px] bg-black px-4 py-4 text-sm font-extrabold text-white hover:bg-black/90 active:scale-[0.98] transition-transform"
                    >
                      Voir l’analyse complète
                    </button>

                    <div className="mt-3 text-xs text-black/45">
                      {(p.sources ?? []).join(" · ")}
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {filtered.length === 0 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="rounded-3xl border border-black/10 bg-white/70 p-6 text-sm text-black/60"
              >
                Aucun produit avec ces filtres.
              </motion.div>
            )}
          </motion.div>

          <div className="mt-10 rounded-[28px] border border-black/10 bg-white/60 p-4 sm:p-5">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
              <div className="min-w-0">
                <div className="text-lg font-extrabold tracking-tight sm:text-xl">
                  Semaine précédente
                </div>
                <div className="text-sm text-black/60">
                  <span className="font-semibold text-black/80">
                    {lastRunDate}
                  </span>
                </div>
              </div>

              <div className="w-full sm:w-auto">
                <Pill>{lastWeekProducts.length} produits</Pill>
              </div>
            </div>

            <div className="mt-4 grid gap-3 md:grid-cols-2">
              {lastWeekProducts.map((p, idx) => (
                <div
                  key={p.id}
                  className="rounded-2xl border border-black/10 bg-white px-3 py-3 hover:bg-white sm:px-4"
                >
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="text-base font-semibold leading-snug text-black/85 sm:text-sm">
                        <span className="mr-1">{idx + 1}.</span>
                        <span className="line-clamp-2 break-words">
                          {p.title}
                        </span>
                      </div>

                      <div className="mt-1 line-clamp-2 break-words text-xs text-black/55">
                        {p.category} • {(p.sources ?? []).join(", ")}
                      </div>
                    </div>

                    <div className="flex w-full items-center gap-2 sm:w-auto sm:shrink-0">
                      <div className="shrink-0 rounded-2xl bg-black px-3 py-1.5 text-xs font-extrabold text-white">
                        {p.score}
                      </div>

                      <button
                        type="button"
                        onClick={() => router.push(`/app/product/${p.slug}`)}
                        className="min-w-0 flex-1 rounded-2xl border border-black/10 bg-white px-3 py-2 text-xs font-extrabold text-black/80 hover:bg-white sm:flex-none"
                      >
                        <span className="block truncate sm:truncate-none">
                          En savoir plus
                        </span>
                      </button>
                    </div>
                  </div>
                </div>
              ))}

              {lastWeekProducts.length === 0 && (
                <div className="rounded-3xl border border-black/10 bg-white/70 p-6 text-sm text-black/60">
                  Aucun produit de la semaine précédente.
                </div>
              )}
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}