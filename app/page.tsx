import Link from "next/link";
import { createSupabaseServerClient } from "@/lib/supabase/server";

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
    <div className="rounded-3xl border border-black/10 bg-white/70 p-6 shadow-sm backdrop-blur">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-black/5">
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
    <div className="rounded-3xl border border-black/10 bg-white/70 p-6 shadow-sm backdrop-blur">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-black text-sm font-bold text-white">
          {n}
        </div>
        <div className="text-base font-semibold text-black/90">{title}</div>
      </div>
      <p className="mt-3 text-sm text-black/60">{desc}</p>
    </div>
  );
}

export default async function HomePage() {
  const supabase = createSupabaseServerClient();

  // settings
  const { data: settingsRows } = await supabase
    .from("settings")
    .select("key,value")
    .in("key", ["teaserN", "current_run_date"]);

  const settings = new Map<string, any>();
  (settingsRows ?? []).forEach((r) => settings.set(r.key, r.value));

  const teaserN = Number(settings.get("teaserN")?.v ?? 5);
  const currentRunDate = String(settings.get("current_run_date")?.v ?? "");

  // teaser products (public RLS => current run + published + not hidden)
  const { data: products } = await supabase
    .from("products")
    .select("id,title,slug,category,score,tags,sources,summary,image_url")
    .order("score", { ascending: false })
    .limit(teaserN);

  const weekLabel = currentRunDate
    ? `Semaine du ${currentRunDate}`
    : "Cette semaine";

  const hasProducts = (products ?? []).length > 0;

  return (
    <main className="min-h-screen bg-[#f6f7fb] text-black">
      {/* Background */}
      <div className="pointer-events-none fixed inset-0">
        <div className="absolute -top-48 left-1/2 h-[520px] w-[900px] -translate-x-1/2 rounded-full bg-gradient-to-r from-indigo-300/40 via-sky-300/40 to-fuchsia-300/40 blur-3xl" />
        <div className="absolute bottom-0 left-0 h-[320px] w-[520px] rounded-full bg-gradient-to-r from-sky-200/50 to-indigo-200/20 blur-3xl" />
      </div>

      {/* Navbar */}
      <header className="relative mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6">
        <Link href="/" className="flex items-center gap-3">
          <div className="h-11 w-11 rounded-2xl bg-black shadow-sm" />
          <div className="leading-tight">
            <div className="text-xs font-semibold tracking-wide text-black/60">
              CDB
            </div>
            <div className="text-lg font-extrabold tracking-tight">
              Produit IA
            </div>
          </div>
        </Link>

        <nav className="flex items-center gap-3">
          <Link
            href="/login"
            className="rounded-2xl bg-black px-4 py-2 text-sm font-semibold text-white hover:bg-black/90"
          >
            Se connecter
          </Link>
          <Link
            href="/login"
            className="hidden rounded-2xl border border-black/10 bg-white/70 px-4 py-2 text-sm font-semibold text-black/80 hover:bg-white sm:inline-flex"
          >
            Démarrer gratuitement
          </Link>
        </nav>
      </header>

      {/* Hero */}
      <section className="relative mx-auto w-full max-w-6xl px-6 pt-6">
        <div className="grid gap-10 lg:grid-cols-2 lg:items-center">
          <div>
            <div className="flex flex-wrap gap-2">
              <Pill>🇫🇷 France</Pill>
              <Pill>🔁 Sélection hebdo</Pill>
              <Pill>🤖 Analyse IA</Pill>
              <Pill>📌 Pinterest → 🎵 TikTok</Pill>
            </div>

            <h1 className="mt-5 text-4xl font-extrabold leading-[1.05] tracking-tight md:text-5xl">
              Trouve des{" "}
              <span className="text-black">produits gagnants</span>{" "}
              <br className="hidden md:block" />
              <span className="text-black/60">en 3 étapes.</span>
            </h1>

            <p className="mt-4 max-w-xl text-base leading-relaxed text-black/60">
              Chaque semaine, CDB Produit IA sélectionne des produits
              prometteurs à partir de signaux (Google Trends, Pinterest, TikTok)
              puis génère un angle marketing prêt à l’emploi.
            </p>

            <div className="mt-7 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/login"
                className="inline-flex items-center justify-center rounded-2xl bg-black px-5 py-3 text-sm font-semibold text-white hover:bg-black/90"
              >
                Accéder gratuitement
              </Link>
              <a
                href="#teaser"
                className="inline-flex items-center justify-center rounded-2xl border border-black/10 bg-white/70 px-5 py-3 text-sm font-semibold text-black/80 hover:bg-white"
              >
                Voir le teaser
              </a>
            </div>

            <div className="mt-6 flex flex-wrap items-center gap-3 text-sm text-black/55">
              <span className="font-semibold text-black/70">
                {weekLabel}
              </span>
              <span className="text-black/20">•</span>
              <span>Teaser public</span>
              <span className="text-black/20">•</span>
              <span>Analyse complète après connexion</span>
            </div>
          </div>

          {/* Hero right card */}
          <div className="rounded-[32px] border border-black/10 bg-white/70 p-6 shadow-sm backdrop-blur">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-sm font-semibold text-black/70">
                  {weekLabel}
                </div>
                <div className="mt-1 text-xl font-extrabold tracking-tight">
                  Top produits (aperçu)
                </div>
              </div>
              <div className="rounded-2xl bg-black px-3 py-2 text-xs font-bold text-white">
                Score /100
              </div>
            </div>

            <div className="mt-6 space-y-3">
              {(products ?? []).slice(0, 3).map((p) => (
                <div
                  key={p.id}
                  className="flex items-center gap-3 rounded-3xl border border-black/10 bg-white p-3"
                >
                  <div className="h-12 w-12 overflow-hidden rounded-2xl bg-black/5">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    {p.image_url ? (
                      <img
                        src={p.image_url}
                        alt={p.title}
                        className="h-full w-full object-cover"
                      />
                    ) : null}
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-semibold text-black/90">
                      {p.title}
                    </div>
                    <div className="mt-1 flex flex-wrap gap-2 text-xs text-black/50">
                      <span>{p.category}</span>
                      <span className="text-black/20">•</span>
                      <span>{(p.sources ?? []).join(", ")}</span>
                    </div>
                  </div>

                  <div className="rounded-2xl bg-black px-3 py-2 text-sm font-extrabold text-white">
                    {p.score}
                  </div>
                </div>
              ))}

              {!hasProducts && (
                <div className="rounded-3xl border border-black/10 bg-white p-4 text-sm text-black/60">
                  Pas encore de produits publiés. Dès que le premier run hebdo
                  est en base, le teaser s’affichera ici.
                </div>
              )}
            </div>

            <div className="mt-6 rounded-3xl border border-black/10 bg-black p-5 text-white">
              <div className="text-sm font-semibold">Débloque l’analyse complète</div>
              <div className="mt-1 text-sm text-white/70">
                Angles, hooks, objections, risques et recommandations.
              </div>
              <Link
                href="/login"
                className="mt-4 inline-flex w-full items-center justify-center rounded-2xl bg-white px-4 py-2 text-sm font-semibold text-black hover:bg-white/90"
              >
                Se connecter
              </Link>
            </div>
          </div>
        </div>

        {/* Feature cards under hero */}
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          <FeatureCard
            title="Découverte multi-sources"
            desc="Google Trends + Pinterest + TikTok. On recoupe les signaux pour éviter les faux buzz."
            icon={<span className="text-lg">🧭</span>}
          />
          <FeatureCard
            title="Angle marketing prêt"
            desc="Promesse, hooks, objections + réponses. Direct exploitable pour tes ads et ta page produit."
            icon={<span className="text-lg">✨</span>}
          />
          <FeatureCard
            title="Images produit"
            desc="Priorité Pinterest, sinon thumbnail TikTok, sinon fallback. Pour une interface crédible."
            icon={<span className="text-lg">🖼️</span>}
          />
        </div>
      </section>

      {/* Social proof strip */}
      <section className="relative mx-auto w-full max-w-6xl px-6 pt-10">
        <div className="rounded-3xl border border-black/10 bg-white/60 px-6 py-4 text-sm text-black/60 backdrop-blur">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <span className="font-semibold text-black/80">
                Approuvé par des e-commerçants
              </span>{" "}
              • sélection hebdo • accès gratuit
            </div>
            <div className="flex gap-2">
              <Pill>Shopify</Pill>
              <Pill>TikTok Ads</Pill>
              <Pill>Pinterest</Pill>
              <Pill>Google Trends</Pill>
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="relative mx-auto w-full max-w-6xl px-6 pt-12">
        <div className="flex flex-col gap-2">
          <h2 className="text-2xl font-extrabold tracking-tight">
            Comment ça marche
          </h2>
          <p className="text-sm text-black/60">
            Le pipeline tourne 1 fois par semaine (GitHub Actions) et alimente la base.
          </p>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <Step
            n="1"
            title="Collecte des signaux"
            desc="On récupère tendances & inspirations (FR) depuis nos 3 sources."
          />
          <Step
            n="2"
            title="Scoring /100"
            desc="On déduplique, on score, on garde un Top N limité et diversifié."
          />
          <Step
            n="3"
            title="Analyse IA"
            desc="On génère un angle prêt à l’emploi + risques + recommandations."
          />
        </div>
      </section>

      {/* Teaser grid */}
      <section id="teaser" className="relative mx-auto w-full max-w-6xl px-6 pb-20 pt-12">
        <div className="flex items-end justify-between gap-4">
          <div>
            <h3 className="text-2xl font-extrabold tracking-tight">
              Teaser gratuit
            </h3>
            <p className="mt-1 text-sm text-black/60">
              {teaserN} produits visibles sans compte — connecte-toi pour voir le Top complet.
            </p>
          </div>

          <Link
            href="/login"
            className="hidden rounded-2xl bg-black px-4 py-2 text-sm font-semibold text-white hover:bg-black/90 sm:inline-flex"
          >
            Débloquer l’accès complet
          </Link>
        </div>

        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {(products ?? []).map((p) => (
            <div
              key={p.id}
              className="group overflow-hidden rounded-[32px] border border-black/10 bg-white/70 shadow-sm backdrop-blur hover:bg-white"
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
                <div className="text-xs font-semibold text-black/50">
                  {p.category}
                </div>
                <div className="mt-1 line-clamp-2 text-lg font-extrabold tracking-tight text-black/90">
                  {p.title}
                </div>

                <div className="mt-3 flex flex-wrap gap-2">
                  {(p.tags ?? []).slice(0, 3).map((t) => (
                    <span
                      key={t}
                      className="rounded-full border border-black/10 bg-black/5 px-3 py-1 text-xs font-medium text-black/70"
                    >
                      {t}
                    </span>
                  ))}
                </div>

                <p className="mt-4 line-clamp-2 text-sm text-black/60">
                  {p.summary || "Analyse complète disponible après connexion."}
                </p>

                <div className="mt-5">
                  <Link
                    href="/login"
                    className="inline-flex w-full items-center justify-center rounded-2xl bg-black px-4 py-2 text-sm font-semibold text-white hover:bg-black/90"
                  >
                    Voir l’analyse complète
                  </Link>
                </div>

                <div className="mt-3 text-xs text-black/45">
                  Sources : {(p.sources ?? []).join(", ")}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Bottom CTAs (Formation + Yart) */}
        <div className="mt-12 grid gap-4 md:grid-cols-2">
          <div className="rounded-[32px] border border-black/10 bg-white/70 p-6 shadow-sm backdrop-blur">
            <div className="text-sm font-semibold text-black/80">🎓 Formation e-commerce</div>
            <div className="mt-1 text-sm text-black/60">
              Méthode complète : produit → offer → créas → lancement → scaling.
            </div>
            <a
              href="#"
              className="mt-4 inline-flex rounded-2xl bg-black px-4 py-2 text-sm font-semibold text-white hover:bg-black/90"
            >
              Découvrir la formation
            </a>
          </div>

          <div className="rounded-[32px] border border-black/10 bg-white/70 p-6 shadow-sm backdrop-blur">
            <div className="text-sm font-semibold text-black/80">🎬 App vidéo (Yart)</div>
            <div className="mt-1 text-sm text-black/60">
              Génère vite des vidéos UGC/Ads pour tester tes produits.
            </div>
            <a
              href="#"
              className="mt-4 inline-flex rounded-2xl bg-black px-4 py-2 text-sm font-semibold text-white hover:bg-black/90"
            >
              Accéder à Yart
            </a>
          </div>
        </div>

        <footer className="mt-14 border-t border-black/10 pt-6 text-sm text-black/50">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>© {new Date().getFullYear()} CDB Produit IA</div>
            <div className="flex gap-4">
              <Link className="hover:text-black" href="/login">Connexion</Link>
              <a className="hover:text-black" href="#">Formation</a>
              <a className="hover:text-black" href="#">Yart</a>
            </div>
          </div>
        </footer>
      </section>
    </main>
  );
}