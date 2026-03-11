"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { supabase } from "@/lib/supabase/client";
import { useParams, useRouter } from "next/navigation";

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
  image_source: string | null;
  source_url: string | null;
  video_storage_url: string | null;
  analysis: any;
  score_breakdown: any;
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
          "id,title,slug,category,score,tags,sources,summary,image_url,image_source,source_url,video_storage_url,analysis,score_breakdown"
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
  const objections: Array<{ objection: string; response: string }> =
    angles.objections ?? [];
  const ugc = angles.ugc_script ?? null;
  const risks: Array<{ type: string; level: string; note: string }> =
    analysis.risks ?? [];
  const recos = analysis.recommendations ?? {};
  const conf = analysis.confidence ?? {};

  return (
    <main className="min-h-screen bg-[#f6f7fb] text-black">
      <div className="pointer-events-none fixed inset-0">
        <div className="absolute -top-48 left-1/2 h-[420px] w-[820px] -translate-x-1/2 rounded-full bg-gradient-to-r from-indigo-300/30 via-sky-300/30 to-fuchsia-300/30 blur-3xl" />
      </div>

      <header className="relative mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6">
        <Link
          href="/app"
          className="text-sm font-semibold text-black/70 hover:text-black"
        >
          ← Retour dashboard
        </Link>
      </header>

      <section className="relative mx-auto w-full max-w-6xl px-6 pb-16">
        <div className="grid items-start gap-6 lg:grid-cols-2">
          <Box className="self-start">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-xs font-semibold text-black/50">
                  Sources : {(p.sources ?? []).join(", ")}
                </div>
                <h1 className="mt-2 text-2xl font-extrabold tracking-tight">
                  {p.title}
                </h1>
                <p className="mt-3 text-sm text-black/60">{p.summary}</p>

                <div className="mt-4 flex flex-wrap gap-2">
                  <Pill>{p.category}</Pill>
                </div>
              </div>
            </div>

            <div className="mt-6">
              <ProductMedia
                title={p.title}
                imageUrl={p.image_url}
                sourceUrl={p.source_url}
                videoStorageUrl={p.video_storage_url}
                score={p.score}
              />
            </div>
          </Box>

          <div className="space-y-6">
            <Box>
              <SectionTitle>Positionnement</SectionTitle>
              <div className="mt-4 space-y-3 text-sm text-black/70">
                <div>
                  <span className="font-semibold text-black/80">Promesse :</span>{" "}
                  {positioning.main_promise ?? "—"}
                </div>
                <div>
                  <span className="font-semibold text-black/80">Cible :</span>{" "}
                  {positioning.target_customer ?? "—"}
                </div>
                <div>
                  <span className="font-semibold text-black/80">
                    Problème résolu :
                  </span>{" "}
                  {positioning.problem_solved ?? "—"}
                </div>
                <div>
                  <span className="font-semibold text-black/80">
                    Pourquoi maintenant :
                  </span>{" "}
                  {positioning.why_now ?? "—"}
                </div>
              </div>
            </Box>

            <Box>
              <SectionTitle>Angles & hooks</SectionTitle>
              <div className="mt-4 grid gap-3">
                {hooks.length ? (
                  hooks.map((h, i) => (
                    <div
                      key={i}
                      className="rounded-2xl border border-black/10 bg-white p-3 text-sm text-black/70"
                    >
                      <span className="font-semibold text-black/80">
                        Hook {i + 1} :
                      </span>{" "}
                      {h}
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-black/60">—</div>
                )}
              </div>
            </Box>

            <Box>
              <SectionTitle>Objections</SectionTitle>
              <div className="mt-4 space-y-3">
                {objections.length ? (
                  objections.map((o, i) => (
                    <div
                      key={i}
                      className="rounded-2xl border border-black/10 bg-white p-4 text-sm"
                    >
                      <div className="font-semibold text-black/80">
                        Objection
                      </div>
                      <div className="mt-1 text-black/70">{o.objection}</div>
                      <div className="mt-3 font-semibold text-black/80">
                        Réponse
                      </div>
                      <div className="mt-1 text-black/70">{o.response}</div>
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-black/60">—</div>
                )}
              </div>
            </Box>

            <Box>
              <SectionTitle>Risques</SectionTitle>
              <div className="mt-4 space-y-2">
                {risks.length ? (
                  risks.map((r, i) => (
                    <div
                      key={i}
                      className="flex items-start justify-between gap-3 rounded-2xl border border-black/10 bg-white p-3 text-sm"
                    >
                      <div className="text-black/70">
                        <span className="font-semibold text-black/80">
                          {r.type}
                        </span>{" "}
                        — {r.note}
                      </div>
                      <span className="rounded-full bg-black px-3 py-1 text-xs font-semibold text-white">
                        {r.level}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-black/60">—</div>
                )}
              </div>
            </Box>

            <Box>
              <SectionTitle>Recommandations</SectionTitle>
              <div className="mt-4 space-y-2 text-sm text-black/70">
                <div>
                  <span className="font-semibold text-black/80">
                    Prix conseillé :
                  </span>{" "}
                  {recos.price_range?.min ?? "—"} – {recos.price_range?.max ?? "—"}{" "}
                  {recos.price_range?.currency ?? ""}
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
              <SectionTitle>Confiance</SectionTitle>
              <div className="mt-4 text-sm text-black/70">
                <div>
                  <span className="font-semibold text-black/80">Score :</span>{" "}
                  {conf.score ?? "—"}
                </div>
                <div className="mt-2">
                  <span className="font-semibold text-black/80">Raisons :</span>
                  <ul className="mt-2 list-disc pl-5">
                    {(conf.reasons ?? []).map((x: string, i: number) => (
                      <li key={i}>{x}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </Box>

            {ugc?.script ? (
              <Box>
                <SectionTitle>Script UGC (court)</SectionTitle>
                <div className="mt-4 whitespace-pre-line rounded-2xl border border-black/10 bg-white p-4 text-sm text-black/70">
                  {ugc.script}
                </div>
                {ugc.duration_seconds ? (
                  <div className="mt-2 text-xs text-black/50">
                    Durée : ~{ugc.duration_seconds}s
                  </div>
                ) : null}
              </Box>
            ) : null}
          </div>
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-2">
          <div className="rounded-[32px] border border-black/10 bg-white/70 p-6 shadow-sm backdrop-blur">
            <div className="text-sm font-semibold text-black/80">
              🎓 Formation e-commerce
            </div>
            <div className="mt-1 text-sm text-black/60">
              Apprends la méthode complète pour lancer et scaler proprement.
            </div>
            <a
              href="https://calendly.com/contact-chemindubusiness/reservez-votre-rendez-vous-gratuit"
              className="mt-4 inline-flex items-center gap-2 rounded-2xl bg-black px-4 py-2 text-sm font-semibold text-white hover:bg-black/90"
            >
              <span>Voir la formation</span>
              <CPFBadge />
            </a>
          </div>

          <div className="rounded-[32px] border border-black/10 bg-white/70 p-6 shadow-sm backdrop-blur">
            <div className="text-sm font-semibold text-black/80">
              🎬 App CDB Video IA
            </div>
            <div className="mt-1 text-sm text-black/60">
              Crée des vidéos ads vite pour tester tes produits.
            </div>
            <a
              href="https://cdbvideoia.com/"
              className="mt-4 inline-flex rounded-2xl bg-black px-4 py-2 text-sm font-semibold text-white hover:bg-black/90"
            >
              Accéder à CDB Video IA
            </a>
          </div>
        </div>
      </section>
    </main>
  );
}