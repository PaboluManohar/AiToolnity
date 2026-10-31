# AIToolnity

**Every AI Tool. One Place.**

AIToolnity is a YAML driven catalogue for discovering and running AI tools. The Next.js application renders tool forms from the catalogue, and a FastAPI service validates requests, calls OpenRouter, and stores signed in users' settings and results in PostgreSQL.

## Run locally with Docker Compose

Requirements: Docker with the Compose plugin.

1. Run `make setup` to create `.env` from `.env.example`. The target never overwrites an existing `.env`.
2. Set `POSTGRES_PASSWORD` to a local development password. Generate the application and encryption secrets:

   ```sh
   openssl rand -hex 32
   openssl rand -base64 32 | tr '+/' '-_'
   ```

   Put the first value in `APP_SECRET_KEY` and the second in `ENCRYPTION_KEY`. Keep `.env` private. The encryption value must be a URL safe base64 encoding of 32 random bytes, as produced by this command.
3. Configure Google OAuth and an OpenRouter key if you want to use those integrations. Browsing the catalogue does not require either provider.
4. Start the application:

   ```sh
   make devrun
   ```

5. Open [http://localhost:3000](http://localhost:3000). The API health check is at [http://localhost:8000/api/health](http://localhost:8000/api/health), and FastAPI's API documentation is at [http://localhost:8000/docs](http://localhost:8000/docs).

Stop the services with `make stop`. This stops containers without deleting PostgreSQL data. Do not add `--volumes` unless you deliberately intend to delete that data.

Use `make run` to start the application in the background, `make logs` to follow logs, and `make stop` to stop it. Run `make prerequisites` to check local tooling. `make install` installs frontend dependencies; `make build` builds the Compose images.

For Google Login, create a Google OAuth web client and add this exact authorized redirect URI:

```text
http://localhost:8000/api/auth/google/callback
```

Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`, then restart the services. The login endpoint returns a clear configuration error until credentials are provided. For an HTTPS deployment, set `COOKIE_SECURE=true` and replace every local secret and database password.

To run generation, sign in and save a personal OpenRouter API key in AI settings. Keys are encrypted with the server's `ENCRYPTION_KEY` before being stored. The default model is `openrouter/free`. Users can choose another OpenRouter model. A server wide provider key is not used as a fallback. Failed requests report an error and never switch models.

## Run the services without Docker

Start a PostgreSQL database and set `DATABASE_URL` to a SQLAlchemy URL such as:

```text
postgresql+psycopg://aitoolnity:your_password@localhost:5432/aitoolnity
```

Install backend dependencies and start FastAPI:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
export DATABASE_URL='postgresql+psycopg://aitoolnity:your_password@localhost:5432/aitoolnity'
export APP_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
export ENCRYPTION_KEY="$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
export GOOGLE_CLIENT_ID=''
export GOOGLE_CLIENT_SECRET=''
export FRONTEND_URL=http://localhost:3000
export FRONTEND_ORIGINS=http://localhost:3000
export GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
export TOOLS_CONFIG_PATH="$PWD/config/tools.yaml"
uvicorn app.main:app --app-dir backend --reload
```

In another terminal:

```sh
cd frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8000` in the frontend environment if the API uses a different address.

## Catalogue format

`config/tools.yaml` contains categories, subcategories, and items. An item without `sub_items` is a tool; when `sub_items` are present, each sub item is an individual tool under that item. Tool configuration may override the shared defaults:

```yaml
tool_defaults:
  description_template: "A guided {name} assistant for your work."
  input_schema:
    fields:
      - name: context
        label: What would you like help with?
        type: textarea
        required: true
  system_prompt: "Complete the requested task using the supplied context."
  tones:
    - id: professional
      name: Professional
      instructions: Use a clear, polished voice.
  enabled: true
```

A tool can override `description`, `input_schema`, `system_prompt`, `tones`, and `enabled`. Supported input types are `text`, `textarea`, `email`, `url`, `number`, and `select`; select fields require `options`. IDs must be unique among tools and use lowercase letters, numbers, and hyphens. The catalogue is validated at startup. Invalid YAML or duplicate tool IDs stop startup with a clear error. Restart the backend after editing the catalogue.

For example, an item can define its own input form and prompt:

```yaml
- id: writing
  name: Writing
  subcategories:
    - id: editing
      name: Editing
      items:
        - id: clarity-editor
          name: Clarity Editor
          description: Improve clarity while preserving the original meaning.
          system_prompt: Edit the supplied writing for clarity and flow.
          input_schema:
            fields:
              - name: draft
                label: Draft to edit
                type: textarea
                required: true
              - name: audience
                label: Intended audience
                type: text
                required: false
          tones:
            - id: concise
              name: Concise
              instructions: Keep the edited text direct and brief.
          enabled: true
```

## API overview

- `GET /api/catalogue/categories`
- `GET /api/catalogue/categories/{category_id}/subcategories`
- `GET /api/catalogue/categories/{category_id}/subcategories/{subcategory_id}/items`
- `GET /api/catalogue/tools/{tool_id}`
- `POST /api/executions`
- `POST /api/executions/{execution_id}/regenerate`
- `POST /api/executions/{execution_id}/refine`
- `GET /api/history`
- `GET`, `PUT /api/settings`; `DELETE /api/settings/api-key`
- `POST /api/settings/test`
- `GET /api/auth/google/start`, `GET /api/auth/me`, `POST /api/auth/logout`

All settings and history queries are scoped to the signed in user. Provider keys are encrypted with Fernet before storage and are not included in API responses. The Google session is an HTTP only, signed cookie.

## Tests

Run all frontend and backend tests with:

```sh
make test
```

The backend tests run against an isolated SQLite database by default and cover catalogue validation and discovery, dynamic form configuration, execution idempotency, provider failures, and private history ownership. OpenRouter generation and Google OAuth require valid external credentials and are not claimed as live tested when those credentials are unavailable.

Run frontend lint and type checking with:

```sh
make lint
make typecheck
```

`make build` builds the production images. Migrations run at backend startup; `make migrate` can apply them explicitly while the database is running.

## Database backups

Keep PostgreSQL backups outside the container and test restoration before relying on them:

```sh
make db-backup
make db-restore BACKUP=backups/aitoolnity-YYYYMMDD-HHMMSS.dump CONFIRM_RESTORE=YES
```

Restore replaces database objects. Verify the selected backup and confirm explicitly before running the restore target. Store `.env` and backups securely. Changing `ENCRYPTION_KEY` without first decrypting and re-encrypting saved provider keys makes those keys unreadable.

## Production deployment notes

Set `APP_ENV=production`, `COOKIE_SECURE=true`, strong unique application/database/encryption secrets, the production Google OAuth redirect URI, and the exact trusted frontend origin. Terminate HTTPS at a trusted reverse proxy and enable its security headers. No shared OpenRouter key is used; every user who generates content must configure a personal key. The built in request limiter is process local, so multi instance deployments must also enforce shared rate limits at the gateway or use a shared limiter. Review [PRODUCT_READINESS_REPORT.md](./PRODUCT_READINESS_REPORT.md) before deployment.
