export default function TermsPage() {
  return (
    <main id="main-content" className="mx-auto min-h-screen max-w-3xl px-6 pb-20 pt-24">
      <h1 className="heading-2 text-ink">Terms</h1>
      <p className="body-6 mt-4 text-ink/65">
        Use AIToolnity lawfully and only with content you are permitted to
        submit. You are responsible for reviewing AI generated content before
        using or sharing it.
      </p>
      <h2 className="heading-5 mt-10 text-ink">AI generated content</h2>
      <p className="body-6 mt-3 text-ink/65">
        Responses can be incomplete or incorrect. AIToolnity does not guarantee
        that a response is accurate, suitable, or available at all times.
      </p>
      <h2 className="heading-5 mt-10 text-ink">Provider accounts</h2>
      <p className="body-6 mt-3 text-ink/65">
        If you add an OpenRouter key, provider usage is subject to your
        OpenRouter account terms and model availability. AIToolnity will not
        silently select a different model when a request fails.
      </p>
    </main>
  );
}
