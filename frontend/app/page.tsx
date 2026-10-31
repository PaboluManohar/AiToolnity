import Link from "next/link";

import { TaglineReveal } from "@/components/tagline-reveal";

const benefits = [
  {
    title: "Find a focused tool",
    description:
      "Browse a catalogue organized around categories, subcategories, and tasks.",
  },
  {
    title: "Start with useful inputs",
    description:
      "Each tool displays the fields defined for it, so you know what context to provide.",
  },
  {
    title: "Shape the response",
    description:
      "Choose a tone, then refine or regenerate a result when you need another pass.",
  },
  {
    title: "Keep your work together",
    description:
      "Sign in to save your model settings and return to your generated results.",
  },
];

const steps = [
  {
    number: "01",
    title: "Browse the catalogue",
    description: "Choose a category and narrow down to a task that fits.",
  },
  {
    number: "02",
    title: "Add your context",
    description: "Fill in the fields and select the tone for your response.",
  },
  {
    number: "03",
    title: "Generate and refine",
    description: "Review the result, copy it, or ask for a clearer next draft.",
  },
];

const questions = [
  {
    question: "What is AIToolnity?",
    answer:
      "AIToolnity is one place to discover and run a catalogue of AI tools for writing, learning, work, and everyday tasks.",
  },
  {
    question: "How are tools organized?",
    answer:
      "The catalogue uses categories, subcategories, and items. Tool forms and prompts are read from YAML configuration.",
  },
  {
    question: "Can I use my own OpenRouter key?",
    answer:
      "Yes. Sign in, add your key in AI settings, and choose the model you want to use.",
  },
  {
    question: "Which model is selected by default?",
    answer:
      "The default model is openrouter/free. AIToolnity does not switch to a paid model when a request fails.",
  },
  {
    question: "Are my settings and history private?",
    answer:
      "Settings and saved results are tied to your signed in account. Your saved provider key is encrypted on the server and is never returned to the browser.",
  },
  {
    question: "Can I add a tool without changing application code?",
    answer:
      "Yes. Add a valid item or sub item to the YAML catalogue. The shared form and execution flow use its configuration.",
  },
];

