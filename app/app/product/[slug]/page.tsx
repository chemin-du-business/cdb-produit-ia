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
};

const STATUS_CONFIG: Record<string, { bg: string; text: string; dot: string }> = {
  "Émergent":    { bg: "bg-violet-100",  text: "text-violet-700", dot: "bg-violet-500" },
  "En tendance": { bg: "bg-orange-100",  text: "text-orange-700", dot: "bg-orange-500" },
  "Populaire":   { bg: "bg-emerald-100", text: "text-emerald-700", dot: "bg-emerald-500" },
  "En regain":   { bg: "bg-sky-100",     text: "text-sky-700",    dot: "bg-sky-500" },
  "En déclin":   { bg: "bg-red-100",     text: "text-red-600",    dot: "bg-red-500" },
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
  tiktok: 40, amazon: 20, google_trends: 10, google_shopping: 10, meta_ads: 10, tiktok_shop: 10,
};

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-lg font-extrabold tracking-tight text-black/90">
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
        "rounded-[28px] border border-black/10 bg-white/70 p-6 shadow-sm backdrop-blur",
        className,
      ].join(" ")}
    >
      {children}
    </div>
  );
}

function Pill({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full border border-black/10 bg-white/70 px-3 py-1 text-xs font-medium text-black/70">
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
  try {
    const u = new URL(url);
    return u.hostname.includes("tiktok.com");
  } catch {
    return false;
  }
}

function ProductMedia({
  title,
  imageUrl,
  sourceUrl,
  videoStorageUrl,
  score,
}: {
  title: string;
  imageUrl: string | null;
  sourceUrl: string | null;
  videoStorageUrl: string | null;
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

  const tiktokId = extractTikTokVideoId(sourceUrl);

  return (
    <div className="overflow-hidden rounded-[28px] border border-black/10 bg-black/5">
      <div className="relative aspect-[9/16] w-full bg-black">
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
    <main className="min-h-screen bg-[#f6f7fb] text-black">
      <div className="pointer-events-none fixed inset-0">
        <div className="absolute -top-48 left-1/2 h-[420px] w-[820px] -translate-x-1/2 rounded-full bg-gradient-to-r from-indigo-300/30 via-sky-300/30 to-fuchsia-300/30 blur-3xl" />
      </div>

      <header className="relative mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6">
        <button onClick={onBack} className="text-sm font-semibold text-black/70 hover:text-black">
          ← Retour dashboard
        </button>
      </header>

      <section className="relative mx-auto w-full max-w-6xl px-6 pb-16">
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
              <h1 className="mt-3 text-2xl font-extrabold tracking-tight">{p.title}</h1>
              <p className="mt-2 text-sm text-black/60">{p.summary}</p>

              <div className="mt-5">
                <ProductMedia
                  title={p.title}
                  imageUrl={p.image_url}
                  sourceUrl={p.source_url}
                  videoStorageUrl={p.video_storage_url}
                  score={p.score}
                />
              </div>

              <div className="mt-4 text-xs text-black/45">
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
            <div className="flex gap-1 rounded-2xl border border-black/10 bg-white/60 p-1 backdrop-blur">
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
                      className="absolute inset-0 rounded-xl bg-black"
                      transition={{ type: "spring", stiffness: 400, damping: 30 }}
                    />
                  )}
                  <span className={`relative z-10 ${activeTab === tab.id ? "text-white" : "text-black/55"}`}>
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
                      <div className="mt-4 space-y-3 text-sm text-black/70">
                        {[
                          ["Promesse", positioning.main_promise],
                          ["Cible", positioning.target_customer],
                          ["Problème résolu", positioning.problem_solved],
                          ["Pourquoi maintenant", positioning.why_now],
                        ].map(([label, value]) => (
                          <div key={label as string}>
                            <span className="font-semibold text-black/80">{label} :</span>{" "}
                            {value ?? "—"}
                          </div>
                        ))}
                      </div>
                    </Box>

                    <Box>
                      <SectionTitle>Recommandations</SectionTitle>
                      <div className="mt-4 space-y-2 text-sm text-black/70">
                        <div>
                          <span className="font-semibold text-black/80">Prix :</span>{" "}
                          {recos.price_range?.min ?? "—"} – {recos.price_range?.max ?? "—"} {recos.price_range?.currency ?? ""}
                        </div>
                        <div>
                          <span className="font-semibold text-black/80">Canaux :</span>{" "}
                          {(recos.channels ?? []).join(", ") || "—"}
                        </div>
                        <div>
                          <span className="font-semibold text-black/80">Upsells :</span>{" "}
                          {(recos.upsells ?? []).join(", ") || "—"}
                        </div>
                      </div>
                    </Box>

                    <Box>
                      <SectionTitle>Confiance IA</SectionTitle>
                      <div className="mt-4 flex items-center gap-4">
                        <div className="text-3xl font-extrabold">{conf.score ?? "—"}</div>
                        <ul className="mt-1 space-y-1 text-xs text-black/60">
                          {(conf.reasons ?? []).map((x: string, i: number) => (
                            <li key={i} className="flex items-start gap-1.5">
                              <span className="mt-0.5 text-black/30">•</span>{x}
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
                            className="rounded-2xl border border-black/10 bg-white p-3 text-sm text-black/70"
                          >
                            <span className="font-semibold text-black/80">#{i + 1}</span>{" "}{h}
                          </motion.div>
                        )) : <div className="text-sm text-black/60">—</div>}
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
                              className="rounded-2xl border border-black/10 bg-white p-4 text-sm"
                            >
                              <div className="font-semibold text-black/80">Objection</div>
                              <div className="mt-1 text-black/70">{o.objection}</div>
                              <div className="mt-3 font-semibold text-black/80">Réponse</div>
                              <div className="mt-1 text-black/70">{o.response}</div>
                            </motion.div>
                          ))}
                        </div>
                      </Box>
                    )}

                    {ugc?.script && (
                      <Box>
                        <SectionTitle>Script UGC</SectionTitle>
                        <div className="mt-4 whitespace-pre-line rounded-2xl border border-black/10 bg-white p-4 text-sm text-black/70">
                          {ugc.script}
                        </div>
                        {ugc.duration_seconds && (
                          <div className="mt-2 text-xs text-black/50">Durée : ~{ugc.duration_seconds}s</div>
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
                          className="flex items-start justify-between gap-3 rounded-2xl border border-black/10 bg-white p-3 text-sm"
                        >
                          <div className="text-black/70">
                            <RiskLevelBadge level={r.level} />
                            <span className="font-semibold text-black/80">{r.type}</span> — {r.note}
                          </div>
                          <span className="shrink-0 rounded-full bg-black/[0.07] px-2.5 py-1 text-[10px] font-semibold text-black/60">{r.level}</span>
                        </motion.div>
                      )) : <div className="text-sm text-black/60">Aucun risque identifié.</div>}
                    </div>
                  </Box>
                )}

                {activeTab === "scores" && (
                  <Box>
                    <SectionTitle>Score par source</SectionTitle>
                    <div className="mt-2 mb-5 flex items-baseline gap-2">
                      <span className="text-4xl font-extrabold">{p.score}</span>
                      <span className="text-sm text-black/50">/ 100</span>
                      {p.status && statusCfg && (
                        <span className={`ml-2 inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold ${statusCfg.bg} ${statusCfg.text}`}>
                          <span className={`h-1.5 w-1.5 rounded-full ${statusCfg.dot}`} />
                          {p.status}
                        </span>
                      )}
                    </div>
                    {p.score_breakdown ? (
                      <div className="space-y-4">
                        {Object.entries(p.score_breakdown).map(([key, val], i) => {
                          const cfg = SOURCE_COLORS[key] ?? { bar: "bg-black/40", label: key };
                          const max = SOURCE_MAX[key] ?? 20;
                          const pct = Math.min(100, Math.round(((val as number) / max) * 100));
                          return (
                            <motion.div key={key} initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.07 }}>
                              <div className="flex items-center justify-between mb-1.5">
                                <span className="text-sm font-semibold text-black/70">{cfg.label}</span>
                                <span className="text-sm font-extrabold text-black/80">{val as number} <span className="text-xs font-normal text-black/40">/ {max}</span></span>
                              </div>
                              <div className="h-2.5 w-full rounded-full bg-black/[0.07] overflow-hidden">
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
                      <div className="text-sm text-black/60">Score breakdown non disponible (produits V1).</div>
                    )}
                  </Box>
                )}
              </motion.div>
            </AnimatePresence>
          </motion.div>
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-2">
          <div className="rounded-[32px] border border-black/10 bg-white/70 p-6 shadow-sm backdrop-blur">
            <div className="text-sm font-semibold text-black/80">🎓 Formation e-commerce</div>
            <div className="mt-1 text-sm text-black/60">Apprends la méthode complète pour lancer et scaler proprement.</div>
            <a href="https://www.chemindubusiness.fr/" className="mt-4 inline-flex items-center gap-2 rounded-2xl bg-black px-4 py-2 text-sm font-semibold text-white hover:bg-black/90">
              <span>Voir la formation</span>
              <CPFBadge />
            </a>
          </div>
          <div className="rounded-[32px] border border-black/10 bg-white/70 p-6 shadow-sm backdrop-blur">
            <div className="text-sm font-semibold text-black/80">🎬 App CDB Video IA</div>
            <div className="mt-1 text-sm text-black/60">Crée des vidéos ads vite pour tester tes produits.</div>
            <a href="https://cdbvideoia.com/" className="mt-4 inline-flex rounded-2xl bg-black px-4 py-2 text-sm font-semibold text-white hover:bg-black/90">
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
          "id,title,slug,category,score,status,tags,sources,summary,image_url,image_source,source_url,video_storage_url,analysis,score_breakdown"
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
      <div className="min-h-screen bg-[#f6f7fb] p-6">
        <div className="mx-auto max-w-6xl rounded-3xl border border-black/10 bg-white/70 p-6">
          Chargement…
        </div>
      </div>
    );
  }

  if (!p) {
    return (
      <div className="min-h-screen bg-[#f6f7fb] p-6">
        <div className="mx-auto max-w-6xl rounded-3xl border border-black/10 bg-white/70 p-6">
          <p className="text-sm text-black/70">Produit introuvable.</p>
          <Link
            className="mt-4 inline-block rounded-2xl bg-black px-4 py-2 text-sm font-semibold text-white"
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
    { id: "risques",  label: "Risques" },
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