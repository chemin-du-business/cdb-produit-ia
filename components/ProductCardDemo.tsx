"use client";

type RiskItem = { note?: string; type?: string; level?: string };
type Product = {
  id: string; title: string; slug: string; category: string; score: number;
  tags: string[]; sources: string[]; summary: string;
  image_url: string | null; video_storage_url?: string | null;
  analysis?: { risks?: RiskItem[] } | null;
};

function scoreColor(s: number) {
  if (s >= 75) return "from-emerald-400 to-green-500";
  if (s >= 50) return "from-violet-400 to-fuchsia-500";
  return "from-orange-400 to-red-400";
}

function riskColor(level?: string) {
  switch ((level ?? "").toLowerCase()) {
    case "high": return "bg-red-500/20 text-red-300 border-red-500/30";
    case "medium": return "bg-blue-500/20 text-blue-300 border-blue-500/30";
    case "low": return "bg-emerald-500/20 text-emerald-300 border-emerald-500/30";
    default: return "bg-white/10 text-white/50 border-white/10";
  }
}

export default function ProductCardDemo({ product }: { product: Product }) {
  const risks = (product.analysis?.risks ?? []).slice(0, 2);

  return (
    <div className="group overflow-hidden rounded-2xl border border-white/[0.07] bg-white/[0.03] backdrop-blur transition hover:border-violet-500/30 hover:bg-white/[0.05]">
      {/* Media */}
      <div className="relative h-52 bg-white/[0.03] sm:h-56">
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
        <p className="mt-3 line-clamp-2 text-sm leading-relaxed text-white/50">
          {product.summary || "Analyse complète disponible après connexion."}
        </p>

        {/* Risks */}
        {risks.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {risks.map((r, i) => (
              <span key={i} className={`inline-flex items-center gap-1 rounded-lg border px-2 py-1 text-[10px] font-semibold ${riskColor(r.level)}`}>
                <span className="h-1.5 w-1.5 rounded-full bg-current" />
                {r.note ?? r.type ?? "Risque"}
              </span>
            ))}
          </div>
        )}

        <div className="mt-5 flex flex-col gap-2">
          <a href="/login" className="inline-flex w-full items-center justify-center rounded-xl bg-gradient-to-r from-violet-600 to-orange-500 py-2.5 text-sm font-semibold text-white hover:brightness-110 transition">
            Voir l'analyse complète
          </a>
          <a href="/login" className="inline-flex w-full items-center justify-center rounded-xl border border-white/10 bg-white/5 py-2.5 text-sm font-semibold text-white/60 hover:bg-white/10 transition">
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
