#!/usr/bin/env sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env}"
COMPOSE_FILE="${COMPOSE_FILE:-$ROOT_DIR/compose.yml}"

usage() {
  cat <<'USAGE'
Usage:
  scripts/deploy.sh [IMAGE_TAG]

Environment:
  ENV_FILE       Path to the VPS .env file. Defaults to ./.env.
  COMPOSE_FILE   Path to compose.yml. Defaults to ./compose.yml.

Examples:
  scripts/deploy.sh sha-abc1234
  IMAGE_TAG=sha-abc1234 scripts/deploy.sh
USAGE
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing env file: $ENV_FILE" >&2
  exit 1
fi

IMAGE_TAG_ARG="${1:-${IMAGE_TAG:-}}"
if [ -n "$IMAGE_TAG_ARG" ]; then
  if grep -q '^IMAGE_TAG=' "$ENV_FILE"; then
    tmp_file="$(mktemp)"
    awk -v tag="$IMAGE_TAG_ARG" '
      BEGIN { updated = 0 }
      /^IMAGE_TAG=/ { print "IMAGE_TAG=" tag; updated = 1; next }
      { print }
      END { if (updated == 0) print "IMAGE_TAG=" tag }
    ' "$ENV_FILE" > "$tmp_file"
    mv "$tmp_file" "$ENV_FILE"
  else
    printf '\nIMAGE_TAG=%s\n' "$IMAGE_TAG_ARG" >> "$ENV_FILE"
  fi
fi

set -a
# shellcheck disable=SC1090
. "$ENV_FILE"
set +a

if [ -z "${APP_BASE_URL:-}" ]; then
  echo "APP_BASE_URL is required in $ENV_FILE" >&2
  exit 1
fi

if [ -z "${IMAGE_REGISTRY:-}" ]; then
  echo "IMAGE_REGISTRY is required in $ENV_FILE" >&2
  exit 1
fi

if [ -z "${IMAGE_NAMESPACE:-}" ]; then
  echo "IMAGE_NAMESPACE is required in $ENV_FILE" >&2
  exit 1
fi

if [ -z "${IMAGE_TAG:-}" ] || [ "$IMAGE_TAG" = "local" ]; then
  echo "IMAGE_TAG must be set to an immutable production tag, for example sha-abc1234" >&2
  exit 1
fi

cd "$ROOT_DIR"

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" pull web api
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d db
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" run --rm api python -m alembic upgrade head
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d proxy web api
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps

curl -fsS "$APP_BASE_URL/v1/public/exams?page_size=1" >/dev/null
curl -fsS "$APP_BASE_URL/v1/public/exams/filters" >/dev/null

echo "Deploy completed for IMAGE_TAG=$IMAGE_TAG"
