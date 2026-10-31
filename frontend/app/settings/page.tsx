"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { api, ApiError, googleLoginUrl } from "@/lib/api";
import type { AISettings, User } from "@/lib/types";

function message(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : "The request could not be completed. Try again.";
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<AISettings | null>(null);
  const [model, setModel] = useState("openrouter/free");
  const [apiKey, setApiKey] = useState("");
  const [signedIn, setSignedIn] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const user = await api<User | null>("/api/auth/status");
        if (!user) {
          setError("Sign in to manage your AI settings.");
          return;
        }
        const saved = await api<AISettings>("/api/settings");
        setSettings(saved);
        setModel(saved.model);
        setSignedIn(true);
      } catch (reason) {
        setError(message(reason));
      }
    }
    void load();
  }, []);

  async function saveSettings(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const body: { model: string; api_key?: string } = { model: model.trim() };
      if (apiKey.trim()) body.api_key = apiKey.trim();
      const saved = await api<AISettings>("/api/settings", {
        method: "PUT",
        body: JSON.stringify(body),
      });
      setSettings(saved);
      setApiKey("");
      setNotice("AI settings saved.");
    } catch (reason) {
      setError(message(reason));
    } finally {
      setBusy(false);
    }
  }

  async function removeKey() {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const saved = await api<AISettings>("/api/settings/api-key", {
        method: "DELETE",
      });
      setSettings(saved);
      setNotice("Saved API key removed.");
    } catch (reason) {
      setError(message(reason));
    } finally {
      setBusy(false);
    }
  }

  async function testConnection() {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await api<{ status: string; model: string }>(
        "/api/settings/test",
        { method: "POST" },
      );
      setNotice(`OpenRouter responded using ${result.model}.`);
    } catch (reason) {
      setError(message(reason));
    } finally {
      setBusy(false);
    }
  }

  const needsLogin = error.toLowerCase().includes("sign in");

  return (
    <main id="main-content" className="mx-auto min-h-screen max-w-3xl px-6 pb-20 pt-24">
      <p className="caption-3 uppercase tracking-[0.12em] text-accent">
        Your account
      </p>
      <h1 className="heading-2 mt-3 text-ink">AI settings</h1>
      <p className="body-3 mt-4 max-w-2xl text-ink/65">
        Choose your OpenRouter model. Your API key is encrypted on the server
        and is never shown here after saving.
      </p>

      {error && (
        <div className="mt-6 rounded-xl border border-red-900/15 bg-red-50 px-4 py-3" role="alert">
          <p className="body-6 text-red-900">{error}</p>
          {needsLogin && (
            <a className="body-5 mt-2 inline-flex text-red-900 underline" href={googleLoginUrl()}>
              Continue with Google Login
            </a>
          )}
        </div>
      )}
      {notice && (
        <p className="mt-6 body-6 text-accent" role="status">{notice}</p>
      )}

      {!signedIn && !error && (
        <div
          aria-label="Checking sign in status"
          className="mt-8 h-40 animate-pulse rounded-xl bg-black/5"
          role="status"
        />
      )}
      {signedIn && (
        <>
          <form
            className="mt-8 space-y-4 rounded-xl border border-black/10 bg-white p-4 sm:p-6"
            onSubmit={saveSettings}
          >
            <div className="space-y-2">
              <label className="body-5 block text-ink" htmlFor="model">
                OpenRouter model
              </label>
              <input
                autoComplete="off"
                className="field-control"
                id="model"
                maxLength={255}
                onChange={(event) => setModel(event.target.value)}
                required
                value={model}
              />
              <p className="caption-2 text-ink/55">
                Use a model identifier from OpenRouter. The default is
                openrouter/free. A failed request never switches models.
              </p>
            </div>
            <div className="space-y-2">
              <label className="body-5 block text-ink" htmlFor="api-key">
                OpenRouter API key
              </label>
              <input
                autoComplete="new-password"
                className="field-control"
                id="api-key"
                minLength={20}
                onChange={(event) => setApiKey(event.target.value)}
                placeholder={
                  settings?.has_api_key
                    ? "A key is saved. Enter a new key to replace it."
                    : "Paste your OpenRouter API key"
                }
                type="password"
                value={apiKey}
              />
              <p className="caption-2 text-ink/55">
                Leave this blank to keep your current key. A personal key is
                required to generate results.
              </p>
            </div>
            <button
              className="button-md rounded-lg bg-ink px-3 py-2 text-white hover:bg-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:cursor-wait disabled:opacity-60"
              disabled={busy}
              type="submit"
            >
              Save settings
            </button>
          </form>

          <div className="mt-4 flex flex-wrap gap-3">
            <button
              className="button-sm rounded-lg border border-black/15 bg-white px-3 py-2 text-ink hover:bg-paper focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent disabled:opacity-60"
              disabled={busy}
              onClick={() => void testConnection()}
              type="button"
            >
              Test OpenRouter connection
            </button>
            {settings?.has_api_key && (
              <button
                className="button-sm rounded-lg border border-black/15 bg-white px-3 py-2 text-ink hover:bg-paper focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent disabled:opacity-60"
                disabled={busy}
                onClick={() => void removeKey()}
                type="button"
              >
                Remove saved key
              </button>
            )}
          </div>
          <Link
            className="body-6 mt-8 inline-flex text-accent underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
            href="/history"
          >
            View execution history
          </Link>
        </>
      )}
    </main>
  );
}
