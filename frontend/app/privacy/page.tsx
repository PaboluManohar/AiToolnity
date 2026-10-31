export default function PrivacyPage() {
  return (
    <main id="main-content" className="mx-auto min-h-screen max-w-3xl px-6 pb-20 pt-24">
      <h1 className="heading-2 text-ink">Privacy</h1>
      <p className="body-6 mt-4 text-ink/65">
        AIToolnity stores the Google account details needed to identify your
        account, the model preference you save, and results you create while
        signed in. Your submitted prompts and generated results are stored as
        execution history.
      </p>
      <h2 className="heading-5 mt-10 text-ink">Provider keys</h2>
      <p className="body-6 mt-3 text-ink/65">
        OpenRouter keys saved in AI settings are encrypted before they are
        stored. They are used to make provider requests and are not returned to
        the browser.
      </p>
      <h2 className="heading-5 mt-10 text-ink">Third party services</h2>
      <p className="body-6 mt-3 text-ink/65">
        Google provides sign in. OpenRouter processes prompts and responses
        when you run a tool. Their privacy terms apply to their services.
      </p>
      <h2 className="heading-5 mt-10 text-ink">Your choices</h2>
      <p className="body-6 mt-3 text-ink/65">
        You can remove a saved OpenRouter key in AI settings and sign out at
        any time. For a deployed instance, use its published contact channel
        to request account data removal.
      </p>
    </main>
  );
}
