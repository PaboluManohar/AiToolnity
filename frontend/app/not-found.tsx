import Link from "next/link";

export default function NotFound() {
  return (
    <main
      className="flex min-h-screen items-center justify-center px-6 pt-24"
      id="main-content"
    >
      <section className="max-w-xl text-center">
        <p className="caption-3 uppercase tracking-[0.12em] text-accent">
          Page not found
        </p>
        <h1 className="heading-2 mt-4 text-ink">This page is not here.</h1>
        <p className="body-3 mt-4 text-ink/65">
          The address may have changed. Return home or explore the tools
          catalogue.
        </p>
        <Link
          className="button-md mt-6 inline-flex rounded-lg bg-ink px-3 py-2 text-white hover:bg-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          href="/"
        >
          Go to home
        </Link>
      </section>
    </main>
  );
}
