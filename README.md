# AIToolnity

**Every AI Tool. One Place.**

AIToolnity is a YAML driven catalogue for discovering and running AI tools. The Next.js application renders tool forms from the catalogue, and a FastAPI service validates requests, calls OpenRouter, and stores signed in users' settings and results in PostgreSQL.

## Run locally with Docker Compose

Requirements: Docker with the Compose plugin.

1. Copy `.env.example` to `.env`.
2. Set `POSTGRES_PASSWORD` to a local development password. Generate the application and encryption secrets:

   ```sh
   openssl rand -hex 32
   openssl rand -base64 32 | tr '+/' '-_'
   ```

   Put the first value in `APP_SECRET_KEY` and the second in `ENCRYPTION_KEY`. Keep `.env` private. The encryption value must be a URL safe base64 encoding of 32 random bytes, as produced by this command.
3. Configure Google OAuth and an OpenRouter key if you want to use those integrations. Browsing the catalogue does not require either provider.
4. Start the application:

   ```sh
   docker compose up --build
   ```

5. Open [http://localhost:3000](http://localhost:3000). The API health check is at [http://localhost:8000/api/health](http://localhost:8000/api/health), and FastAPI's API documentation is at [http://localhost:8000/docs](http://localhost:8000/docs).

Stop the services with `docker compose down`. Add `--volumes` only if you intend to delete the local PostgreSQL data.

For Google Login, create a Google OAuth web client and add this exact authorized redirect URI:

```text
http://localhost:8000/api/auth/google/callback
```

Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`, then restart the services. The login endpoint returns a clear configuration error until credentials are provided. For an HTTPS deployment, set `COOKIE_SECURE=true` and replace every local secret and database password.

To run generation, either set `OPENROUTER_API_KEY` in `.env` or sign in and save a personal key in AI settings. The default model is `openrouter/free`. Users can choose another OpenRouter model. Failed requests report an error and never silently switch to a paid model.

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

Run the backend tests with:

```sh
cd backend
python3 -m pytest
```

The tests cover catalogue validation and discovery, dynamic form configuration, and private history ownership. OpenRouter generation and Google OAuth require valid external credentials and are not claimed as live tested when those credentials are unavailable.

Run the frontend type check and production build with:

```sh
cd frontend
npm install
npx tsc --noEmit
npm run build
```
