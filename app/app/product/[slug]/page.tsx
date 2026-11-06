"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { supabase } from "@/lib/supabase/client";
import { useParams, useRouter } from "next/navigation";

type Product = {
  id: string;
  title: string;
  slug: string;
  category: string;
  score: number;
  status?: string;
  tags: string[];
  sources: string[];
  summary: string;
  image_url: string | null;
  image_source: string | null;
  source_url: string | null;
  video_storage_url: string | null;
  analysis: any;
  score_breakdown: Record<string, number> | null;
  signals?: Record<string, any> | null;
};

const STATUS_CONFIG: Record<string, { bg: string; text: string; dot: string }> = {
  "Émergent":    { bg: "bg-violet-500/20 border border-violet-500/30",  text: "text-violet-300", dot: "bg-violet-400" },
  "En tendance": { bg: "bg-orange-500/20 border border-orange-500/30",  text: "text-orange-300", dot: "bg-orange-400" },
  "Populaire":   { bg: "bg-emerald-500/20 border border-emerald-500/30", text: "text-emerald-300", dot: "bg-emerald-400" },
  "En regain":   { bg: "bg-sky-500/20 border border-sky-500/30",     text: "text-sky-300",    dot: "bg-sky-400" },
  "En déclin":   { bg: "bg-red-500/20 border border-red-500/30",     text: "text-red-300",    dot: "bg-red-400" },
};

const SOURCE_COLORS: Record<string, { bar: string; label: string }> = {
  tiktok:          { bar: "bg-black",      label: "TikTok" },
  amazon:          { bar: "bg-orange-400", label: "Amazon" },
  google_trends:   { bar: "bg-blue-400",   label: "G. Trends" },
  google_shopping: { bar: "bg-indigo-400", label: "G. Shopping" },
  meta_ads:        { bar: "bg-sky-500",    label: "Meta Ads" },
  tiktok_shop:     { bar: "bg-pink-500",   label: "TikTok Shop" },
};

const SOURCE_MAX: Record<string, number> = {
  amazon: 35, google_trends: 30, google_shopping: 20, tiktok_shop: 15, tiktok: 10, meta_ads: 5,
};

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-lg font-bold tracking-tight text-white/90">
      {children}
    </h2>
  );
}

function Box({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={[
        "rounded-2xl border border-white/[0.07] bg-white/[0.04] p-5 backdrop-blur",
        className,
      ].join(" ")}
    >
      {children}
    </div>
  );
}

function Pill({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-white/60">
      {children}
    </span>
  );
}

function CPFBadge() {
  return (
    <span className="inline-flex items-center rounded-full border border-white/20 bg-white px-2 py-0.5 text-[10px] font-extrabold uppercase tracking-wide text-black">
      CPF
    </span>
  );
}

function extractTikTokVideoId(url?: string | null) {
  if (!url) return null;
  const m = url.match(/\/video\/(\d+)/);
  return m?.[1] ?? null;
}

function isTikTokUrl(url?: string | null) {
  if (!url) return false;
  try { return new URL(url).hostname.includes("tiktok.com"); } catch { return false; }
}

function extractYouTubeVideoId(url?: string | null) {
  if (!url) return null;
  try {
    const u = new URL(url);
    if (u.hostname.includes("youtube.com")) return u.searchParams.get("v");
    if (u.hostname.includes("youtu.be")) return u.pathname.slice(1);
  } catch {}
  return null;
}

function isYouTubeUrl(url?: string | null) {
  if (!url) return false;
  try { const h = new URL(url).hostname; return h.includes("youtube.com") || h.includes("youtu.be"); } catch { return false; }
}

