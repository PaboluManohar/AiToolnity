SHELL := /bin/sh
.DEFAULT_GOAL := help

COMPOSE ?= docker compose
BACKUP ?= backups/aitoolnity-$(shell date +%Y%m%d-%H%M%S).dump

.PHONY: help prerequisites setup require-env install build devrun run test frontend-test backend-test lint typecheck migrate logs stop db-backup db-restore

help:
	@printf '%s\n' \
	  'AIToolnity commands:' \
	  '  make prerequisites  Check Docker, Node.js, and npm' \
	  '  make setup          Create .env from .env.example only when absent' \
	  '  make install       Install frontend dependencies with npm ci' \
	  '  make build         Build the Docker Compose services' \
	  '  make devrun        Run the development Compose stack in the foreground' \
	  '  make run           Start the Compose stack in the background' \
	  '  make test          Run frontend and backend tests' \
	  '  make lint          Lint frontend source' \
	  '  make typecheck     Type check frontend source' \
	  '  make migrate       Apply Alembic migrations to the running database' \
	  '  make logs          Follow Compose service logs' \
	  '  make stop          Stop services without deleting database data' \
	  '  make db-backup     Write a PostgreSQL custom format backup' \
	  '  make db-restore BACKUP=... CONFIRM_RESTORE=YES  Replace database contents'

prerequisites:
	@command -v docker >/dev/null || { echo 'Docker is required.' >&2; exit 1; }
	@docker compose version >/dev/null
	@command -v node >/dev/null || { echo 'Node.js is required.' >&2; exit 1; }
	@command -v npm >/dev/null || { echo 'npm is required.' >&2; exit 1; }
	@echo 'Docker Compose, Node.js, and npm are available.'

setup:
	@if [ -e .env ]; then \
	  echo '.env already exists; it was left unchanged.'; \
	else \
	  cp .env.example .env; \
	  echo 'Created .env. Set its required passwords and secrets before starting services.'; \
	fi

require-env:
	@test -f .env || { echo 'Missing .env. Run make setup, then configure its required values.' >&2; exit 1; }

install:
	cd frontend && npm ci

build: require-env
	$(COMPOSE) build

devrun: require-env
	$(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml up --build

run: require-env
	$(COMPOSE) up --build -d

test: frontend-test backend-test

frontend-test:
	cd frontend && npm test

backend-test:
	docker build -f backend/Dockerfile -t aitoolnity-backend-test:local .
	docker run --rm \
	  -e APP_ENV=development \
	  -e DATABASE_URL=sqlite+pysqlite:///:memory: \
	  -e APP_SECRET_KEY=aitoolnity-test-secret-not-for-deployment-0123456789 \
	  -e ENCRYPTION_KEY=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA= \
	  aitoolnity-backend-test:local pytest -q

lint:
	cd frontend && npm run lint

typecheck:
	cd frontend && npm run typecheck

migrate: require-env
	$(COMPOSE) run --rm --no-deps backend alembic upgrade head

logs: require-env
	$(COMPOSE) logs --follow --tail=200

stop: require-env
	$(COMPOSE) down

db-backup: require-env
	@mkdir -p "$(dir $(BACKUP))"
	$(COMPOSE) exec -T db sh -c 'pg_dump -Fc -U "$$POSTGRES_USER" "$$POSTGRES_DB"' > "$(BACKUP)"
	@echo "Backup written to $(BACKUP)"

db-restore: require-env
	@test -n "$(BACKUP)" && test -f "$(BACKUP)" || { echo 'Set BACKUP to an existing dump file.' >&2; exit 1; }
	@test "$(CONFIRM_RESTORE)" = "YES" || { echo 'Restore replaces database objects. Re-run with CONFIRM_RESTORE=YES after verifying the dump.' >&2; exit 1; }
	$(COMPOSE) exec -T db sh -c 'pg_restore --clean --if-exists --no-owner --exit-on-error -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"' < "$(BACKUP)"
