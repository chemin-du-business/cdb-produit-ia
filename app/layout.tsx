import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://www.cdbproduitia.com"),
  title: {
    default: "CDB Produit IA | Produits gagnants e-commerce détectés par IA",
    template: "%s | CDB Produit IA",
  },
  description:
    "CDB Produit IA détecte des produits gagnants e-commerce grâce à l’intelligence artificielle, analyse leur potentiel, leur scoring et leurs angles marketing pour lancer plus vite.",
  applicationName: "CDB Produit IA",
  keywords: [
    "produit gagnant",
    "produits gagnants",
    "produit gagnant ecommerce",
    "produit gagnant dropshipping",
    "ia ecommerce",
    "outil ecommerce",
    "scoring produit",
    "analyse marketing produit",
    "détection produit gagnant",
    "e-commerce IA",
    "produits tendance",
    "produit viral",
    "dashboard produit ia",
    "recherche produit ecommerce",
    "cdb produit ia",
  ],
  authors: [{ name: "CDB Produit IA" }],
  creator: "CDB Produit IA",
  publisher: "CDB Produit IA",
  category: "business",
  classification: "E-commerce, IA, Marketing",
  referrer: "origin-when-cross-origin",
  robots: {
    index: true,
    follow: true,
    nocache: false,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  alternates: {
    canonical: "/",
    languages: {
      "fr-FR": "/",
    },
  },
  openGraph: {
    type: "website",
    locale: "fr_FR",
    url: "https://www.cdbproduitia.com",
    siteName: "CDB Produit IA",
    title: "CDB Produit IA | Produits gagnants e-commerce détectés par IA",
    description:
      "Détecte des produits gagnants avec l’IA, analyse leur score, leur potentiel marketing et trouve plus vite quoi lancer en e-commerce.",
    images: [
      {
        url: "/og-image.jpg",
        width: 1200,
        height: 630,
        alt: "CDB Produit IA - Produits gagnants e-commerce détectés par IA",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "CDB Produit IA | Produits gagnants e-commerce détectés par IA",
    description:
      "Détecte des produits gagnants avec l’IA et accède à leur scoring, leur analyse marketing et leur potentiel e-commerce.",
    images: ["/og-image.jpg"],
    creator: "@cdbproduitia",
  },
  icons: {
    icon: "/favicon.ico",
    shortcut: "/favicon.ico",
    apple: "/apple-touch-icon.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}