function ProductMedia({
  title,
  imageUrl,
  sourceUrl,
  videoStorageUrl,
  youtubeUrl,
  score,
}: {
  title: string;
  imageUrl: string | null;
  sourceUrl: string | null;
  videoStorageUrl: string | null;
  youtubeUrl?: string | null;
  score: number;
}) {
  const [muted, setMuted] = useState(true);
  const [videoError, setVideoError] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !videoStorageUrl || videoError) return;

    let cancelled = false;

    const playVideo = async () => {
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

    playVideo();

    return () => {
      cancelled = true;
    };
  }, [muted, videoStorageUrl, videoError]);

  // YouTube URL : depuis source_url ou depuis youtubeUrl prop
  const effectiveVideoUrl = isYouTubeUrl(sourceUrl) ? sourceUrl : (youtubeUrl ?? null);
  const tiktokId = extractTikTokVideoId(sourceUrl);
  const youtubeId = extractYouTubeVideoId(effectiveVideoUrl ?? sourceUrl);

  return (
    <div className="overflow-hidden rounded-[28px] border border-white/[0.07] bg-black/5">
      <div className={`relative w-full bg-black ${effectiveVideoUrl && isYouTubeUrl(effectiveVideoUrl) ? "aspect-video" : "aspect-[9/16]"}`}>
        {videoStorageUrl && !videoError ? (
          <video
            ref={videoRef}
            className="h-full w-full object-cover"
            playsInline
            autoPlay
            loop
            muted={muted}
            preload="metadata"
            controls={false}
            poster={imageUrl ?? undefined}
            onError={() => {
              console.error("video source unsupported or failed:", videoStorageUrl);
              setVideoError(true);
            }}
          >
            <source src={videoStorageUrl} type="video/mp4" />
          </video>
        ) : (isYouTubeUrl(effectiveVideoUrl ?? "") || isYouTubeUrl(sourceUrl)) && youtubeId ? (
          <iframe
            src={`https://www.youtube.com/embed/${youtubeId}?rel=0&modestbranding=1`}
            className="h-full w-full"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
            title={title}
          />
        ) : isTikTokUrl(sourceUrl) && tiktokId ? (
          <iframe
            src={`https://www.tiktok.com/embed/v2/${tiktokId}`}
            className="h-full w-full"
            allow="autoplay; encrypted-media"
            sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
            title={title}
          />
        ) : imageUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={imageUrl}
            alt={title}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-sm text-white/70">
            Média indisponible
          </div>
        )}

        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-28 bg-gradient-to-t from-black/55 to-transparent" />

        <div className="absolute right-3 top-3 rounded-2xl bg-black px-3 py-2 text-xs font-extrabold text-white">
          {score}/100
        </div>

        {videoStorageUrl && !videoError ? (
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
            className="absolute bottom-3 right-3 rounded-2xl bg-black/90 px-3 py-2 text-xs font-extrabold text-white hover:bg-black"
            aria-label={muted ? "Activer le son" : "Couper le son"}
            title={muted ? "Activer le son" : "Couper le son"}
          >
            {muted ? "🔇" : "🔊"}
          </button>
        ) : null}

        {sourceUrl ? (
          <a
            href={sourceUrl}
            target="_blank"
            rel="noreferrer"
            className="absolute bottom-3 left-3 rounded-2xl bg-white/90 px-3 py-2 text-xs font-extrabold text-black hover:bg-white"
          >
            Voir la source
          </a>
        ) : null}
      </div>
    </div>
  );
}

function RiskLevelBadge({ level }: { level: string }) {
  const map: Record<string, string> = { high: "bg-red-500", medium: "bg-orange-400", low: "bg-emerald-500" };
  return (
    <span className={`inline-block h-2 w-2 rounded-full mr-1.5 ${map[level?.toLowerCase()] ?? "bg-black/30"}`} />
  );
}

function TrendArrow({ dir }: { dir: string }) {
  if (dir === "up") return <span className="text-emerald-400">↑</span>;
  if (dir === "down") return <span className="text-red-400">↓</span>;
  return <span className="text-white/40">→</span>;
}