export default function HomePage() {
  return (
    <main id="main-content" className="overflow-hidden">
      <section className="mx-auto grid min-h-[720px] max-w-6xl items-center gap-12 px-6 pb-20 pt-24 md:grid-cols-[1.05fr_0.95fr] md:pt-24">
        <div className="max-w-2xl">
          <p className="caption-3 mb-4 uppercase tracking-[0.12em] text-accent">
            A clearer way to work with AI
          </p>
          <h1 className="heading-1 hero-heading max-w-[680px]">
            Run the right AI tool for every task.
          </h1>
          <p className="body-3 mt-6 max-w-[680px] text-ink/70">
            Find a focused tool, add the context it needs, and shape the result
            with a model and tone that work for you.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-4">
            <Link
              className="button-md inline-flex items-center justify-center rounded-lg bg-ink px-3 py-2 text-white transition duration-300 hover:bg-accent active:translate-y-px focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
              href="/tools"
            >
              Explore tools
            </Link>
            <p className="caption-2 text-ink/60">
              Browse the catalogue before signing in.
            </p>
          </div>
          <p className="body-6 mt-10 border-l-2 border-accent pl-3 text-ink/70">
            Every catalogue entry is loaded from YAML configuration.
          </p>
        </div>

        <div
          aria-label="Preview of the AIToolnity catalogue and tool form"
          className="rounded-2xl border border-black/10 bg-white p-3 shadow-xl shadow-black/5 sm:p-6"
          role="img"
        >
          <div className="flex items-center justify-between border-b border-black/10 pb-4">
            <div>
              <p className="title-3 text-ink">Tool workspace</p>
              <p className="caption-2 mt-1 text-ink/55">
                Choose a task and make it your own
              </p>
            </div>
            <span className="rounded-full bg-accent-soft px-3 py-1 caption-3 text-accent">
              Ready to explore
            </span>
          </div>
          <div className="grid gap-3 py-4 sm:grid-cols-[0.8fr_1.2fr]">
            <div className="space-y-2 rounded-xl bg-paper p-3">
              <p className="caption-3 mb-3 uppercase tracking-wide text-ink/50">
                Catalogue
              </p>
              <div className="h-10 rounded-lg bg-white px-3 py-3">
                <span className="block h-1.5 w-3/4 rounded bg-ink/15" />
              </div>
              <div className="h-10 rounded-lg bg-accent-soft px-3 py-3">
                <span className="block h-1.5 w-2/3 rounded bg-accent/35" />
              </div>
              <div className="h-10 rounded-lg bg-white px-3 py-3">
                <span className="block h-1.5 w-4/5 rounded bg-ink/15" />
              </div>
            </div>
            <div className="rounded-xl border border-black/10 p-4">
              <p className="title-3 text-ink">Your tool</p>
              <p className="caption-2 mt-1 text-ink/55">
                Add the details that matter
              </p>
              <div className="mt-4 h-20 rounded-lg border border-black/10 bg-paper p-3">
                <span className="block h-1.5 w-2/5 rounded bg-ink/15" />
                <span className="mt-3 block h-1.5 w-4/5 rounded bg-ink/10" />
              </div>
              <div className="mt-3 flex items-center justify-between">
                <span className="caption-2 text-ink/55">Tone</span>
                <span className="rounded-lg bg-paper px-3 py-2 caption-2 text-ink">
                  Professional
                </span>
              </div>
              <div className="mt-4 h-10 rounded-lg bg-ink px-3 py-3">
                <span className="mx-auto block h-1.5 w-1/3 rounded bg-white/70" />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-white py-20 sm:py-24">
        <div className="mx-auto max-w-6xl px-6">
          <p className="caption-3 uppercase tracking-[0.12em] text-accent">
            One workspace, less searching
          </p>
          <h2 className="heading-3 mt-4 max-w-2xl text-ink">
            Move from a blank page to a useful first draft.
          </h2>
          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {benefits.map((benefit) => (
              <article
                className="rounded-xl border border-black/10 bg-paper p-4"
                key={benefit.title}
              >
                <h3 className="title-2 text-ink">{benefit.title}</h3>
                <p className="body-6 mt-3 text-ink/65">
                  {benefit.description}
                </p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-20 sm:py-24">
        <div className="max-w-2xl">
          <p className="caption-3 uppercase tracking-[0.12em] text-accent">
            A simple workflow
          </p>
          <h2 className="heading-3 mt-4 text-ink">From task to result in three steps.</h2>
        </div>
        <ol className="mt-10 grid gap-4 md:grid-cols-3">
          {steps.map((step) => (
            <li
              className="rounded-xl border border-black/10 bg-white p-6"
              key={step.number}
            >
              <span className="caption-3 text-accent">{step.number}</span>
              <h3 className="title-2 mt-6 text-ink">{step.title}</h3>
              <p className="body-6 mt-3 text-ink/65">{step.description}</p>
            </li>
          ))}
        </ol>
      </section>

      <div className="bg-[#181818]">
        <TaglineReveal />
      </div>

      <section className="bg-white py-20 sm:py-24">
        <div className="mx-auto max-w-4xl px-6">
          <p className="caption-3 uppercase tracking-[0.12em] text-accent">
            Common questions
          </p>
          <h2 className="heading-3 mt-4 text-ink">Before you explore</h2>
          <div className="mt-8 divide-y divide-black/10">
            {questions.map((item) => (
              <details className="group py-4" key={item.question}>
                <summary className="title-3 cursor-pointer list-none text-ink marker:hidden focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent">
                  {item.question}
                </summary>
                <p className="body-6 mt-3 max-w-3xl text-ink/65">
                  {item.answer}
                </p>
              </details>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-20 sm:py-24">
        <div className="rounded-2xl bg-accent-soft px-6 py-10 sm:px-10 sm:py-12">
          <div className="max-w-2xl">
            <h2 className="heading-3 text-ink">
              Start with the task you have today.
            </h2>
            <p className="body-3 mt-4 text-ink/70">
              Browse the catalogue, choose a tool, and see what a focused
              workflow can do.
            </p>
            <Link
              className="button-md mt-6 inline-flex items-center justify-center rounded-lg bg-ink px-3 py-2 text-white transition duration-300 hover:bg-accent active:translate-y-px focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink"
              href="/tools"
            >
              Explore tools
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-black/10 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-6 py-6 sm:flex-row sm:items-center sm:justify-between">
          <p className="caption-2 text-ink/60">
            AIToolnity · Every AI Tool. One Place.
          </p>
          <nav aria-label="Legal" className="flex gap-6">
            <Link
              className="body-6 text-ink/65 hover:text-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
              href="/privacy"
            >
              Privacy
            </Link>
            <Link
              className="body-6 text-ink/65 hover:text-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
              href="/terms"
            >
              Terms
            </Link>
          </nav>
        </div>
      </footer>
    </main>
  );
}
