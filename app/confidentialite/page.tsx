// app/privacy/page.tsx
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

function Pill({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-black/10 bg-black/[0.03] px-3 py-1 text-xs font-medium text-black/70">
      {children}
    </span>
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

function Li({ children }: { children: React.ReactNode }) {
  return <li className="ml-5 list-disc">{children}</li>;
}

export default function PrivacyPage() {
  const updatedAt = "19/01/2026";

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
            <Pill>🇫🇷 Développé en France</Pill>
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
          <div className="flex flex-wrap items-center gap-2">
            <Pill>RGPD</Pill>
            <Pill>Confidentialité</Pill>
            <span className="text-xs text-black/50">
              Dernière mise à jour : {updatedAt}
            </span>
          </div>

          <h1 className="mt-4 text-3xl font-semibold tracking-tight md:text-4xl">
            Politique de confidentialité
          </h1>
          <p className="mt-3 text-sm text-black/60">
            Cette politique explique comment <strong>CDB Produit IA</strong>{" "}
            collecte, utilise et protège vos données personnelles, conformément
            au Règlement (UE) 2016/679 (RGPD) et à la loi Informatique et
            Libertés.
          </p>

          <div className="mt-10 space-y-6">
            <Section title="1) Responsable du traitement">
              <p>
                Le responsable du traitement est : <strong>LE CONSULTANT IT</strong>{" "}
                (EURL), 15 rue de Magellan, 77700 Serris, France.
              </p>
              <p>
                Pour toute question relative à vos données :{" "}
                <a
                  href="/contact"
                  className="font-medium text-black/80 hover:text-black"
                >
                  page Contact
                </a>
                .
              </p>
            </Section>

            <Section title="2) Données collectées">
              <p>Selon votre utilisation du service, nous pouvons collecter :</p>
              <ul className="space-y-2">
                <Li>
                  <strong>Données de compte</strong> : identifiant utilisateur,
                  email, nom/prénom (si fourni par Google), photo de profil (si
                  fournie), identifiants techniques de session.
                </Li>
                <Li>
                  <strong>Données de connexion</strong> : logs techniques
                  (date/heure), adresse IP, informations navigateur/appareil
                  (dans la limite nécessaire à la sécurité et au bon
                  fonctionnement).
                </Li>
                <Li>
                  <strong>Données liées à l’application</strong> : préférences,
                  filtres, historiques d’usage, produits consultés, données
                  nécessaires à l’affichage du scoring, des analyses, des
                  recommandations et des contenus associés.
                </Li>
                <Li>
                  <strong>Données d’assistance</strong> : messages envoyés au
                  support, contenus partagés lors d’une demande d’aide.
                </Li>
              </ul>
              <p className="text-xs text-black/50">
                Nous ne demandons pas de données “sensibles” (au sens du RGPD).
                Évitez d’en saisir dans les formulaires ou messages de support.
              </p>
            </Section>

            <Section title="3) Finalités et bases légales">
              <p>Nous traitons vos données pour :</p>
              <ul className="space-y-2">
                <Li>
                  <strong>Fournir le service</strong> (création de compte, accès
                  à l’application, affichage des produits, analyses et
                  fonctionnalités) — <strong>exécution du contrat</strong>.
                </Li>
                <Li>
                  <strong>Sécuriser la plateforme</strong> (prévention fraude,
                  abus, authentification, sécurité des accès) —{" "}
                  <strong>intérêt légitime</strong>.
                </Li>
                <Li>
                  <strong>Support client</strong> (répondre aux demandes) —{" "}
                  <strong>intérêt légitime</strong> ou{" "}
                  <strong>exécution du contrat</strong>.
                </Li>
                <Li>
                  <strong>Amélioration du produit</strong> (statistiques
                  techniques, performance, stabilité) —{" "}
                  <strong>intérêt légitime</strong>.
                </Li>
                <Li>
                  <strong>Obligations légales</strong> (comptabilité, litiges,
                  conservation requise) — <strong>obligation légale</strong>.
                </Li>
              </ul>
            </Section>

            <Section title="4) Authentification Google (OAuth)">
              <p>
                La connexion “Continuer avec Google” utilise l’authentification
                OAuth. Google peut nous transmettre certaines informations de
                profil (par exemple email, nom, photo) selon vos paramètres
                Google.
              </p>
              <p>
                Nous utilisons ces informations uniquement pour créer et gérer
                votre compte et vous permettre d’accéder à{" "}
                <strong>CDB Produit IA</strong>.
              </p>
            </Section>

            <Section title="5) Sous-traitants et services tiers">
              <p>
                Pour fournir le service, nous pouvons faire appel à des
                prestataires (sous-traitants) qui traitent des données pour
                notre compte, notamment :
              </p>
              <ul className="space-y-2">
                <Li>
                  <strong>Vercel</strong> (hébergement et déploiement du site).
                </Li>
                <Li>
                  <strong>Google</strong> (OAuth) si vous choisissez de vous
                  connecter via Google.
                </Li>
              </ul>
              <p className="text-xs text-black/50">
                Les prestataires peuvent être situés hors de l’Union Européenne.
                Dans ce cas, des garanties appropriées peuvent s’appliquer (ex :
                clauses contractuelles types).
              </p>
            </Section>

            <Section title="6) Durées de conservation">
              <ul className="space-y-2">
                <Li>
                  <strong>Données de compte</strong> : conservées tant que votre
                  compte est actif, puis supprimées ou anonymisées dans un délai
                  raisonnable, sauf obligation légale.
                </Li>
                <Li>
                  <strong>Logs et sécurité</strong> : conservés pour une durée
                  limitée liée à la sécurité, au débogage et à la prévention des
                  abus.
                </Li>
                <Li>
                  <strong>Support</strong> : conservé le temps du traitement
                  puis archivage limité si nécessaire.
                </Li>
              </ul>
            </Section>

            <Section title="7) Cookies & traceurs">
              <p>
                Nous utilisons des cookies et stockages locaux strictement
                nécessaires au fonctionnement du service (sessions,
                préférences, sécurité).
              </p>
              <p>
                Si vous ajoutez ultérieurement des outils d’analyse ou marketing
                (ex : pixels, analytics avancés), un bandeau de consentement
                devra être mis en place et cette page devra être mise à jour en
                conséquence.
              </p>
            </Section>

            <Section title="8) Vos droits (RGPD)">
              <p>
                Vous disposez des droits suivants : <strong>accès</strong>,{" "}
                <strong>rectification</strong>, <strong>effacement</strong>,
                <strong> opposition</strong>, <strong>limitation</strong>,
                <strong> portabilité</strong>.
              </p>
              <p>
                Vous pouvez exercer vos droits via la{" "}
                <a
                  href="/contact"
                  className="font-medium text-black/80 hover:text-black"
                >
                  page Contact
                </a>{" "}
                en précisant l’email de votre compte.
              </p>
              <p>
                Vous pouvez également introduire une réclamation auprès de la{" "}
                <strong>CNIL</strong>.
              </p>
            </Section>

            <Section title="9) Sécurité">
              <p>
                Nous mettons en œuvre des mesures techniques et
                organisationnelles raisonnables pour protéger vos données
                (contrôles d’accès, authentification, surveillance, sécurisation
                de l’infrastructure).
              </p>
              <p className="text-xs text-black/50">
                Aucun système n’étant infaillible, nous ne pouvons garantir une
                sécurité absolue, mais nous faisons le maximum pour réduire les
                risques.
              </p>
            </Section>

            <Section title="10) Modifications">
              <p>
                Nous pouvons mettre à jour cette politique pour refléter les
                évolutions du service et/ou des exigences légales. La date de
                mise à jour est indiquée en haut de la page.
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
              <a className="hover:text-black" href="/mentions-legales">
                Mentions légales
              </a>
              <a className="hover:text-black" href="/confidentialite">
                Confidentialité
              </a>
              <a className="hover:text-black" href="/contact">
                Contact
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}