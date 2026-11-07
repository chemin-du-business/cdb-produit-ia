import React from "react";
import Link from "next/link";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-3xl border border-white/[0.08] bg-white/[0.03] p-6 backdrop-blur sm:p-8">
      <h2 className="text-base font-black tracking-tight text-white">{title}</h2>
      <div className="mt-3 space-y-3 text-sm leading-6 text-white/60">{children}</div>
    </section>
  );
}

export default function MentionsLegalesPage() {
  return (
    <div className="min-h-screen bg-[#06060a] text-white">
      {/* Glows */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
        <div className="absolute -top-40 left-1/2 h-[500px] w-[700px] -translate-x-1/2 rounded-full bg-violet-600/20 blur-[120px]" />
        <div className="absolute bottom-0 right-0 h-[300px] w-[400px] rounded-full bg-orange-500/10 blur-[100px]" />
      </div>

      {/* Nav */}
      <header className="fixed inset-x-0 top-0 z-50 border-b border-white/[0.06] bg-[#06060a]/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-orange-500">
              <span className="text-xs font-black text-white">CDB</span>
            </div>
            <span className="text-sm font-semibold tracking-tight">Produit IA</span>
          </Link>
          <Link href="/" className="inline-flex h-9 items-center rounded-full border border-white/10 bg-white/5 px-4 text-sm font-semibold text-white/70 hover:bg-white/10 transition">
            Retour
          </Link>
        </div>
      </header>

      <main className="relative z-10 mx-auto w-full max-w-6xl px-4 pb-16 pt-28 sm:px-5 sm:pt-36">
        <div className="mx-auto max-w-3xl">
          <h1 className="text-3xl font-black tracking-tight sm:text-4xl">Mentions légales</h1>
          <p className="mt-3 text-sm leading-relaxed text-white/50">
            Conformément aux articles 6-III et 19 de la loi n°2004-575 du 21 juin 2004 pour la Confiance dans l'Économie Numérique (LCEN).
          </p>

          <div className="mt-10 space-y-4">
            <Section title="Éditeur du site">
              <p>Le site <strong className="text-white/80">CDB Produit IA</strong> est édité par :</p>
              <ul className="list-disc space-y-1 pl-5">
                <li>Dénomination sociale : <strong className="text-white/80">LE CONSULTANT IT</strong></li>
                <li>Forme juridique : EURL (entreprise unipersonnelle à responsabilité limitée)</li>
                <li>Capital social : 200,00 €</li>
                <li>Adresse : 15 rue de Magellan, 77700 Serris, France</li>
                <li>SIREN : 932 365 083</li>
                <li>SIRET (siège) : 932 365 083 00017</li>
                <li>RCS : 932 365 083 R.C.S. Meaux</li>
                <li>TVA intracommunautaire : FR60932365083</li>
              </ul>
            </Section>

            <Section title="Responsable de la publication">
              <p>Le responsable de la publication est le représentant légal de la société <strong className="text-white/80">LE CONSULTANT IT</strong>.</p>
            </Section>

            <Section title="Hébergement">
              <p>Le site est hébergé par :</p>
              <ul className="list-disc space-y-1 pl-5">
                <li>Vercel Inc.</li>
                <li>440 N Barranca Ave #4133, Covina, CA 91723, États-Unis</li>
                <li>Site web : <a href="https://vercel.com" target="_blank" rel="noreferrer" className="text-violet-400 hover:text-violet-300 transition">https://vercel.com</a></li>
              </ul>
            </Section>

            <Section title="Propriété intellectuelle">
              <p>L'ensemble du site, de sa structure à ses contenus (textes, images, graphismes, logos, vidéos, icônes, sons, logiciels), est la propriété exclusive de <strong className="text-white/80">LE CONSULTANT IT</strong>, sauf mentions contraires.</p>
              <p>Toute reproduction, représentation, modification, publication, adaptation totale ou partielle du site, quel que soit le moyen ou le procédé utilisé, est interdite sans autorisation écrite préalable.</p>
            </Section>

            <Section title="Responsabilité">
              <p>L'éditeur s'efforce de fournir sur le site des informations aussi précises que possible. Toutefois, il ne pourra être tenu responsable des omissions, inexactitudes ou carences dans la mise à jour.</p>
              <p>L'utilisateur reconnaît utiliser le site sous sa responsabilité exclusive.</p>
            </Section>

            <Section title="Données personnelles">
              <p>Les données personnelles collectées via le site sont traitées conformément à la réglementation en vigueur (RGPD).</p>
              <p>Pour plus d'informations, consulte la page <Link href="/confidentialite" className="text-violet-400 hover:text-violet-300 transition">Politique de confidentialité</Link>.</p>
            </Section>

            <Section title="Droit applicable">
              <p>Les présentes mentions légales sont soumises au droit français. En cas de litige, les tribunaux français seront seuls compétents.</p>
            </Section>
          </div>
        </div>
      </main>

      <footer className="relative z-10 border-t border-white/[0.06] px-5 py-8">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <span className="text-sm text-white/30">© {new Date().getFullYear()} CDB Produit IA — Tous droits réservés</span>
          <div className="flex flex-wrap gap-5 text-sm text-white/30">
            <Link className="hover:text-white/60 transition" href="/mentions-legales">Mentions légales</Link>
            <Link className="hover:text-white/60 transition" href="/confidentialite">Confidentialité</Link>
            <Link className="hover:text-white/60 transition" href="/contact">Contact</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
