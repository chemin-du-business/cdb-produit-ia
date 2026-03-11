import Link from "next/link";
import { createSupabaseServerClient } from "@/lib/supabase/server";

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
  title: string;
  slug: string;
  category: string;
  score: number;
  tags: string[];
  sources: string[];
  summary: string;
  image_url: string | null;
  video_storage_url?: string | null;
  analysis?: ProductAnalysis | null;
};

function cn(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

function Pill({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full border border-black/10 bg-white/70 px-3 py-1 text-xs font-medium text-black/70 backdrop-blur">
      {children}
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

function FeatureCard({
  title,
  desc,
  icon,
}: {
  title: string;
  desc: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="rounded-3xl border border-black/10 bg-white/75 p-5 shadow-sm backdrop-blur transition hover:-translate-y-0.5 hover:bg-white sm:p-6">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-black/5">
          {icon}
        </div>
        <h3 className="text-base font-semibold text-black/90">{title}</h3>
      </div>
      <p className="mt-3 text-sm leading-relaxed text-black/60">{desc}</p>
    </div>
  );
}

function Step({
  n,
  title,
  desc,
}: {
  n: string;
  title: string;
  desc: string;
}) {
  return (
    <div className="rounded-3xl border border-black/10 bg-white/75 p-5 shadow-sm backdrop-blur sm:p-6">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl bg-black text-sm font-bold text-white">
          {n}
        </div>
        <div className="text-base font-semibold text-black/90">{title}</div>
      </div>
      <p className="mt-3 text-sm text-black/60">{desc}</p>
    </div>
  );
}

function DemoMedia({
  product,
  withControls = true,
}: {
  product: Product;
  withControls?: boolean;
}) {
  if (product.video_storage_url) {
    return (
      <video
        src={product.video_storage_url}
        className="h-full w-full object-cover"
        {...(withControls
          ? { controls: true }
          : {
              autoPlay: true,
              loop: true,
              muted: true,
            })}
        playsInline
        preload="metadata"
      />
    );
  }

  if (product.image_url) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={product.image_url}
        alt={product.title}
        className="h-full w-full object-cover"
      />
    );
  }

  return (
    <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-black/[0.03] via-black/[0.05] to-black/[0.08]">
      <div className="text-center">
        <div className="text-3xl">✨</div>
        <div className="mt-2 text-xs font-medium text-black/50">
          Visuel bientôt disponible
        </div>
      </div>
    </div>
  );
}

function HeroMediaCard({
  product,
  large = false,
}: {
  product: Product;
  large?: boolean;
}) {
  return (
    <div className="overflow-hidden rounded-[28px] border border-black/10 bg-white">
      <div
        className={cn(
          "relative bg-black/5",
          large ? "h-[220px] sm:h-[260px]" : "h-[160px] sm:h-[180px]"
        )}
      >
        <DemoMedia product={product} withControls={false} />
        <div className="absolute right-3 top-3 rounded-2xl bg-black px-3 py-2 text-xs font-extrabold text-white">
          {product.score}/100
        </div>
      </div>

      <div className="p-4">
        <div className="text-xs font-semibold uppercase tracking-wide text-black/45">
          {product.category}
        </div>
        <div className="mt-1 line-clamp-1 text-sm font-extrabold tracking-tight text-black/90">
          {product.title}
        </div>
      </div>
    </div>
  );
}

export default async function HomePage() {
  const supabase = createSupabaseServerClient();

  const { data: settingsRows } = await supabase
    .from("settings")
    .select("key,value")
    .in("key", ["current_run_date"]);

  const settings = new Map<string, any>();
  (settingsRows ?? []).forEach((r) => settings.set(r.key, r.value));

  const teaserN = 3;
  const currentRunDate = String(settings.get("current_run_date")?.v ?? "");

  const { data: products } = await supabase
    .from("products")
    .select(
      "id,title,slug,category,score,tags,sources,summary,analysis,image_url,video_storage_url"
    )
    .order("score", { ascending: false })
    .limit(teaserN);

  const weekLabel = currentRunDate
    ? `Semaine du ${currentRunDate}`
    : "Cette semaine";

  const hasProducts = (products ?? []).length > 0;
  const heroProducts = (products ?? []).slice(0, 3);

  return (
    <main className="min-h-screen overflow-x-hidden bg-[#f6f7fb] pt-[76px] text-black sm:pt-[84px]">
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-48 left-1/2 h-[520px] w-[900px] -translate-x-1/2 rounded-full bg-gradient-to-r from-indigo-300/40 via-sky-300/40 to-fuchsia-300/40 blur-3xl" />
        <div className="absolute bottom-0 left-0 h-[320px] w-[520px] rounded-full bg-gradient-to-r from-sky-200/50 to-indigo-200/20 blur-3xl" />
      </div>

      <header className="fixed inset-x-0 top-0 z-[100] w-full border-b border-black/10 bg-white/80 backdrop-blur supports-[backdrop-filter]:bg-white/70">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-3 px-4 py-4 sm:px-6 sm:py-5">
          <Link href="/" className="flex min-w-0 items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-black/10 bg-black/[0.03]">
              <span className="text-sm font-semibold text-black">CDB</span>
            </div>
            <span className="truncate text-sm font-semibold tracking-tight text-black">
              CDB Produit IA
            </span>
          </Link>

          <nav className="flex shrink-0 items-center gap-2 sm:gap-3">
            <Link
              href="/login"
              className="inline-flex items-center justify-center rounded-2xl bg-black px-4 py-2 text-sm font-semibold text-white hover:bg-black/90 sm:hidden"
            >
              Accéder à l’app
            </Link>

            <Link
              href="/login"
              className="hidden rounded-2xl border border-black/10 bg-white/80 px-4 py-2 text-sm font-semibold text-black/80 hover:bg-white sm:inline-flex"
            >
              Se connecter
            </Link>
            <Link
              href="/login"
              className="hidden rounded-2xl bg-black px-4 py-2 text-sm font-semibold text-white hover:bg-black/90 sm:inline-flex"
            >
              Créer un compte gratuit
            </Link>
          </nav>
        </div>
      </header>

      <section className="relative mx-auto w-full max-w-6xl px-4 pt-6 sm:px-6">
        <div className="grid gap-8 lg:grid-cols-2 lg:items-center lg:gap-10">
          <div className="min-w-0">
            <div className="flex flex-wrap gap-2">
              <Pill>🇫🇷 France</Pill>
              <Pill>100% gratuit</Pill>
              <Pill>🤖 IA de détection</Pill>
            </div>

            <h1 className="mt-5 text-3xl font-extrabold leading-[1.02] tracking-tight sm:text-4xl md:text-5xl lg:text-6xl">
              Trouve des <span className="text-black">produits gagnants </span>
              avec l’IA,
              <span className="text-black/60"> lance-toi gratuitement.</span>
            </h1>

            <p className="mt-5 max-w-xl text-sm leading-relaxed text-black/60 sm:text-base md:text-lg">
              CDB Produit IA utilise l’IA pour repérer des produits gagnants,
              les scorer, puis générer une analyse marketing claire pour passer
              plus vite au lancement.
            </p>

            <div className="mt-7 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/login"
                className="inline-flex items-center justify-center rounded-2xl bg-black px-5 py-3 text-sm font-semibold text-white hover:bg-black/90"
              >
                Accéder gratuitement à l’application
              </Link>
              <a
                href="#demo"
                className="inline-flex items-center justify-center rounded-2xl border border-black/10 bg-white/80 px-5 py-3 text-sm font-semibold text-black/80 hover:bg-white"
              >
                Voir la démo
              </a>
            </div>
          </div>

          <div className="min-w-0 rounded-[32px] border border-black/10 bg-white/75 p-4 shadow-sm backdrop-blur sm:p-6">
            {heroProducts.length > 0 ? (
              <div className="grid gap-4 sm:grid-cols-2">
                {heroProducts.map((p, index) => (
                  <div key={p.id} className={cn(index === 0 && "sm:col-span-2")}>
                    <HeroMediaCard product={p} large={index === 0} />
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex min-h-[260px] items-center justify-center rounded-[28px] border border-black/10 bg-white text-center text-sm text-black/50 sm:min-h-[320px]">
                Les vidéos de démonstration apparaîtront ici.
              </div>
            )}
          </div>
        </div>

        <div className="mt-10 grid gap-4 md:grid-cols-3">
          <FeatureCard
            title="Produits gagnants"
            desc="L’IA détecte les meilleures opportunités e-commerce."
            icon={<span className="text-lg">🔎</span>}
          />
          <FeatureCard
            title="Scoring intelligent"
            desc="Chaque produit est évalué selon plusieurs signaux clés."
            icon={<span className="text-lg">🤖</span>}
          />
          <FeatureCard
            title="Analyse prête à vendre"
            desc="Angles marketing, potentiel et base claire pour lancer."
            icon={<span className="text-lg">🚀</span>}
          />
        </div>
      </section>

      <section className="relative mx-auto w-full max-w-6xl px-4 pt-10 sm:px-6">
        <div className="rounded-3xl border border-emerald-200 bg-emerald-50 px-5 py-5 text-sm text-emerald-900 sm:px-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <span className="font-semibold">Application gratuite.</span>{" "}
              Accès complet après connexion.
            </div>
            <Link
              href="/login"
              className="inline-flex items-center justify-center rounded-2xl bg-black px-4 py-2 font-semibold text-white hover:bg-black/90"
            >
              Démarrer gratuitement
            </Link>
          </div>
        </div>
      </section>

      <section className="relative mx-auto w-full max-w-6xl px-4 pt-12 sm:px-6">
        <div className="flex flex-col gap-2">
          <h2 className="text-2xl font-extrabold tracking-tight">
            Comment ça marche
          </h2>
          <p className="text-sm text-black/60">
            Une app IA simple pour détecter, scorer et lancer plus vite.
          </p>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <Step
            n="1"
            title="Détecte"
            desc="L’IA analyse des signaux provenant de contenus, vidéos et tendances pour identifier des produits avec un potentiel e-commerce réel."
          />
          <Step
            n="2"
            title="Score"
            desc="Chaque produit est évalué selon plusieurs critères : potentiel créatif vidéo, attractivité visuelle, signaux sociaux et capacité à performer en publicité."
          />
          <Step
            n="3"
            title="Lance"
            desc="Tu identifies rapidement un produit prêt à tester : angle marketing, compréhension du potentiel et base claire pour créer ta boutique et tes ads."
          />
        </div>
      </section>

      <section
        id="demo"
        className="relative mx-auto w-full max-w-6xl px-4 pb-20 pt-12 sm:px-6"
      >
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h3 className="text-2xl font-extrabold tracking-tight">Démo</h3>
            <p className="mt-1 max-w-xl text-sm text-black/60">
              Un aperçu rapide avant d’accéder gratuitement à l’application
              complète.
            </p>
          </div>

          <Link
            href="/login"
            className="hidden rounded-2xl bg-black px-4 py-2 text-sm font-semibold text-white hover:bg-black/90 sm:inline-flex"
          >
            Se connecter gratuitement
          </Link>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-3">
          {(products ?? []).slice(0, 3).map((p) => (
            <div
              key={p.id}
              className="group overflow-hidden rounded-[32px] border border-black/10 bg-white/75 shadow-sm backdrop-blur transition hover:-translate-y-0.5 hover:bg-white"
            >
              <div className="relative h-52 bg-black/5 sm:h-56">
                <DemoMedia product={p} />

                <div className="absolute right-3 top-3 rounded-2xl bg-black px-3 py-2 text-xs font-extrabold text-white">
                  {p.score}/100
                </div>
              </div>

              <div className="p-5">
                <div className="text-xs font-semibold uppercase tracking-wide text-black/45">
                  {p.category}
                </div>
                <div className="mt-1 line-clamp-2 text-lg font-extrabold tracking-tight text-black/90">
                  {p.title}
                </div>

                <p className="mt-4 line-clamp-3 text-sm text-black/60">
                  {p.summary || "Analyse complète disponible après connexion."}
                </p>

                <RiskBlock risks={p.analysis?.risks} />

                <div className="mt-5 flex flex-col gap-3">
                  <Link
                    href="/login"
                    className="inline-flex w-full items-center justify-center rounded-2xl bg-black px-4 py-2 text-sm font-semibold text-white hover:bg-black/90"
                  >
                    Voir l’analyse complète
                  </Link>

                  <Link
                    href="/login"
                    className="inline-flex w-full items-center justify-center rounded-2xl border border-black/10 bg-white px-4 py-2 text-sm font-semibold text-black/80 hover:bg-black/[0.02]"
                  >
                    Utiliser l’application gratuitement
                  </Link>
                </div>

                <div className="mt-3 text-xs text-black/45">
                  Sources : {(p.sources ?? []).join(", ")}
                </div>
              </div>
            </div>
          ))}
        </div>

        {!hasProducts && (
          <div className="mt-6 rounded-3xl border border-black/10 bg-white p-4 text-sm text-black/60">
            Pas encore de produits publiés. Dès que le premier run hebdo est en
            base, la démo s’affichera ici.
          </div>
        )}

        <div className="mt-12 rounded-[32px] border border-black/10 bg-black p-6 text-white sm:p-8">
          <div className="grid gap-6 md:grid-cols-[1.5fr_1fr] md:items-center">
            <div>
              <div className="text-sm font-semibold text-white/70">
                Passe de la démo à l’application complète
              </div>
              <h4 className="mt-2 text-2xl font-extrabold tracking-tight sm:text-3xl">
                Inscris-toi et commence gratuitement.
              </h4>
              <p className="mt-3 max-w-xl text-sm leading-relaxed text-white/70">
                Plus de produits, plus d’analyses IA, plus de matière pour
                lancer.
              </p>
            </div>
            <div className="flex flex-col gap-3">
              <Link
                href="/login"
                className="inline-flex items-center justify-center rounded-2xl bg-white px-4 py-3 text-sm font-semibold text-black hover:bg-white/90"
              >
                Créer mon compte gratuit
              </Link>
            </div>
          </div>
        </div>

        <footer
          id="footer-links"
          className="mt-14 border-t border-black/10 pt-6 text-sm text-black/55"
        >
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="font-semibold text-black/80">
                © {new Date().getFullYear()} CDB Produit IA
              </div>
              <div className="mt-1 text-xs text-black/45">
                Produits gagnants, scoring IA et analyse marketing.
              </div>
            </div>

            <div className="flex flex-wrap gap-4">
              <Link className="hover:text-black" href="/login">
                Connexion
              </Link>
              <Link className="hover:text-black" href="/confidentialite">
                Confidentialité
              </Link>
              <Link className="hover:text-black" href="/mentions-legales">
                Mentions légales
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