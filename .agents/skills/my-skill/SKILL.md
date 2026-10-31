---
description: Build and maintain AIToolnity, a simple YAML-driven AI
  tools platform using Next.js, FastAPI, PostgreSQL, Google Login, and
  OpenRouter.
name: aitoolnity
---

# AIToolnity Development Skill

## Project Goal

Build **AIToolnity**, a platform where users can discover and run many
AI tools from one application.

**Tagline:** Every AI Tool. One Place.

Keep the implementation straightforward. Follow the existing project
structure and avoid unnecessary abstractions, frameworks, or features.

## Technology Stack

-   Frontend: Next.js, React, TypeScript, Tailwind CSS
-   Backend: Python FastAPI
-   Database: PostgreSQL
-   AI provider: OpenRouter
-   Default model: `openrouter/free`
-   Tool catalogue: YAML
-   Authentication: Google Login
-   Local development: Docker Compose

## Core Requirements

### 1. Home Page

Create `/` with: - AIToolnity branding and navigation - A short
explanation of the problem the platform solves - A concise feature
overview - An Explore Tools button - Google Login

### 2. Dynamic Tools Catalogue

Create `/tools` and load the catalogue from `config/tools.yaml`.

Support this hierarchy:

`Categories → Subcategories → Items → Individual Tools`

Initially show categories only. Clicking a category shows its
subcategories; clicking a subcategory shows its items and tools. An item
may contain one or multiple tools.

Do not hardcode category names, subcategory names, items, or individual
tools in frontend components.

### 3. YAML-Driven Tools

Each tool configuration should support: - Unique ID - Name and
description - Input field schema - Default system prompt - Supported
tone/style options - Enabled/disabled status

Validate the YAML when loading it. Report invalid configuration clearly
and do not silently ignore errors.

**Critical rule:** Adding a valid tool to YAML must make it appear in
the correct place and work through the existing generic execution flow.
Do not add tool-specific frontend components, backend endpoints, or code
for individual tools.

Use a single reusable dynamic form renderer and a single reusable AI
execution flow.

### 4. Tool Execution

When a user selects a tool: 1. Load its configuration. 2. Render its
input form from the configured schema. 3. Let the user choose an
available tone/style, such as professional, formal, casual, concise, or
simple English. 4. Validate input on the backend. 5. Apply the tool's
configured system prompt and requested style. 6. Call the selected
OpenRouter model. 7. Display and save the result.

Provide Copy, Regenerate, and Refine actions. Refinement should allow a
user to change tone, style, or instructions while preserving the
original task context.

### 5. OpenRouter and AI Settings

Users can save their own OpenRouter API key and select a model. Use
`openrouter/free` as the default model preference.

-   Never expose saved API keys to the frontend.
-   Encrypt API keys at rest.
-   Never log credentials.
-   Let users test, update, and remove their key.
-   Handle invalid keys, rate limits, provider errors, and unavailable
    models clearly.
-   Never silently switch to a paid model.

Keep provider calls in one reusable backend service.

### 6. Google Login

Implement Google OAuth login. After authentication, users can manage
their AI settings and view their saved results.

Protect user-specific data. A user must not be able to access another
user's API key, settings, or execution history.

### 7. PostgreSQL

Use PostgreSQL to store: - Users - User AI settings and encrypted
credentials - Tool execution history, including tool ID, input, result,
model, tone, and timestamp

Keep the tool catalogue in YAML. Adding a tool must not require a
database schema change.

### 8. Backend API

Use FastAPI for generic endpoints to: - Get categories, subcategories,
items, and tools - Get a tool's configuration - Execute a tool - Refine
or regenerate a result - Get execution history - Read and update AI
settings - Test the OpenRouter connection

Avoid creating endpoints for individual tools.

## Suggested Structure

``` text
aitoolnity/
├── frontend/
│   ├── app/
│   ├── components/
│   └── lib/
├── backend/
│   └── app/
│       ├── main.py
│       ├── routes/
│       ├── services/
│       ├── models/
│       └── database.py
├── config/
│   └── tools.yaml
├── docker-compose.yml
├── .env.example
└── README.md
```

Adapt this structure if a working repository already exists; do not
reorganize files without a reason.

## Development Order

Implement incrementally:

1.  Set up frontend, FastAPI backend, and PostgreSQL.
2.  Create and validate the YAML configuration loader.
3.  Build dynamic category and tool navigation.
4.  Render forms from tool input schemas.
5.  Integrate OpenRouter through a shared execution service.
6.  Add Google Login.
7.  Add secure AI settings.
8.  Save and display execution history.
9.  Add refine and regenerate actions.
10. Test and document local setup.

Keep each step runnable before proceeding to the next.

## Coding Rules

-   Keep code simple, readable, and modular.
-   Reuse components and services.
-   Do not build features outside the requirements unless necessary.
-   Do not hardcode tools in the frontend or backend.
-   Use environment variables for secrets and configuration.
-   Include `.env.example`, but never commit real secrets.
-   Add useful validation and error messages.
-   Use database migrations if the project setup calls for them.
-   Add tests for YAML validation, dynamic discovery, execution,
    authentication boundaries, and user data ownership.
-   Update the README with setup and run instructions.
-   Do not claim a feature works unless it has been implemented and
    tested.

## Definition of Done

The core workflow works end to end:

1.  A user opens the home page.
2.  The user explores categories and selects a tool.
3.  The UI renders that tool's form from YAML.
4.  The user submits input and selects a style.
5.  The backend calls OpenRouter using the selected model.
6.  The result appears in the UI and is saved in PostgreSQL.
7.  The authenticated user can view, refine, regenerate, and copy their
    own results.
8.  Adding another valid tool to YAML makes it discoverable and
    executable without tool-specific code.
