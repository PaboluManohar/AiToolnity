"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { api, ApiError, googleLoginUrl } from "@/lib/api";
import type { Execution, User } from "@/lib/types";

function message(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : "The request could not be completed. Try again.";
}

export default function HistoryPage() {
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const user = await api<User | null>("/api/auth/status");
        if (!user) {
          setError("Sign in to view your execution history.");
          return;
        }
        setExecutions(await api<Execution[]>("/api/history"));
      } catch (reason) {
        setError(message(reason));
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  return (
    <main id="main-content" className="mx-auto min-h-screen max-w-4xl px-6 pb-20 pt-24">
      <p className="caption-3 uppercase tracking-[0.12em] text-accent">
        Saved work
      </p>
      <h1 className="heading-2 mt-3 text-ink">Execution history</h1>
      <p className="body-3 mt-4 text-ink/65">
        Results created while signed in are saved to your account.
      </p>

      {error && (
        <div className="mt-6 rounded-xl border border-red-900/15 bg-red-50 px-4 py-3" role="alert">
          <p className="body-6 text-red-900">{error}</p>
          {error.toLowerCase().includes("sign in") && (
            <a className="body-5 mt-2 inline-flex text-red-900 underline" href={googleLoginUrl()}>
              Continue with Google Login
            </a>
          )}
        </div>
      )}

      {loading && (
        <div aria-label="Loading history" className="mt-8 space-y-4" role="status">
          {[0, 1, 2].map((item) => (
            <div className="h-40 animate-pulse rounded-xl bg-black/5" key={item} />
          ))}
        </div>
      )}

      {!loading && !error && !executions.length && (
        <section className="mt-8 rounded-xl border border-dashed border-black/20 bg-white p-6">
          <h2 className="title-2 text-ink">Your saved results will appear here</h2>
          <p className="body-6 mt-2 text-ink/65">
            Sign in and generate a result to start your history.
          </p>
          <Link
            className="button-sm mt-4 inline-flex rounded-lg bg-ink px-3 py-2 text-white hover:bg-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
            href="/tools"
          >
            Explore tools
          </Link>
        </section>
      )}

      {!loading && executions.length > 0 && (
        <ol className="mt-8 space-y-4">
          {executions.map((execution) => (
            <li
              className="rounded-xl border border-black/10 bg-white p-4"
              key={execution.id}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <h2 className="title-2 text-ink">{execution.tool_id}</h2>
                <time className="caption-2 text-ink/55" dateTime={execution.created_at}>
                  {new Date(execution.created_at).toLocaleString()}
                </time>
              </div>
              <p className="caption-2 mt-2 text-ink/55">
                {execution.model} · {execution.tone}
              </p>
              <p className="body-6 mt-4 whitespace-pre-wrap text-ink/80">
                {execution.result}
              </p>
            </li>
          ))}
        </ol>
      )}
    </main>
  );
}
