import React from "react";

function GlowBg() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
      <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(0,0,0,0.06)_1px,transparent_1px),linear-gradient(to_bottom,rgba(0,0,0,0.06)_1px,transparent_1px)] bg-[size:64px_64px] opacity-[0.18]" />
      <div className="absolute -top-48 left-1/2 h-[560px] w-[560px] -translate-x-1/2 rounded-full bg-gradient-to-tr from-indigo-500/18 via-violet-500/14 to-fuchsia-500/14 blur-3xl" />
      <div className="absolute -bottom-64 right-[-140px] h-[620px] w-[620px] rounded-full bg-gradient-to-tr from-fuchsia-500/14 via-violet-500/12 to-indigo-500/16 blur-3xl" />
      <div className="absolute inset-0 bg-[radial-gradient(1200px_600px_at_50%_0%,transparent,rgba(255,255,255,0.92))]" />
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-3xl border border-black/10 bg-white/80 p-6 shadow-[0_30px_90px_-70px_rgba(0,0,0,0.25)] backdrop-blur md:p-8">
      <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
      <div className="mt-3 space-y-3 text-sm leading-6 text-black/70">
        {children}
      </div>
    </section>
  );
}

export default function MentionsLegalesPage() {
  return (
    <div className="relative min-h-screen bg-white text-black">
      <GlowBg />

      <header className="relative z-10">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6">
          <a href="/" className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-black/10 bg-black/[0.03]">
              <span className="text-sm font-semibold">CDB</span>
            </div>
            <span className="text-sm font-semibold tracking-tight">
              CDB Produit IA
            </span>
            <span className="inline-flex items-center gap-2 rounded-full border border-black/10 bg-black/[0.03] px-3 py-1 text-xs font-medium text-black/70">
              🇫🇷 Développé en France
            </span>
          </a>

          <a
            href="/"
            className="hidden rounded-full border border-black/10 bg-white/70 px-4 py-2 text-sm font-semibold text-black/80 hover:bg-black/[0.05] md:inline-flex"
          >
            Retour au site
          </a>
        </div>
      </header>

      <main className="relative z-10 mx-auto w-full max-w-6xl px-6 pb-16 pt-6">
        <div className="mx-auto max-w-3xl">
          <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">
            Mentions légales
          </h1>
          <p className="mt-3 text-sm text-black/60">
            Conformément aux articles 6-III et 19 de la loi n°2004-575 du 21 juin
            2004 pour la Confiance dans l’Économie Numérique (LCEN).
          </p>

          <div className="mt-10 space-y-6">
            <Section title="Éditeur du site">
              <p>
                Le site <strong>CDB Produit IA</strong> est édité par :
              </p>
              <ul className="list-disc pl-5">
                <li>
                  Dénomination sociale : <strong>LE CONSULTANT IT</strong>
                </li>
                <li>
                  Forme juridique : EURL (entreprise unipersonnelle à responsabilité limitée)
                </li>
                <li>Capital social : 200,00 €</li>
                <li>Adresse : 15 rue de Magellan, 77700 Serris, France</li>
                <li>SIREN : 932 365 083</li>
                <li>SIRET (siège) : 932 365 083 00017</li>
                <li>RCS : 932 365 083 R.C.S. Meaux</li>
                <li>TVA intracommunautaire : FR60932365083</li>
              </ul>
            </Section>

            <Section title="Responsable de la publication">
              <p>
                Le responsable de la publication est le représentant légal de la
                société <strong>LE CONSULTANT IT</strong>.
              </p>
            </Section>

            <Section title="Hébergement">
              <p>Le site est hébergé par :</p>
              <ul className="list-disc pl-5">
                <li>Vercel Inc.</li>
                <li>440 N Barranca Ave #4133, Covina, CA 91723, États-Unis</li>
                <li>
                  Site web :{" "}
                  <a
                    href="https://vercel.com"
                    target="_blank"
                    rel="noreferrer"
                    className="font-medium text-black/80 hover:text-black"
                  >
                    https://vercel.com
                  </a>
                </li>
              </ul>
            </Section>

            <Section title="Propriété intellectuelle">
              <p>
                L’ensemble du site, de sa structure à ses contenus (textes,
                images, graphismes, logos, vidéos, icônes, sons, logiciels),
                est la propriété exclusive de <strong>LE CONSULTANT IT</strong>,
                sauf mentions contraires.
              </p>
              <p>
                Toute reproduction, représentation, modification, publication,
                adaptation totale ou partielle du site, quel que soit le moyen
                ou le procédé utilisé, est interdite sans autorisation écrite
                préalable.
              </p>
            </Section>

            <Section title="Responsabilité">
              <p>
                L’éditeur s’efforce de fournir sur le site des informations aussi
                précises que possible. Toutefois, il ne pourra être tenu
                responsable des omissions, inexactitudes ou carences dans la
                mise à jour.
              </p>
              <p>
                L’utilisateur reconnaît utiliser le site sous sa responsabilité
                exclusive.
              </p>
            </Section>

            <Section title="Données personnelles">
              <p>
                Les données personnelles collectées via le site sont traitées
                conformément à la réglementation en vigueur (RGPD).
              </p>
              <p>
                Pour plus d’informations sur la collecte et le traitement des
                données personnelles, consulte la page{" "}
                <a
                  href="/privacy"
                  className="font-medium text-black/80 hover:text-black"
                >
                  Politique de confidentialité
                </a>
                .
              </p>
            </Section>

            <Section title="Droit applicable">
              <p>
                Les présentes mentions légales sont soumises au droit français.
                En cas de litige, les tribunaux français seront seuls compétents.
              </p>
            </Section>
          </div>
        </div>
      </main>

      <footer className="relative z-10">
        <div className="mx-auto w-full max-w-6xl px-6 pb-10 text-xs text-black/45">
          <div className="flex flex-col justify-between gap-4 border-t border-black/10 pt-6 sm:flex-row sm:items-center">
            <div>
              © {new Date().getFullYear()} CDB Produit IA — Tous droits réservés
            </div>
            <div className="flex gap-4">
              <a href="/mentions-legales" className="hover:text-black">
                Mentions légales
              </a>
              <a href="/confidentialite" className="hover:text-black">
                Confidentialité
              </a>
              <a href="/contact" className="hover:text-black">
                Contact
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}