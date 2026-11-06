"use client";

type Signals = {
  google_trends?: { current_value?: number; trend_direction?: string } | null;
  tiktok_shop?: { results_count?: number; total_sales?: number } | null;
  tiktok_discover?: { viral_score?: number; total_views?: number } | null;
  amazon?: { results_count?: number; total_reviews?: number } | null;
};

type Product = {
  id: string; title: string; slug: string; category: string; score: number;
  tags: string[]; sources: string[]; summary: string;
  image_url: string | null; video_storage_url?: string | null;
  score_breakdown?: Record<string, number> | null;
  signals?: Record<string, unknown> | null;
};

function scoreColor(s: number) {
  if (s >= 75) return "from-emerald-400 to-green-500";
  if (s >= 50) return "from-violet-400 to-fuchsia-500";
  return "from-orange-400 to-red-400";
}

function TrendArrow({ dir }: { dir?: string }) {
  if (dir === "rising") return <span className="text-emerald-400">↑</span>;
  if (dir === "declining") return <span className="text-red-400">↓</span>;
  return <span className="text-white/40">→</span>;
}

function MiniBar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = Math.min(100, Math.round((value / max) * 100));
  return (
    <div className="h-1 w-full rounded-full bg-white/10">
      <div className={`h-1 rounded-full ${color}`} style={{ width: `${pct}%` }} />
    </div>
  );
}

export default function ProductCardDemo({ product }: { product: Product }) {
  const sig = (product.signals ?? {}) as Signals;
  const bd = product.score_breakdown ?? {};

  const trendsVal = sig.google_trends?.current_value ?? 0;
  const trendsDir = sig.google_trends?.trend_direction;
  const tshopSales = sig.tiktok_shop?.total_sales ?? 0;
  const tshopCount = sig.tiktok_shop?.results_count ?? 0;
  const viralScore = sig.tiktok_discover?.viral_score ?? 0;
  const amazonScore = bd["amazon"] ?? 0;
  const trendsScore = bd["google_trends"] ?? 0;
  const tshopScore = bd["tiktok_shop"] ?? 0;

  const hasIndicators = trendsVal > 0 || tshopCount > 0 || amazonScore > 0;

  return (
    <div className="group overflow-hidden rounded-2xl border border-white/[0.07] bg-white/[0.03] backdrop-blur transition hover:border-violet-500/30 hover:bg-white/[0.05]">
      {/* Media */}
      <div className="relative h-44 bg-white/[0.03] sm:h-52">
        {product.video_storage_url ? (
          <video
            src={product.video_storage_url}
            className="h-full w-full object-cover"
            autoPlay loop muted playsInline preload="metadata"
          />
        ) : product.image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={product.image_url} alt={product.title} className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-3xl opacity-30">✨</div>
        )}

        {/* Score badge */}
        <div className={`absolute right-3 top-3 rounded-xl bg-gradient-to-r ${scoreColor(product.score)} px-3 py-1.5 text-xs font-black text-white shadow-lg`}>
          {product.score}/100
        </div>

        {/* Category */}
        <div className="absolute bottom-3 left-3 rounded-lg border border-white/10 bg-black/60 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-white/70 backdrop-blur">
          {product.category}
        </div>
      </div>

      {/* Content */}
      <div className="p-5">
        <h3 className="line-clamp-2 text-base font-bold leading-snug text-white">{product.title}</h3>
        <p className="mt-2 line-clamp-2 text-sm leading-relaxed text-white/50">
          {product.summary || "Analyse complète disponible après connexion."}
        </p>

        {/* Indicators */}
        {hasIndicators ? (
          <div className="mt-4 space-y-2.5 rounded-xl border border-white/[0.06] bg-white/[0.03] p-3">
            {/* Google Trends */}
            {trendsVal > 0 && (
              <div>
                <div className="mb-1 flex items-center justify-between text-[10px]">
                  <span className="flex items-center gap-1 font-semibold text-emerald-400">
                    <svg viewBox="0 0 14 14" className="h-3 w-3 fill-current"><path d="M13 1l-5 5-3-3-5 5v2l5-5 3 3 5-5z"/></svg>
                    Google Trends
                  </span>
                  <span className="font-mono text-white/60">
                    {trendsVal}/100 <TrendArrow dir={trendsDir} />
                  </span>
                </div>
                <MiniBar value={trendsScore} max={30} color="bg-emerald-500" />
              </div>
            )}

            {/* TikTok Shop */}
            {tshopCount > 0 && (
              <div>
                <div className="mb-1 flex items-center justify-between text-[10px]">
                  <span className="flex items-center gap-1 font-semibold text-[#69C9D0]">
                    <svg viewBox="0 0 12 12" className="h-3 w-3 fill-current"><path d="M9.8 3.35a2.4 2.4 0 0 1-1.88-2.12V1H6.07v6.83a1.44 1.44 0 0 1-2.88-.44 1.44 1.44 0 0 1 1.44-1.44c.14 0 .27.02.4.05V4.5a3.17 3.17 0 0 0-3.17 3.17 3.17 3.17 0 0 0 6.34 0V3.84a4.1 4.1 0 0 0 2.4.77V2.88a2.42 2.42 0 0 1-.82-.53z"/></svg>
                    TikTok Shop
                  </span>
                  <span className="font-mono text-white/60">
                    {tshopSales > 0 ? `${tshopSales}+ ventes` : "actif"}
                  </span>
                </div>
                <MiniBar value={tshopScore} max={15} color="bg-[#69C9D0]" />
              </div>
            )}

            {/* Amazon */}
            {amazonScore > 0 && (
              <div>
                <div className="mb-1 flex items-center justify-between text-[10px]">
                  <span className="flex items-center gap-1 font-semibold text-[#FF9900]">
                    <svg viewBox="0 0 12 12" className="h-3 w-3 fill-current"><path d="M6 1a5 5 0 1 0 0 10A5 5 0 0 0 6 1zm.5 7.5h-1v-4h1v4zm0-5h-1V2.5h1V3.5z"/></svg>
                    Amazon
                  </span>
                  <span className="font-mono text-white/60">{amazonScore}/35 pts</span>
                </div>
                <MiniBar value={amazonScore} max={35} color="bg-[#FF9900]" />
              </div>
            )}

            {/* Viral score TikTok if available */}
            {viralScore > 0 && (
              <div className="flex items-center justify-between pt-1 text-[10px] border-t border-white/[0.05]">
                <span className="text-white/40">Score viral TikTok</span>
                <span className="font-semibold text-[#EE1D52]">{Math.round(viralScore)}/100</span>
              </div>
            )}
          </div>
        ) : (
          <div className="mt-4 rounded-xl border border-white/[0.06] bg-white/[0.03] p-3 text-center text-[11px] text-white/30">
            Indicateurs disponibles après connexion
          </div>
        )}

        <div className="mt-4 flex flex-col gap-2">
          <a href="/login" className="inline-flex h-11 w-full items-center justify-center rounded-full bg-gradient-to-r from-violet-600 to-orange-500 text-sm font-semibold text-white hover:brightness-110 transition">
            Voir l&apos;analyse complète →
          </a>
          <a href="/login" className="inline-flex h-11 w-full items-center justify-center rounded-full border border-white/15 bg-white/5 text-sm font-semibold text-white/60 hover:bg-white/10 transition">
            Accéder gratuitement
          </a>
        </div>

        <div className="mt-3 text-[11px] text-white/25">
          Sources : {(product.sources ?? []).join(", ")}
        </div>
      </div>
    </div>
  );
}