function GoogleTrendsCard({ gt }: { gt: Record<string, any> }) {
  const current = gt.current_value ?? 0;
  const peak = gt.peak_value ?? 0;
  const dir = gt.trend_direction ?? "stable";
  const rising = (gt.rising_queries ?? []) as Array<{ query: string } | string>;
  const timeline: Array<{ date: string; value: number }> = gt.timeline ?? [];

  const W = 320, H = 72, PAD_X = 4, PAD_Y = 4;
  const vals = timeline.map((p) => p.value);
  const maxV = Math.max(...vals, 1);
  const points = vals.length >= 2
    ? vals.map((v, i) => {
        const x = PAD_X + (i / (vals.length - 1)) * (W - PAD_X * 2);
        const y = H - PAD_Y - ((v / maxV) * (H - PAD_Y * 2));
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      }).join(" ")
    : null;

  const dirColor = dir === "rising" ? "#34d399" : dir === "declining" ? "#f87171" : "#60a5fa";

  // Labels de dates : premier, milieu, dernier
  const dateLabels: { x: number; label: string }[] = [];
  if (timeline.length >= 2) {
    const fmt = (d: string) => {
      const dt = new Date(d);
      if (isNaN(dt.getTime())) return d.slice(0, 7);
      return dt.toLocaleDateString("fr-FR", { month: "short", year: "2-digit" });
    };
    const indices = [0, Math.floor((timeline.length - 1) / 2), timeline.length - 1];
    indices.forEach((i) => {
      const x = PAD_X + (i / (timeline.length - 1)) * (W - PAD_X * 2);
      dateLabels.push({ x, label: fmt(timeline[i].date) });
    });
  }

  return (
    <Box>
      <div className="flex items-center justify-between mb-3">
        <SectionTitle>Google Trends</SectionTitle>
        <span className="text-sm font-semibold" style={{ color: dirColor }}>
          <TrendArrow dir={dir} /> {current}<span className="text-white/30 text-xs"> / {peak} pic</span>
        </span>
      </div>

      {points ? (
        <div className="rounded-xl overflow-hidden bg-white/[0.03] border border-white/[0.05]">
          <svg viewBox={`0 0 ${W} ${H + 14}`} className="w-full" preserveAspectRatio="none">
            <defs>
              <linearGradient id="tg-fill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={dirColor} stopOpacity="0.25" />
                <stop offset="100%" stopColor={dirColor} stopOpacity="0.0" />
              </linearGradient>
            </defs>
            <polygon
              points={`${PAD_X},${H} ${points} ${W - PAD_X},${H}`}
              fill="url(#tg-fill)"
            />
            <polyline
              points={points}
              fill="none"
              stroke={dirColor}
              strokeWidth="1.8"
              strokeLinejoin="round"
              strokeLinecap="round"
            />
            {dateLabels.map(({ x, label }, i) => (
              <text
                key={i}
                x={x}
                y={H + 11}
                textAnchor={i === 0 ? "start" : i === dateLabels.length - 1 ? "end" : "middle"}
                fontSize="8"
                fill="rgba(255,255,255,0.3)"
                fontFamily="sans-serif"
              >
                {label}
              </text>
            ))}
          </svg>
        </div>
      ) : (
        <div className="h-2 w-full rounded-full bg-white/[0.07] overflow-hidden mb-1">
          <div className="h-full rounded-full bg-blue-400" style={{ width: `${peak > 0 ? Math.round((current / peak) * 100) : 0}%` }} />
        </div>
      )}

      {rising.length > 0 && (
        <div className="mt-3">
          <div className="text-xs text-white/40 mb-1.5">Requêtes en hausse</div>
          <div className="flex flex-wrap gap-1.5">
            {rising.map((q, i) => (
              <span key={i} className="rounded-full border border-blue-400/20 bg-blue-400/10 px-2 py-0.5 text-[11px] text-blue-300">
                {typeof q === "string" ? q : q.query}
              </span>
            ))}
          </div>
        </div>
      )}
    </Box>
  );
}

