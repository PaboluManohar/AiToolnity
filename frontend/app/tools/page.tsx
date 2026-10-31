"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";

import { api, ApiError, googleLoginUrl } from "@/lib/api";
import type {
  CatalogueItem,
  CatalogueNode,
  Execution,
  InputField,
  Tool,
} from "@/lib/types";

function FieldControl({
  field,
  value,
  onChange,
}: {
  field: InputField;
  value: string;
  onChange: (value: string) => void;
}) {
  const common = {
    className: "field-control",
    id: field.name,
    name: field.name,
    placeholder: field.placeholder ?? undefined,
    required: field.required,
    value,
    onChange: (
      event: React.ChangeEvent<
        HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
      >,
    ) => onChange(event.target.value),
  };

  if (field.type === "textarea") {
    return <textarea {...common} className="field-control min-h-32 resize-y" />;
  }
  if (field.type === "select") {
    return (
      <select {...common}>
        <option value="">Choose an option</option>
        {field.options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    );
  }
  return (
    <input
      {...common}
      maxLength={field.max_length ?? undefined}
      min={field.type === "number" ? (field.min_value ?? undefined) : undefined}
      max={field.type === "number" ? (field.max_value ?? undefined) : undefined}
      minLength={field.min_length ?? undefined}
      type={field.type}
    />
  );
}

function errorMessage(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : "The request could not be completed. Try again.";
}

export default function ToolsPage() {
  const [categories, setCategories] = useState<CatalogueNode[]>([]);
  const [subcategories, setSubcategories] = useState<CatalogueNode[]>([]);
  const [items, setItems] = useState<CatalogueItem[]>([]);
  const [category, setCategory] = useState<CatalogueNode | null>(null);
  const [subcategory, setSubcategory] = useState<CatalogueNode | null>(null);
  const [tool, setTool] = useState<Tool | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [tone, setTone] = useState("");
  const [execution, setExecution] = useState<Execution | null>(null);
  const [refinement, setRefinement] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const workingRef = useRef(false);

  useEffect(() => {
    api<CatalogueNode[]>("/api/catalogue/categories")
      .then(setCategories)
      .catch((reason: unknown) => setError(errorMessage(reason)))
      .finally(() => setLoading(false));
  }, []);

  async function selectCategory(nextCategory: CatalogueNode) {
    setCategory(nextCategory);
    setSubcategory(null);
    setSubcategories([]);
    setItems([]);
    setTool(null);
    setExecution(null);
    setError("");
    setLoading(true);
    try {
      setSubcategories(
        await api<CatalogueNode[]>(
          `/api/catalogue/categories/${encodeURIComponent(nextCategory.id)}/subcategories`,
        ),
      );
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      setLoading(false);
    }
  }

  async function selectSubcategory(nextSubcategory: CatalogueNode) {
    if (!category) return;
    setSubcategory(nextSubcategory);
    setItems([]);
    setTool(null);
    setExecution(null);
    setError("");
    setLoading(true);
    try {
      setItems(
        await api<CatalogueItem[]>(
          `/api/catalogue/categories/${encodeURIComponent(category.id)}/subcategories/${encodeURIComponent(nextSubcategory.id)}/items`,
        ),
      );
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      setLoading(false);
    }
  }

  async function selectTool(toolId: string) {
    setError("");
    setNotice("");
    setExecution(null);
    setLoading(true);
    try {
      const selectedTool = await api<Tool>(
        `/api/catalogue/tools/${encodeURIComponent(toolId)}`,
      );
      setTool(selectedTool);
      setValues({});
      setTone(selectedTool.tones[0]?.id ?? "");
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      setLoading(false);
    }
  }

  function goToCategories() {
    setCategory(null);
    setSubcategory(null);
    setSubcategories([]);
    setItems([]);
    setTool(null);
    setExecution(null);
    setError("");
  }

  function goToSubcategories() {
    setSubcategory(null);
    setItems([]);
    setTool(null);
    setExecution(null);
    setError("");
  }

  async function submitTool(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tool || workingRef.current) return;
    setError("");
    setNotice("");
    const inputs: Record<string, string | number> = {};
    for (const field of tool.input_schema.fields) {
      const value = values[field.name] ?? "";
      if (field.required && !value.trim()) {
        setError(`${field.label} is required.`);
        return;
      }
      if (value !== "") {
        inputs[field.name] =
          field.type === "number" ? Number(value) : value;
      }
    }
    workingRef.current = true;
    setWorking(true);
    try {
      const saved = await api<Execution>("/api/executions", {
        method: "POST",
        headers: { "Idempotency-Key": crypto.randomUUID() },
        body: JSON.stringify({ tool_id: tool.id, inputs, tone }),
      });
      setExecution(saved);
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      workingRef.current = false;
      setWorking(false);
    }
  }

  async function regenerate() {
    if (!execution || workingRef.current) return;
    workingRef.current = true;
    setWorking(true);
    setError("");
    try {
      setExecution(
        await api<Execution>(
          `/api/executions/${execution.id}/regenerate`,
          {
            method: "POST",
            headers: { "Idempotency-Key": crypto.randomUUID() },
          },
        ),
      );
      setNotice("A new result is ready.");
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      workingRef.current = false;
      setWorking(false);
    }
  }

  async function refine() {
    if (!execution || workingRef.current) return;
    workingRef.current = true;
    setWorking(true);
    setError("");
    setNotice("");
    try {
      setExecution(
        await api<Execution>(`/api/executions/${execution.id}/refine`, {
          method: "POST",
          headers: { "Idempotency-Key": crypto.randomUUID() },
          body: JSON.stringify({ tone, instructions: refinement }),
        }),
      );
      setRefinement("");
      setNotice("Your refined result is ready.");
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      workingRef.current = false;
      setWorking(false);
    }
  }

  async function copyResult() {
    if (!execution) return;
    try {
      await navigator.clipboard.writeText(execution.result);
      setNotice("Result copied.");
    } catch {
      setError("Could not copy the result. Select and copy the text instead.");
    }
  }

  return (
    <main id="main-content" className="mx-auto min-h-screen max-w-6xl px-6 pb-20 pt-24">
      <div className="mb-8 max-w-3xl">
        <p className="caption-3 uppercase tracking-[0.12em] text-accent">
          AIToolnity catalogue
        </p>
        <h1 className="heading-2 mt-3 text-ink">Find a tool for your task.</h1>
        <p className="body-3 mt-4 text-ink/65">
          Choose a category to start. Tool forms come from the catalogue
          configuration.
        </p>
      </div>

      <nav aria-label="Catalogue path" className="mb-4 flex flex-wrap items-center gap-2">
        <button
          className="body-5 rounded-lg px-2 py-1 text-accent hover:bg-accent-soft focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
          onClick={goToCategories}
          type="button"
        >
          All categories
        </button>
        {category && (
          <>
            <span aria-hidden="true" className="caption-2 text-ink/35">/</span>
            <button
              className="body-5 rounded-lg px-2 py-1 text-accent hover:bg-accent-soft focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
              onClick={goToSubcategories}
              type="button"
            >
              {category.name}
            </button>
          </>
        )}
        {subcategory && (
          <>
            <span aria-hidden="true" className="caption-2 text-ink/35">/</span>
            <span aria-current="page" className="body-5 px-2 py-1 text-ink">
              {subcategory.name}
            </span>
          </>
        )}
      </nav>

      {error && (
        <div
          className="mb-4 rounded-xl border border-red-900/15 bg-red-50 px-4 py-3"
          role="alert"
        >
          <p className="body-6 text-red-900">{error}</p>
          {error.toLowerCase().includes("sign in") && (
            <a
              className="body-5 mt-2 inline-flex text-red-900 underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-red-900"
              href={googleLoginUrl()}
            >
              Continue with Google Login
            </a>
          )}
        </div>
      )}
      {notice && (
        <p className="mb-4 body-6 text-accent" role="status">
          {notice}
        </p>
      )}

      {loading && (
        <div
          aria-label="Loading catalogue"
          className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3"
          role="status"
        >
          {[0, 1, 2, 3, 4, 5].map((item) => (
            <div
              className="h-24 animate-pulse rounded-xl bg-black/5"
              key={item}
            />
          ))}
        </div>
      )}

      {!loading && !category && (
        <section aria-label="Categories" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {categories.map((item) => (
            <button
              className="title-3 group flex min-h-24 items-center justify-between rounded-xl border border-black/10 bg-white p-4 text-left text-ink transition duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] hover:-translate-y-0.5 hover:border-accent/30 hover:shadow-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent active:scale-[0.98]"
              key={item.id}
              onClick={() => void selectCategory(item)}
              type="button"
            >
              {item.name}
              <span aria-hidden="true" className="body-4 text-accent">View</span>
            </button>
          ))}
        </section>
      )}

      {!loading && category && !subcategory && (
        <section aria-label={`${category.name} subcategories`}>
          <h2 className="heading-5 mb-4 text-ink">{category.name}</h2>
          {subcategories.length ? (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {subcategories.map((item) => (
                <button
                  className="title-3 flex min-h-24 items-center justify-between rounded-xl border border-black/10 bg-white p-4 text-left text-ink transition duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] hover:-translate-y-0.5 hover:border-accent/30 hover:shadow-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent active:scale-[0.98]"
                  key={item.id}
                  onClick={() => void selectSubcategory(item)}
                  type="button"
                >
                  {item.name}
                  <span aria-hidden="true" className="body-4 text-accent">View</span>
                </button>
              ))}
            </div>
          ) : (
            <p className="body-6 rounded-xl border border-black/10 bg-white p-4 text-ink/65">
              No subcategories are available yet.
            </p>
          )}
        </section>
      )}

      {!loading && category && subcategory && !tool && (
        <section aria-label={`${subcategory.name} tools`} className="space-y-4">
          {items.length ? (
            items.map((item) => (
              <article
                className="rounded-xl border border-black/10 bg-white p-4"
                key={item.id}
              >
                <h2 className="title-2 text-ink">{item.name}</h2>
                <div className="mt-4 flex flex-wrap gap-2">
                  {item.tools.map((entry) => (
                    <button
                      className="button-sm rounded-lg border border-black/10 bg-paper px-3 py-2 text-ink transition-colors duration-300 hover:border-accent hover:bg-accent-soft focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent active:scale-[0.98]"
                      key={entry.id}
                      onClick={() => void selectTool(entry.id)}
                      type="button"
                    >
                      {entry.name}
                    </button>
                  ))}
                </div>
              </article>
            ))
          ) : (
            <p className="body-6 rounded-xl border border-black/10 bg-white p-4 text-ink/65">
              No tools are available in this subcategory yet.
            </p>
          )}
        </section>
      )}

      {!loading && tool && (
        <section className="grid items-start gap-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
          <article className="rounded-xl border border-black/10 bg-white p-4 sm:p-6">
            <button
              className="body-5 mb-4 rounded px-1 py-1 text-accent hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
              onClick={() => setTool(null)}
              type="button"
            >
              Back to tools
            </button>
            <h2 className="heading-5 text-ink">{tool.name}</h2>
            <p className="body-6 mt-2 text-ink/65">{tool.description}</p>
            <form className="mt-6 space-y-4" onSubmit={submitTool}>
              {tool.input_schema.fields.map((field) => (
                <div className="space-y-2" key={field.name}>
                  <label className="body-5 block text-ink" htmlFor={field.name}>
                    {field.label}
                    {field.required && <span aria-hidden="true"> *</span>}
                  </label>
                  <FieldControl
                    field={field}
                    onChange={(value) =>
                      setValues((previous) => ({
                        ...previous,
                        [field.name]: value,
                      }))
                    }
                    value={values[field.name] ?? ""}
                  />
                </div>
              ))}
              <div className="space-y-2">
                <label className="body-5 block text-ink" htmlFor="tone">
                  Tone
                </label>
                <select
                  className="field-control"
                  id="tone"
                  onChange={(event) => setTone(event.target.value)}
                  value={tone}
                >
                  {tool.tones.map((entry) => (
                    <option key={entry.id} value={entry.id}>
                      {entry.name}
                    </option>
                  ))}
                </select>
              </div>
              <button
                className="button-md w-full rounded-lg bg-ink px-3 py-2 text-white transition-colors duration-300 hover:bg-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:cursor-wait disabled:opacity-60"
                disabled={working}
                type="submit"
              >
                {working ? "Working…" : "Generate result"}
              </button>
            </form>
          </article>

          <section aria-label="Generated result" aria-live="polite">
            {execution ? (
              <article className="rounded-xl border border-black/10 bg-white p-4 sm:p-6">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="heading-5 text-ink">Your result</h2>
                    <p className="caption-2 mt-2 text-ink/55">
                      {execution.model} · {execution.tone}
                    </p>
                  </div>
                  <button
                    className="button-sm rounded-lg border border-black/15 px-3 py-2 text-ink hover:bg-paper focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
                    onClick={() => void copyResult()}
                    type="button"
                  >
                    Copy
                  </button>
                </div>
                <div className="body-3 mt-4 whitespace-pre-wrap rounded-xl bg-paper p-4 text-ink">
                  {execution.result}
                </div>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <button
                    className="button-sm rounded-lg border border-black/15 px-3 py-2 text-ink hover:bg-paper focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent disabled:opacity-60"
                    disabled={working}
                    onClick={() => void regenerate()}
                    type="button"
                  >
                    Regenerate
                  </button>
                  <Link
                    className="button-sm rounded-lg border border-black/15 px-3 py-2 text-center text-ink hover:bg-paper focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
                    href="/history"
                  >
                    View history
                  </Link>
                </div>
                <div className="mt-4 space-y-2">
                  <label className="body-5 block text-ink" htmlFor="refinement">
                    Refine this result
                  </label>
                  <textarea
                    className="field-control min-h-24 resize-y"
                    id="refinement"
                    onChange={(event) => setRefinement(event.target.value)}
                    placeholder="Describe what you would like to change."
                    value={refinement}
                  />
                  <button
                    className="button-sm rounded-lg bg-accent px-3 py-2 text-white hover:bg-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:opacity-60"
                    disabled={working || !refinement.trim()}
                    onClick={() => void refine()}
                    type="button"
                  >
                    Refine result
                  </button>
                </div>
              </article>
            ) : (
              <div className="flex min-h-64 flex-col justify-center rounded-xl border border-dashed border-black/20 bg-white p-6">
                <h2 className="title-2 text-ink">Your result will appear here</h2>
                <p className="body-6 mt-2 max-w-md text-ink/60">
                  Add the context for this task, choose a tone, and generate a
                  response.
                </p>
              </div>
            )}
          </section>
        </section>
      )}
    </main>
  );
}
