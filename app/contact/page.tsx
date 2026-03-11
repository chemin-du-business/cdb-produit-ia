// app/contact/page.tsx
"use client";

import React, { useMemo, useState } from "react";

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

function Field({
  label,
  children,
  hint,
}: {
  label: string;
  children: React.ReactNode;
  hint?: string;
}) {
  return (
    <div>
      <label className="text-sm font-medium text-black/80">{label}</label>
      <div className="mt-2">{children}</div>
      {hint ? <div className="mt-2 text-xs text-black/50">{hint}</div> : null}
    </div>
  );
}

export default function ContactPage() {
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">(
    "idle"
  );
  const [form, setForm] = useState({
    name: "",
    email: "",
    subject: "Support CDB Produit IA",
    message: "",
  });

  const mailtoHref = useMemo(() => {
    const subject = encodeURIComponent(`[CDB Produit IA] ${form.subject}`);
    const body = encodeURIComponent(
      `Nom: ${form.name}\nEmail: ${form.email}\n\nMessage:\n${form.message}`
    );
    return `mailto:contact@chemindubusiness.fr?subject=${subject}&body=${body}`;
  }, [form]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setStatus("sending");
      window.location.href = mailtoHref;
      setStatus("sent");
    } catch {
      setStatus("error");
    }
  };

  return (
    <div className="relative min-h-screen bg-white text-black">
      <GlowBg />

      <header className="relative z-10">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6">
          <a href="/" className="flex min-w-0 items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-black/10 bg-black/[0.03]">
              <span className="text-sm font-semibold">CDB</span>
            </div>
            <span className="truncate text-sm font-semibold tracking-tight">
              CDB Produit IA
            </span>
            <span className="hidden sm:inline-flex">
              <Pill>🇫🇷 Développé en France</Pill>
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
          <div className="flex flex-wrap items-center gap-2">
            <Pill>Support</Pill>
            <Pill>Partenariats</Pill>
            <Pill>Demandes légales</Pill>
          </div>

          <h1 className="mt-4 text-3xl font-semibold tracking-tight md:text-4xl">
            Contact 
          </h1>
          <p className="mt-3 text-sm text-black/60">
            Une question sur l’application, un problème d’accès, une demande,
            ou un partenariat ? Écris-nous et on te répond rapidement.
          </p>

          <div className="mt-10 grid gap-6 md:grid-cols-[1fr_0.9fr]">
            <div className="rounded-3xl border border-black/10 bg-white/80 p-6 shadow-[0_30px_90px_-70px_rgba(0,0,0,0.25)] backdrop-blur md:p-8">
              <form onSubmit={onSubmit} className="space-y-5">
                <Field label="Nom">
                  <input
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    className="h-11 w-full rounded-2xl border border-black/10 bg-white px-4 text-sm outline-none focus:border-black/20"
                    placeholder="Ton nom"
                  />
                </Field>

                <Field label="Email">
                  <input
                    required
                    type="email"
                    value={form.email}
                    onChange={(e) =>
                      setForm({ ...form, email: e.target.value })
                    }
                    className="h-11 w-full rounded-2xl border border-black/10 bg-white px-4 text-sm outline-none focus:border-black/20"
                    placeholder="ton@email.com"
                  />
                </Field>

                <Field label="Sujet">
                  <select
                    value={form.subject}
                    onChange={(e) =>
                      setForm({ ...form, subject: e.target.value })
                    }
                    className="h-11 w-full rounded-2xl border border-black/10 bg-white px-4 text-sm outline-none focus:border-black/20"
                  >
                    <option>Support CDB Produit IA</option>
                    <option>Partenariat</option>
                    <option>Demande légale (RGPD)</option>
                    <option>Bug ou problème d’accès</option>
                    <option>Autre</option>
                  </select>
                </Field>

                <Field
                  label="Message"
                  hint="Évite d’envoyer des données sensibles. Si c’est une demande RGPD, indique l’email du compte."
                >
                  <textarea
                    required
                    value={form.message}
                    onChange={(e) =>
                      setForm({ ...form, message: e.target.value })
                    }
                    className="min-h-[140px] w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm outline-none focus:border-black/20"
                    placeholder="Explique ta demande..."
                  />
                </Field>

                <button
                  type="submit"
                  disabled={status === "sending"}
                  className="inline-flex h-12 w-full items-center justify-center rounded-full bg-black px-6 text-sm font-semibold text-white hover:bg-black/90 disabled:opacity-60"
                >
                  {status === "sending" ? "Envoi..." : "Envoyer"}
                </button>

                {status === "sent" ? (
                  <div className="text-xs text-emerald-700">
                    Ton client mail va s’ouvrir pour envoyer le message.
                  </div>
                ) : null}
                {status === "error" ? (
                  <div className="text-xs text-red-700">
                    Une erreur est survenue. Réessaie ou écris-nous directement.
                  </div>
                ) : null}

                <div className="text-xs text-black/45">
                  Ou écris directement :{" "}
                  <a
                    className="font-medium text-black/70 hover:text-black"
                    href={mailtoHref}
                  >
                    contact@chemindubusiness.fr
                  </a>
                </div>
              </form>
            </div>

            <div className="rounded-3xl border border-black/10 bg-white/70 p-6 backdrop-blur md:p-8">
              <div className="text-sm font-semibold">Infos utiles</div>
              <div className="mt-3 space-y-3 text-sm text-black/60">
                <div className="rounded-2xl border border-black/10 bg-white p-4">
                  <div className="text-xs font-semibold text-black/70">Support</div>
                  <div className="mt-1">
                    Réponse généralement sous 24–48h (jours ouvrés).
                  </div>
                </div>

                <div className="rounded-2xl border border-black/10 bg-white p-4">
                  <div className="text-xs font-semibold text-black/70">
                    Demandes RGPD
                  </div>
                  <div className="mt-1">
                    Indique l’email du compte + la demande (accès, suppression,
                    portabilité).
                  </div>
                </div>
              </div>

              <div className="mt-6 text-xs text-black/45">
                En cas d’urgence technique, joins une capture écran + ton navigateur.
              </div>
            </div>
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