function AmazonSignalCard({ amz }: { amz: Record<string, any> }) {
  const avgPrice = amz.avg_price ?? amz.average_price;
  const totalReviews = amz.total_reviews ?? amz.reviews_count;
  const isBestseller = amz.has_bestseller ?? amz.has_bestseller_badge ?? false;
  const hasChoice = amz.has_amazon_choice ?? false;
  const topProducts: any[] = amz.top_products ?? [];

  if (!avgPrice && !totalReviews && !isBestseller && topProducts.length === 0) return null;
  const showPrice = avgPrice != null && Number(avgPrice) > 0;
  const showReviews = totalReviews != null && Number(totalReviews) > 0;

  return (
    <Box>
      <div className="flex items-center justify-between mb-3">
        <SectionTitle>Demande Amazon</SectionTitle>
        <div className="flex gap-1.5">
          {isBestseller && <span className="rounded-full border border-orange-400/30 bg-orange-400/10 px-2 py-0.5 text-[11px] font-semibold text-orange-300">#1 Best Seller</span>}
          {hasChoice && !isBestseller && <span className="rounded-full border border-blue-400/30 bg-blue-400/10 px-2 py-0.5 text-[11px] font-semibold text-blue-300">Amazon's Choice</span>}
        </div>
      </div>
      <div className="flex gap-3 text-sm mb-3">
        {showPrice && (
          <div className="flex-1 rounded-xl border border-white/[0.07] bg-white/[0.03] p-3">
            <div className="text-xs text-white/40 mb-0.5">Prix moyen</div>
            <div className="font-bold text-white/90">{avgPrice}€</div>
          </div>
        )}
        {showReviews && (
          <div className="flex-1 rounded-xl border border-white/[0.07] bg-white/[0.03] p-3">
            <div className="text-xs text-white/40 mb-0.5">Avis clients</div>
            <div className="font-bold text-white/90">{Number(totalReviews).toLocaleString("fr-FR")}</div>
          </div>
        )}
      </div>
      {topProducts.length > 0 && (
        <div className="space-y-2">
          <div className="text-xs text-white/40 mb-1">Top produits</div>
          {topProducts.slice(0, 3).map((prod: any, i: number) => (
            <div key={i} className="flex items-center gap-2 text-xs text-white/60">
              <span className="shrink-0 w-5 h-5 flex items-center justify-center rounded-full bg-orange-400/10 text-orange-300 font-bold text-[10px]">{i + 1}</span>
              <span className="line-clamp-1 flex-1">{prod.title ?? "—"}</span>
              {prod.price != null && <span className="shrink-0 text-white/40">{prod.price}€</span>}
            </div>
          ))}
        </div>
      )}
    </Box>
  );
}

function ProductDetailInner({ p, positioning, hooks, objections, ugc, risks, recos, conf, statusCfg, tabs, onBack }: {
  p: Product;
  positioning: any; hooks: string[]; objections: any[]; ugc: any; risks: any[];
  recos: any; conf: any;
  statusCfg: { bg: string; text: string; dot: string } | null;
  tabs: ReadonlyArray<{ id: string; label: string }>;
  onBack: () => void;
}) {
  const [activeTab, setActiveTab] = useState<string>("analyse");

  return (
    <main className="min-h-screen bg-[#06060a] text-white overflow-x-hidden">
      {/* Glows */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
        <div className="absolute -top-40 left-1/2 h-[500px] w-[700px] -translate-x-1/2 rounded-full bg-violet-600/15 blur-[120px]" />
        <div className="absolute top-1/3 -right-40 h-[300px] w-[400px] rounded-full bg-orange-500/8 blur-[100px]" />
        <div className="absolute bottom-0 -left-40 h-[300px] w-[400px] rounded-full bg-indigo-600/10 blur-[100px]" />
      </div>

      <header className="relative z-10 border-b border-white/[0.06] bg-[#06060a]/80 backdrop-blur-xl">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-5 py-4">
          <button onClick={onBack} className="flex items-center gap-2 text-sm font-semibold text-white/50 hover:text-white transition-colors">
            <span>←</span> Retour dashboard
          </button>
        </div>
      </header>

      <section className="relative z-10 mx-auto w-full max-w-6xl px-5 pb-16 pt-6">
        <div className="grid items-start gap-6 lg:grid-cols-[1fr_1.4fr]">

          {/* Left col — media + meta */}
          <motion.div
            initial={{ opacity: 0, x: -24 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="self-start space-y-5"
          >
            <Box>
              <div className="flex flex-wrap items-center gap-2">
                <Pill>{p.category}</Pill>
                {statusCfg && p.status && (
                  <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold ${statusCfg.bg} ${statusCfg.text}`}>
                    <span className={`h-1.5 w-1.5 rounded-full ${statusCfg.dot}`} />
                    {p.status}
                  </span>
                )}
              </div>
              <h1 className="mt-3 text-2xl font-bold tracking-tight text-white">{p.title}</h1>
              <p className="mt-2 text-sm text-white/50">{p.summary}</p>

              <div className="mt-5">
                <ProductMedia
                  title={p.title}
                  imageUrl={p.image_url}
                  sourceUrl={p.source_url}
                  videoStorageUrl={p.video_storage_url}
                  youtubeUrl={p.signals?.youtube_url ?? null}
                  score={p.score}
                />
              </div>

              <div className="mt-4 text-xs text-white/30">
                {(p.sources ?? []).join(" · ")}
              </div>
            </Box>
          </motion.div>

          {/* Right col — tabs */}
          <motion.div
            initial={{ opacity: 0, x: 24 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, ease: "easeOut", delay: 0.1 }}
            className="space-y-4"
          >
            {/* Tab bar */}
            <div className="flex gap-1 rounded-2xl border border-white/[0.07] bg-white/[0.04] p-1 backdrop-blur">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id)}
                  className="relative flex-1 rounded-xl px-3 py-2 text-xs font-semibold transition-colors"
                >
                  {activeTab === tab.id && (
                    <motion.div
                      layoutId="tab-bg"
                      className="absolute inset-0 rounded-xl bg-gradient-to-r from-violet-600 to-orange-500"
                      transition={{ type: "spring", stiffness: 400, damping: 30 }}
                    />
                  )}
                  <span className={`relative z-10 ${activeTab === tab.id ? "text-white" : "text-white/40"}`}>
                    {tab.label}
                  </span>
                </button>
              ))}
            </div>

            {/* Tab content */}
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.25, ease: "easeOut" }}
                className="space-y-4"
              >
                {activeTab === "analyse" && (
                  <>
                    <Box>
                      <SectionTitle>Positionnement</SectionTitle>
                      <div className="mt-3 space-y-2 text-sm text-white/60">
                        {[
                          ["Promesse", positioning.main_promise],
                          ["Cible", positioning.target_customer],
                          ["Problème résolu", positioning.problem_solved],
                          ["Pourquoi maintenant", positioning.why_now],
                        ].map(([label, value]) => (
                          <div key={label as string}>
                            <span className="font-semibold text-white/80">{label} :</span>{" "}
                            {value ?? "—"}
                          </div>
                        ))}
                      </div>
                    </Box>

                    <Box>
                      <SectionTitle>Recommandations</SectionTitle>
                      <div className="mt-3 space-y-2 text-sm text-white/60">
                        <div>
                          <span className="font-semibold text-white/80">Prix :</span>{" "}
                          {recos.price_range?.min ?? "—"} – {recos.price_range?.max ?? "—"} {recos.price_range?.currency ?? ""}
                        </div>
                        <div>
                          <span className="font-semibold text-white/80">Canaux :</span>{" "}
                          {(recos.channels ?? []).join(", ") || "—"}
                        </div>
                        <div>
                          <span className="font-semibold text-white/80">Upsells :</span>{" "}
                          {(recos.upsells ?? []).join(", ") || "—"}
                        </div>
                      </div>
                    </Box>

                    {p.signals?.amazon && Object.keys(p.signals.amazon).length > 0 && (
                      <AmazonSignalCard amz={p.signals.amazon} />
                    )}

                    <Box>
                      <SectionTitle>Confiance IA</SectionTitle>
                      <div className="mt-3 flex items-center gap-4">
                        <div className="text-3xl font-extrabold">{conf.score ?? "—"}</div>
                        <ul className="space-y-1 text-xs text-white/50">
                          {(conf.reasons ?? []).map((x: string, i: number) => (
                            <li key={i} className="flex items-start gap-1.5">
                              <span className="mt-0.5 text-white/20">•</span>{x}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </Box>
                  </>
                )}

                {activeTab === "hooks" && (
                  <>
                    <Box>
                      <SectionTitle>Hooks</SectionTitle>
                      <div className="mt-4 grid gap-3">
                        {hooks.length ? hooks.map((h, i) => (
                          <motion.div
                            key={i}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: i * 0.06 }}
                            className="rounded-2xl border border-white/[0.07] bg-white/[0.04] p-3 text-sm text-white/60"
                          >
                            <span className="font-semibold text-white/80">#{i + 1}</span>{" "}{h}
                          </motion.div>
                        )) : <div className="text-sm text-white/50">—</div>}
                      </div>
                    </Box>

                    {objections.length > 0 && (
                      <Box>
                        <SectionTitle>Objections</SectionTitle>
                        <div className="mt-4 space-y-3">
                          {objections.map((o, i) => (
                            <motion.div
                              key={i}
                              initial={{ opacity: 0, x: -10 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: i * 0.06 }}
                              className="rounded-2xl border border-white/[0.07] bg-white/[0.04] p-4 text-sm"
                            >
                              <div className="font-semibold text-white/80">Objection</div>
                              <div className="mt-1 text-white/60">{o.objection}</div>
                              <div className="mt-3 font-semibold text-white/80">Réponse</div>
                              <div className="mt-1 text-white/60">{o.response}</div>
                            </motion.div>
                          ))}
                        </div>
                      </Box>
                    )}

                    {ugc?.script && (
                      <Box>
                        <SectionTitle>Script UGC</SectionTitle>
                        <div className="mt-4 whitespace-pre-line rounded-2xl border border-white/[0.07] bg-white/[0.04] p-4 text-sm text-white/60">
                          {ugc.script}
                        </div>
                        {ugc.duration_seconds && (
                          <div className="mt-2 text-xs text-white/40">Durée : ~{ugc.duration_seconds}s</div>
                        )}
                      </Box>
                    )}
                  </>
                )}

                {activeTab === "risques" && (
                  <Box>
                    <SectionTitle>Risques identifiés</SectionTitle>
                    <div className="mt-4 space-y-2">
                      {risks.length ? risks.map((r, i) => (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0, y: 8 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: i * 0.07 }}
                          className="flex items-start justify-between gap-3 rounded-2xl border border-white/[0.07] bg-white/[0.04] p-3 text-sm"
                        >
                          <div className="text-white/60">
                            <RiskLevelBadge level={r.level} />
                            <span className="font-semibold text-white/80">{r.type}</span> — {r.note}
                          </div>
                          <span className="shrink-0 rounded-full bg-white/[0.07] px-2.5 py-1 text-[10px] font-semibold text-white/50">{r.level}</span>
                        </motion.div>
                      )) : <div className="text-sm text-white/50">Aucun risque identifié.</div>}
                    </div>
                  </Box>
                )}

                {activeTab === "scores" && (
                  <>
                  <Box>
                    <SectionTitle>Score par source</SectionTitle>
                    <div className="mt-2 mb-5 flex items-baseline gap-2">
                      <span className="text-4xl font-extrabold">{p.score}</span>
                      <span className="text-sm text-white/40">/ 100</span>
                      {p.status && statusCfg && (
                        <span className={`ml-2 inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold ${statusCfg.bg} ${statusCfg.text}`}>
                          <span className={`h-1.5 w-1.5 rounded-full ${statusCfg.dot}`} />
                          {p.status}
                        </span>
                      )}
                    </div>
                    {p.score_breakdown ? (
                      <div className="space-y-4">
                        {Object.entries(p.score_breakdown).filter(([k, v]) => ["tiktok","amazon","google_trends","google_shopping","meta_ads","tiktok_shop"].includes(k) && (v as number) > 0).map(([key, val], i) => {
                          const cfg = SOURCE_COLORS[key] ?? { bar: "bg-black/40", label: key };
                          const max = SOURCE_MAX[key] ?? 20;
                          const pct = Math.min(100, Math.round(((val as number) / max) * 100));
                          return (
                            <motion.div key={key} initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.07 }}>
                              <div className="flex items-center justify-between mb-1.5">
                                <span className="text-sm font-semibold text-white/60">{cfg.label}</span>
                                <span className="text-sm font-extrabold text-white/80">{val as number} <span className="text-xs font-normal text-white/30">/ {max}</span></span>
                              </div>
                              <div className="h-2.5 w-full rounded-full bg-white/[0.07] overflow-hidden">
                                <motion.div
                                  className={`h-full rounded-full ${cfg.bar}`}
                                  initial={{ width: 0 }}
                                  animate={{ width: `${pct}%` }}
                                  transition={{ duration: 0.7, ease: "easeOut", delay: i * 0.07 }}
                                />
                              </div>
                            </motion.div>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="text-sm text-white/50">Score breakdown non disponible (produits V1).</div>
                    )}
                  </Box>
                  {p.signals?.google_trends && (p.signals.google_trends.current_value > 0 || p.signals.google_trends.peak_value > 0) && (
                    <GoogleTrendsCard gt={p.signals.google_trends} />
                  )}
                  </>
                )}
              </motion.div>
            </AnimatePresence>
          </motion.div>
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl border border-white/[0.07] bg-white/[0.04] p-5 backdrop-blur">
            <div className="text-sm font-semibold text-white/80">🎓 Formation e-commerce</div>
            <div className="mt-1 text-sm text-white/50">Apprends la méthode complète pour lancer et scaler proprement.</div>
            <a href="https://www.chemindubusiness.fr/" className="mt-4 inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-orange-500 px-4 py-2 text-sm font-semibold text-white hover:opacity-90">
              <span>Voir la formation</span>
              <CPFBadge />
            </a>
          </div>
          <div className="rounded-2xl border border-white/[0.07] bg-white/[0.04] p-5 backdrop-blur">
            <div className="text-sm font-semibold text-white/80">🎬 App CDB Video IA</div>
            <div className="mt-1 text-sm text-white/50">Crée des vidéos ads vite pour tester tes produits.</div>
            <a href="https://cdbvideoia.com/" className="mt-4 inline-flex rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-white/70 hover:bg-white/10">
              Accéder à CDB Video IA
            </a>
          </div>
        </div>
      </section>
    </main>
  );
}

export default function ProductPage() {
  const params = useParams<{ slug: string }>();
  const slug = params.slug;
  const router = useRouter();

  const [loading, setLoading] = useState(true);
  const [p, setP] = useState<Product | null>(null);

  useEffect(() => {
    let mounted = true;

    const init = async () => {
      const { data: sessionData } = await supabase.auth.getSession();
      if (!sessionData.session) {
        router.replace("/login");
        return;
      }

      const { data, error } = await supabase
        .from("products")
        .select(
          "id,title,slug,category,score,status,tags,sources,summary,image_url,image_source,source_url,video_storage_url,analysis,score_breakdown,signals"
        )
        .eq("slug", slug)
        .single();

      if (error) {
        console.error(error);
        if (mounted) setP(null);
      } else if (mounted) {
        setP(data as Product);
      }

      if (mounted) setLoading(false);
    };

    init();
    return () => {
      mounted = false;
    };
  }, [router, slug]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#06060a] flex items-center justify-center">
        <div className="text-white/40 text-sm animate-pulse">Chargement…</div>
      </div>
    );
  }

  if (!p) {
    return (
      <div className="min-h-screen bg-[#06060a] flex items-center justify-center p-6">
        <div className="rounded-2xl border border-white/[0.07] bg-white/[0.04] p-6 text-center">
          <p className="text-sm text-white/60">Produit introuvable.</p>
          <Link
            className="mt-4 inline-block rounded-xl bg-gradient-to-r from-violet-600 to-orange-500 px-4 py-2 text-sm font-semibold text-white"
            href="/app"
          >
            Retour dashboard
          </Link>
        </div>
      </div>
    );
  }

  const analysis = p.analysis ?? {};
  const positioning = analysis.positioning ?? {};
  const angles = analysis.angles ?? {};
  const hooks: string[] = angles.hooks ?? [];
  const objections: Array<{ objection: string; response: string }> = angles.objections ?? [];
  const ugc = angles.ugc_script ?? null;
  const risks: Array<{ type: string; level: string; note: string }> = analysis.risks ?? [];
  const recos = analysis.recommendations ?? {};
  const conf = analysis.confidence ?? {};
  const statusCfg = STATUS_CONFIG[p.status ?? ""] ?? null;

  const TABS = [
    { id: "analyse",  label: "Analyse" },
    { id: "hooks",    label: "Hooks & UGC" },
    { id: "scores",   label: "Scores" },
  ] as const;

  return (
    <ProductDetailInner
      p={p}
      positioning={positioning}
      hooks={hooks}
      objections={objections}
      ugc={ugc}
      risks={risks}
      recos={recos}
      conf={conf}
      statusCfg={statusCfg}
      tabs={TABS}
      onBack={() => router.push("/app")}
    />
  );
}