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

function Li({ children }: { children: React.ReactNode }) {
  return <li className="ml-5 list-disc">{children}</li>;
}

export default function PrivacyPage() {
  const updatedAt = "19/01/2026";

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
          <div className="mb-4 flex flex-wrap items-center gap-2">
            {["RGPD", "Confidentialité"].map((t) => (
              <span key={t} className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-white/60">{t}</span>
            ))}
            <span className="text-xs text-white/30">Dernière mise à jour : {updatedAt}</span>
          </div>

          <h1 className="text-3xl font-black tracking-tight sm:text-4xl">Politique de confidentialité</h1>
          <p className="mt-3 text-sm leading-relaxed text-white/50">
            Cette politique explique comment <strong className="text-white/80">CDB Produit IA</strong> collecte, utilise et protège vos données personnelles, conformément au Règlement (UE) 2016/679 (RGPD) et à la loi Informatique et Libertés.
          </p>

          <div className="mt-10 space-y-4">
            <Section title="1) Responsable du traitement">
              <p>Le responsable du traitement est : <strong className="text-white/80">LE CONSULTANT IT</strong> (EURL), 15 rue de Magellan, 77700 Serris, France.</p>
              <p>Pour toute question relative à vos données : <Link href="/contact" className="text-violet-400 hover:text-violet-300 transition">page Contact</Link>.</p>
            </Section>

            <Section title="2) Données collectées">
              <p>Selon votre utilisation du service, nous pouvons collecter :</p>
              <ul className="space-y-2">
                <Li><strong className="text-white/80">Données de compte</strong> : identifiant utilisateur, email, nom/prénom (si fourni par Google), photo de profil (si fournie), identifiants techniques de session.</Li>
                <Li><strong className="text-white/80">Données de connexion</strong> : logs techniques (date/heure), adresse IP, informations navigateur/appareil.</Li>
                <Li><strong className="text-white/80">Données liées à l'application</strong> : préférences, filtres, historiques d'usage, produits consultés, données nécessaires à l'affichage du scoring, des analyses et des contenus associés.</Li>
                <Li><strong className="text-white/80">Données d'assistance</strong> : messages envoyés au support, contenus partagés lors d'une demande d'aide.</Li>
              </ul>
              <p className="text-xs text-white/30">Nous ne demandons pas de données "sensibles" (au sens du RGPD). Évitez d'en saisir dans les formulaires ou messages de support.</p>
            </Section>

            <Section title="3) Finalités et bases légales">
              <p>Nous traitons vos données pour :</p>
              <ul className="space-y-2">
                <Li><strong className="text-white/80">Fournir le service</strong> (création de compte, accès à l'application, affichage des produits, analyses) — <strong className="text-white/80">exécution du contrat</strong>.</Li>
                <Li><strong className="text-white/80">Sécuriser la plateforme</strong> (prévention fraude, abus, authentification) — <strong className="text-white/80">intérêt légitime</strong>.</Li>
                <Li><strong className="text-white/80">Support client</strong> (répondre aux demandes) — <strong className="text-white/80">intérêt légitime</strong> ou <strong className="text-white/80">exécution du contrat</strong>.</Li>
                <Li><strong className="text-white/80">Amélioration du produit</strong> (statistiques techniques, performance) — <strong className="text-white/80">intérêt légitime</strong>.</Li>
                <Li><strong className="text-white/80">Obligations légales</strong> (comptabilité, litiges, conservation requise) — <strong className="text-white/80">obligation légale</strong>.</Li>
              </ul>
            </Section>

            <Section title="4) Authentification Google (OAuth)">
              <p>La connexion "Continuer avec Google" utilise l'authentification OAuth. Google peut nous transmettre certaines informations de profil (email, nom, photo) selon vos paramètres Google.</p>
              <p>Nous utilisons ces informations uniquement pour créer et gérer votre compte et vous permettre d'accéder à <strong className="text-white/80">CDB Produit IA</strong>.</p>
            </Section>

            <Section title="5) Sous-traitants et services tiers">
              <p>Pour fournir le service, nous pouvons faire appel à des prestataires, notamment :</p>
              <ul className="space-y-2">
                <Li><strong className="text-white/80">Vercel</strong> (hébergement et déploiement du site).</Li>
                <Li><strong className="text-white/80">Google</strong> (OAuth) si vous choisissez de vous connecter via Google.</Li>
              </ul>
              <p className="text-xs text-white/30">Les prestataires peuvent être situés hors de l'Union Européenne. Dans ce cas, des garanties appropriées peuvent s'appliquer (ex : clauses contractuelles types).</p>
            </Section>

            <Section title="6) Durées de conservation">
              <ul className="space-y-2">
                <Li><strong className="text-white/80">Données de compte</strong> : conservées tant que votre compte est actif, puis supprimées ou anonymisées dans un délai raisonnable, sauf obligation légale.</Li>
                <Li><strong className="text-white/80">Logs et sécurité</strong> : conservés pour une durée limitée liée à la sécurité et au débogage.</Li>
                <Li><strong className="text-white/80">Support</strong> : conservé le temps du traitement puis archivage limité si nécessaire.</Li>
              </ul>
            </Section>

            <Section title="7) Cookies & traceurs">
              <p>Nous utilisons des cookies et stockages locaux strictement nécessaires au fonctionnement du service (sessions, préférences, sécurité).</p>
              <p>Si vous ajoutez ultérieurement des outils d'analyse ou marketing, un bandeau de consentement devra être mis en place et cette page mise à jour.</p>
            </Section>

            <Section title="8) Vos droits (RGPD)">
              <p>Vous disposez des droits suivants : <strong className="text-white/80">accès</strong>, <strong className="text-white/80">rectification</strong>, <strong className="text-white/80">effacement</strong>, <strong className="text-white/80">opposition</strong>, <strong className="text-white/80">limitation</strong>, <strong className="text-white/80">portabilité</strong>.</p>
              <p>Vous pouvez exercer vos droits via la <Link href="/contact" className="text-violet-400 hover:text-violet-300 transition">page Contact</Link> en précisant l'email de votre compte.</p>
              <p>Vous pouvez également introduire une réclamation auprès de la <strong className="text-white/80">CNIL</strong>.</p>
            </Section>

            <Section title="9) Sécurité">
              <p>Nous mettons en œuvre des mesures techniques et organisationnelles raisonnables pour protéger vos données (contrôles d'accès, authentification, surveillance, sécurisation de l'infrastructure).</p>
              <p className="text-xs text-white/30">Aucun système n'étant infaillible, nous ne pouvons garantir une sécurité absolue, mais nous faisons le maximum pour réduire les risques.</p>
            </Section>

            <Section title="10) Modifications">
              <p>Nous pouvons mettre à jour cette politique pour refléter les évolutions du service et/ou des exigences légales. La date de mise à jour est indiquée en haut de la page.</p>
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
