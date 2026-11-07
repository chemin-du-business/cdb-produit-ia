"use client";

import React, { useMemo, useState } from "react";
import Link from "next/link";

export default function ContactPage() {
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [form, setForm] = useState({ name: "", email: "", subject: "Support CDB Produit IA", message: "" });

  const mailtoHref = useMemo(() => {
    const subject = encodeURIComponent(`[CDB Produit IA] ${form.subject}`);
    const body = encodeURIComponent(`Nom: ${form.name}\nEmail: ${form.email}\n\nMessage:\n${form.message}`);
    return `mailto:contact@chemindubusiness.fr?subject=${subject}&body=${body}`;
  }, [form]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try { setStatus("sending"); window.location.href = mailtoHref; setStatus("sent"); }
    catch { setStatus("error"); }
  };

  const inputCls = "h-11 w-full rounded-full border border-white/10 bg-white/5 px-4 text-sm text-white placeholder:text-white/30 outline-none focus:border-violet-500/50 transition";
  const textareaCls = "min-h-[140px] w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder:text-white/30 outline-none focus:border-violet-500/50 transition";

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
          <div className="mb-5 flex flex-wrap gap-2">
            {["Support", "Partenariats", "Demandes légales"].map((t) => (
              <span key={t} className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-white/60">{t}</span>
            ))}
          </div>
          <h1 className="text-3xl font-black tracking-tight sm:text-4xl">Contact</h1>
          <p className="mt-3 text-sm leading-relaxed text-white/50">
            Une question sur l'application, un problème d'accès, une demande ou un partenariat ? Écris-nous et on te répond rapidement.
          </p>

          <div className="mt-10 grid gap-5 md:grid-cols-[1fr_0.9fr]">
            {/* Form */}
            <div className="rounded-3xl border border-white/[0.08] bg-white/[0.03] p-6 backdrop-blur sm:p-8">
              <form onSubmit={onSubmit} className="space-y-5">
                <div>
                  <label className="text-sm font-medium text-white/70">Nom</label>
                  <div className="mt-2">
                    <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className={inputCls} placeholder="Ton nom" />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium text-white/70">Email</label>
                  <div className="mt-2">
                    <input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className={inputCls} placeholder="ton@email.com" />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium text-white/70">Sujet</label>
                  <div className="mt-2">
                    <select value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} className={inputCls + " cursor-pointer"}>
                      <option>Support CDB Produit IA</option>
                      <option>Partenariat</option>
                      <option>Demande légale (RGPD)</option>
                      <option>Bug ou problème d'accès</option>
                      <option>Autre</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium text-white/70">Message</label>
                  <div className="mt-2">
                    <textarea required value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} className={textareaCls} placeholder="Explique ta demande..." />
                  </div>
                  <p className="mt-2 text-xs text-white/30">Évite d'envoyer des données sensibles. Si c'est une demande RGPD, indique l'email du compte.</p>
                </div>

                <button type="submit" disabled={status === "sending"} className="inline-flex h-11 w-full items-center justify-center rounded-full bg-gradient-to-r from-violet-600 to-orange-500 text-sm font-semibold text-white hover:brightness-110 disabled:opacity-60 transition">
                  {status === "sending" ? "Envoi..." : "Envoyer"}
                </button>

                {status === "sent" && <p className="text-xs text-emerald-400">Ton client mail va s'ouvrir pour envoyer le message.</p>}
                {status === "error" && <p className="text-xs text-red-400">Une erreur est survenue. Réessaie ou écris-nous directement.</p>}

                <p className="text-xs text-white/30">
                  Ou écris directement :{" "}
                  <a className="font-medium text-white/50 hover:text-white transition" href={mailtoHref}>contact@chemindubusiness.fr</a>
                </p>
              </form>
            </div>

            {/* Info */}
            <div className="rounded-3xl border border-white/[0.08] bg-white/[0.03] p-6 backdrop-blur sm:p-8">
              <div className="text-sm font-semibold text-white/80">Infos utiles</div>
              <div className="mt-4 space-y-3 text-sm">
                <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
                  <div className="text-xs font-semibold text-white/50">Support</div>
                  <div className="mt-1 text-white/60">Réponse généralement sous 24–48h (jours ouvrés).</div>
                </div>
                <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
                  <div className="text-xs font-semibold text-white/50">Demandes RGPD</div>
                  <div className="mt-1 text-white/60">Indique l'email du compte + la demande (accès, suppression, portabilité).</div>
                </div>
              </div>
              <p className="mt-6 text-xs text-white/30">En cas d'urgence technique, joins une capture écran + ton navigateur.</p>
            </div>
          </div>
        </div>
      </main>

      <footer className="relative z-10 border-t border-white/[0.06] px-5 py-8">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <span className="text-sm text-white/30">© {new Date().getFullYear()} CDB Produit IA</span>
          <div className="flex flex-wrap gap-5 text-sm text-white/30">
            <Link className="hover:text-white/60 transition" href="/confidentialite">Confidentialité</Link>
            <Link className="hover:text-white/60 transition" href="/mentions-legales">Mentions légales</Link>
            <Link className="hover:text-white/60 transition" href="/contact">Contact</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
