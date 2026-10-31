import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import "./globals.css";

import { SiteHeader } from "@/components/site-header";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: "AIToolnity | Every AI Tool. One Place.",
  description:
    "Explore a YAML driven catalogue of AI tools, run them with your preferred OpenRouter model, and keep your results in one place.",
  openGraph: {
    title: "AIToolnity | Every AI Tool. One Place.",
    description:
      "Find a tool for your task, choose a tone, and create a useful result in one place.",
    images: ["/og-image.svg"],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "AIToolnity | Every AI Tool. One Place.",
    description:
      "Find a tool for your task, choose a tone, and create a useful result in one place.",
    images: ["/og-image.svg"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={GeistSans.className}>
      <body className="min-h-screen">
        <a
          className="sr-only z-50 rounded-lg bg-white px-3 py-2 text-ink focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
          href="#main-content"
        >
          Skip to content
        </a>
        <SiteHeader />
        {children}
      </body>
    </html>
  );
}
