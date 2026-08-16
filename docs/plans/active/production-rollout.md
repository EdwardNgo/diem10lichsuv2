# Execution Plan: Production Rollout

Date: 2026-08-15

## Status

Active

## Outcome

Production can publish versioned Docker images on merge to `main`, deploy those
images manually on the VPS, and back up PostgreSQL daily into a dedicated R2
bucket.

## Context

- Product operations: `docs/product/operations-and-quality.md`
- VPS architecture: `docs/decisions/0001-vps-monorepo-architecture.md`
- Production delivery decision: `docs/decisions/0004-production-delivery.md`
- Runtime topology: `compose.yml`
- Operator runbook: `docs/operations/runbook.md`

## Scope

In scope:

- GitHub Container Registry image publishing for `apps/web` and `services/api`.
- Compose image tags for production while preserving local builds.
- Manual VPS deploy script and rollback path.
- PostgreSQL backup script to Cloudflare R2.
- Runbook and decision documentation.

Out of scope:

- Automatic SSH deploy from GitHub.
- Dedicated staging environment.
- Full monitoring, Seq, rate limiting and deep R2/PostgreSQL health checks.

## Approach

1. Add a publish workflow that reruns web/API checks and pushes GHCR images with
   immutable SHA tags.
2. Teach Compose about production images and pass production log/session
   environment variables into API containers.
3. Add a manual deploy script that pulls images, runs Alembic, recreates
   services and smokes public endpoints.
4. Add a backup script that uses `pg_dump -Fc` and uploads the dump to R2 via an
   S3-compatible endpoint.
5. Record the runbook and accepted production delivery decision.

## Risks And Recovery

- A bad app release can be recovered by setting `IMAGE_TAG` back to the previous
  known-good tag and running `scripts/deploy.sh`.
- A failed migration must stop the deploy before recreating app services with
  incompatible code.
- Data restore requires a fresh snapshot/backup and a downtime window; do not
  restore over production ad hoc.

## Progress

- [x] Add GHCR image publish workflow.
- [x] Update Compose and environment examples for image tags and production
  logging.
- [x] Add manual deploy script.
- [x] Add PostgreSQL backup script for R2.
- [x] Update runbook and production delivery decision.
- [x] Run validation.

## Decisions

- 2026-08-15: Use GHCR, manual VPS deploy, cron-based Postgres backup to
  R2 and Cloudflare-fronted TLS as accepted in
  `docs/decisions/0004-production-delivery.md`.

## Validation

- Focused proof: `sh -n scripts/deploy.sh` and
  `sh -n scripts/backup-postgres.sh` passed.
- Integration or end-to-end proof:
  `docker compose --env-file .env.example config` passed.
- Repository-required checks: not required for application code because this
  work only changes CI, Compose, scripts and docs. `git diff --check` passed.

## Result

Production rollout scaffolding is implemented. GitHub Actions can publish
versioned GHCR images after checks pass, Compose can pull pinned web/API images
by `IMAGE_TAG`, VPS deploy is scripted, PostgreSQL backup to R2 is scripted, and
the operator runbook/decision record describe rollout, rollback, TLS and restore
responsibilities.
