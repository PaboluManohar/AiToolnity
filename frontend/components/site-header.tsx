"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { api, ApiError, googleLoginUrl } from "@/lib/api";
import type { User } from "@/lib/types";

export function SiteHeader() {
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [feedback, setFeedback] = useState("");

  useEffect(() => {
    const authError = new URLSearchParams(window.location.search).get("auth_error");
    if (authError === "google_login_cancelled") {
      setFeedback("Google Login was cancelled. Try again when you are ready.");
      window.history.replaceState(null, "", window.location.pathname);
    }
    api<User | null>("/api/auth/status")
      .then(setUser)
      .catch((error: unknown) => {
        setUser(null);
        setFeedback(
          error instanceof ApiError
            ? error.message
            : "Could not check your sign in status.",
        );
      });
  }, []);

  async function signOut() {
    try {
      await api("/api/auth/logout", { method: "POST" });
      setUser(null);
      setFeedback("");
    } catch (error) {
      setFeedback(
        error instanceof Error ? error.message : "Could not sign out. Try again.",
      );
    }
  }

  const links = [
    { href: "/tools", label: "Explore tools" },
    ...(user
      ? [
          { href: "/history", label: "History" },
          { href: "/settings", label: "AI settings" },
        ]
      : []),
  ];

  return (
    <header className="fixed inset-x-0 top-0 z-30 px-4 pt-4 sm:px-6">
      <nav
        aria-label="Main navigation"
        className="mx-auto flex max-w-6xl items-center justify-between rounded-2xl border border-black/10 bg-white/90 px-4 py-3 shadow-sm backdrop-blur-md sm:px-6"
      >
        <Link
          href="/"
          className="title-1 inline-flex items-center gap-2 text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-accent"
        >
          <span
            aria-hidden="true"
            className="flex h-8 w-8 items-center justify-center rounded-lg bg-ink text-sm font-semibold text-white"
          >
            A
          </span>
          AIToolnity
        </Link>

        <div className="hidden items-center gap-6 md:flex">
          {links.map((link) => (
            <Link
              aria-current={pathname === link.href ? "page" : undefined}
              className={`body-6 rounded px-1 py-2 transition-colors duration-300 hover:text-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent ${
                pathname === link.href ? "text-accent" : "text-ink/70"
              }`}
              href={link.href}
              key={link.href}
            >
              {link.label}
            </Link>
          ))}
          {user ? (
            <button
              className="button-sm rounded-lg border border-black/15 px-3 py-2 text-ink transition-colors duration-300 hover:bg-black/5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
              onClick={signOut}
              tabIndex={menuOpen ? -1 : 0}
              type="button"
            >
              Sign out
            </button>
          ) : (
            <a
              className="button-sm rounded-lg border border-black/15 px-3 py-2 text-ink transition-colors duration-300 hover:bg-black/5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
              href={googleLoginUrl()}
              tabIndex={menuOpen ? -1 : 0}
            >
              Google Login
            </a>
          )}
        </div>

        <button
          aria-expanded={menuOpen}
          aria-label={menuOpen ? "Close menu" : "Open menu"}
          className="relative z-50 flex h-10 w-10 flex-col items-center justify-center gap-2 rounded-lg text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent md:hidden"
          onClick={() => setMenuOpen((open) => !open)}
          type="button"
        >
          <span
            className={`h-0.5 w-5 rounded bg-current transition-transform duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] ${
              menuOpen ? "translate-y-1 rotate-45" : ""
            }`}
          />
          <span
            className={`h-0.5 w-5 rounded bg-current transition-transform duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] ${
              menuOpen ? "-translate-y-1 -rotate-45" : ""
            }`}
          />
        </button>
      </nav>
      {feedback && (
        <p
          className="mx-auto mt-2 max-w-6xl rounded-lg border border-red-900/15 bg-red-50 px-4 py-3 body-6 text-red-900"
          role="alert"
        >
          {feedback}
        </p>
      )}

      <div
        aria-hidden={!menuOpen}
        className={`fixed inset-0 z-40 flex min-h-screen flex-col bg-paper/95 px-6 pb-10 pt-24 backdrop-blur-xl transition-opacity duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] md:hidden ${
          menuOpen
            ? "pointer-events-auto opacity-100"
            : "pointer-events-none opacity-0"
        }`}
      >
        <div className="mx-auto flex w-full max-w-sm flex-col gap-3">
          {links.map((link, index) => (
            <Link
              aria-current={pathname === link.href ? "page" : undefined}
              className={`heading-5 rounded-xl px-4 py-4 text-ink transition duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent ${
                menuOpen
                  ? "translate-y-0 opacity-100"
                  : "translate-y-6 opacity-0"
              }`}
              href={link.href}
              key={link.href}
              onClick={() => setMenuOpen(false)}
              tabIndex={menuOpen ? 0 : -1}
              style={{ transitionDelay: menuOpen ? `${index * 60}ms` : "0ms" }}
            >
              {link.label}
            </Link>
          ))}
          {user ? (
            <button
              className="button-md mt-2 rounded-xl bg-ink px-3 py-2 text-white transition-colors duration-300 hover:bg-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
              onClick={() => {
                void signOut();
                setMenuOpen(false);
              }}
              tabIndex={menuOpen ? 0 : -1}
              type="button"
            >
              Sign out
            </button>
          ) : (
            <a
              className="button-md mt-2 rounded-xl bg-ink px-3 py-2 text-center text-white transition-colors duration-300 hover:bg-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
              href={googleLoginUrl()}
              tabIndex={menuOpen ? 0 : -1}
            >
              Google Login
            </a>
          )}
        </div>
      </div>
    </header>
  );
}
