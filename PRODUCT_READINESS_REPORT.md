# AIToolnity production readiness review

## Assessment

**Status: ready for configured local development and staging validation; not yet cleared for public production deployment.**

The application, database migration, catalogue, frontend workflows, and dependency checks pass the validations listed below. No live Google OAuth or OpenRouter request was made because provider credentials were not available. This review is an implementation and test review, not a penetration test or independent security certification.

## Scope and evidence

Reviewed the FastAPI authentication, settings, execution, catalogue, request-guard, database, and migration paths; the Next.js tool, settings, and history workflows; Compose configuration; setup documentation; and dependency manifests.

| Check | Result |
|---|---|
| Backend tests on SQLite | 18 passed |
| Backend tests on isolated PostgreSQL 16 | 18 passed |
| Fresh PostgreSQL startup migration | Passed; `/api/health` returned 200 |
| YAML catalogue API | Passed; 29 categories returned from the configured catalogue |
| Frontend type check | Passed |
| Frontend lint | Passed |
| Frontend workflow tests | 6 passed |
| Next.js production build | Passed |
| Frontend dependency audit | 0 advisories |
| Production and development Compose configuration | Both validated |
| OpenRouter live request | Not tested; requires a personal user key |
| Google OAuth login | Not tested; requires configured Google OAuth credentials |
| Database backup and restore | Targets documented; restore was not executed against persistent data |

The backend test run reports one upstream `StarletteDeprecationWarning` about `httpx` usage in `TestClient`; it did not fail the suite.

## Changes made during hardening

- Removed the shared server OpenRouter key fallback. Generation requires the authenticated user's encrypted personal key and does not retry with a different model.
- Added OAuth state, nonce, and PKCE validation; secure cookie configuration checks; request origin, body-size, and process-local rate limits; and sanitized request validation errors.
- Added per-user idempotency records, replay handling, and rejection when a request key is reused for different content.
- Tightened YAML schema, hierarchy, ID, duplicate, enabled-state, and dynamic form validation.
- Added an explicit Alembic baseline schema and compatibility checks for an existing complete pre-migration schema.
- Added frontend tests for catalogue navigation, dynamic forms, execution controls, and signed-out settings/history states.
- Added Makefile workflows, safer backup/restore commands, and deployment caveats to the README.

## Remaining risks and required actions

| Priority | Finding | Status and recommended action |
|---|---|---|
| **High** | Request throttling is in process memory. Limits reset on restarts and are not shared across workers or replicas. | Before a multi-worker or multi-instance deployment, enforce limits at the trusted gateway or adopt a shared limiter. Do not treat the in-process guard as the sole production abuse control. |
| **High** | Production TLS termination, security headers, and edge protections are not provided by the local Compose stack. | Put the application behind a maintained HTTPS reverse proxy or platform gateway. Configure HSTS and an appropriate Content Security Policy there, and expose only the required public endpoints. |
| **Medium** | The initial migration is a fixed baseline and can adopt a fully compatible existing schema, but it does not reconcile partially divergent tables or columns. No later schema revisions exist yet. | Back up and inspect an existing database before adopting it. Add a new Alembic revision for every future schema change, and run migrations as a controlled deployment step when scaling instances. |
| **Medium** | Fernet encryption-key rotation is not automated. Replacing `ENCRYPTION_KEY` without re-encrypting saved provider keys makes them unreadable. | Preserve the key securely and design a controlled key-rotation procedure before production rotation is needed. |
| **Medium** | Execution idempotency records have no retention policy. | Define a retention window and cleanup process before sustained production use; coordinate it with the duration for which retries must remain replayable. |
| **Release blocker** | Google OAuth and real OpenRouter behavior have not been verified with production credentials. | Configure test credentials in a staging environment and complete login, account isolation, saved-key, provider success/error, and logout checks before launch. |
| **Release blocker** | Backup creation and restoration commands have not been exercised against a persistent production-like database. | Test backup, restore, and application recovery on a disposable database before relying on them. Never use a production restore as a test. |

## Configuration required

Copy `.env.example` using `make setup`, then set:

- `POSTGRES_PASSWORD` to a unique database password.
- `APP_SECRET_KEY` to a random secret of at least 32 characters.
- `ENCRYPTION_KEY` to a valid Fernet key; keep a protected backup of it.
- `APP_ENV=production` and `COOKIE_SECURE=true` for a production HTTPS deployment.
- `FRONTEND_URL`, `FRONTEND_ORIGINS`, `GOOGLE_REDIRECT_URI`, `NEXT_PUBLIC_API_URL`, and `NEXT_PUBLIC_SITE_URL` to the actual deployment URLs.
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` to the Google OAuth web-client credentials. Configure the matching callback URI with Google.
- `OPENROUTER_SITE_URL` and `OPENROUTER_SITE_NAME` if those attribution headers are desired.

`DATABASE_URL` is assembled by Compose from the PostgreSQL settings. For a non-Compose backend, set it directly to the SQLAlchemy PostgreSQL URL. No shared `OPENROUTER_API_KEY` is used; each user must save a personal OpenRouter key in AI settings.

## Local commands

```sh
make prerequisites
make setup
# Edit .env and set the required secrets and URLs.
make devrun
```

In another terminal:

```sh
make lint
make typecheck
make test
```

For production image builds and background startup, use `make build` and `make run`. Stop containers without deleting the database volume using `make stop`. See [README.md](./README.md) for all targets, migrations, and backup procedures.
