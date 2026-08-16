#!/usr/bin/env sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env}"
COMPOSE_FILE="${COMPOSE_FILE:-$ROOT_DIR/compose.yml}"
AWS_CLI_IMAGE="${AWS_CLI_IMAGE:-amazon/aws-cli:2.17.37}"
BACKUP_TZ="${BACKUP_TZ:-Asia/Ho_Chi_Minh}"

usage() {
  cat <<'USAGE'
Usage:
  scripts/backup-postgres.sh

Required .env values:
  POSTGRES_DB
  POSTGRES_USER
  R2_ACCOUNT_ID
  R2_ACCESS_KEY_ID
  R2_SECRET_ACCESS_KEY
  R2_BACKUP_BUCKET

Optional environment:
  ENV_FILE       Path to the VPS .env file. Defaults to ./.env.
  COMPOSE_FILE   Path to compose.yml. Defaults to ./compose.yml.
  AWS_CLI_IMAGE  AWS CLI container image. Defaults to amazon/aws-cli:2.17.37.
  BACKUP_TZ      Timestamp timezone. Defaults to Asia/Ho_Chi_Minh.
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

set -a
# shellcheck disable=SC1090
. "$ENV_FILE"
set +a

required_vars="POSTGRES_DB POSTGRES_USER R2_ACCOUNT_ID R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY R2_BACKUP_BUCKET"
for var_name in $required_vars; do
  eval "var_value=\${$var_name:-}"
  if [ -z "$var_value" ]; then
    echo "$var_name is required in $ENV_FILE" >&2
    exit 1
  fi
done

timestamp="$(TZ="$BACKUP_TZ" date +%Y%m%dT%H%M%S)"
year="$(TZ="$BACKUP_TZ" date +%Y)"
month="$(TZ="$BACKUP_TZ" date +%m)"
dump_file="diem10-${timestamp}.dump"
object_key="postgres/${year}/${month}/${dump_file}"
backup_dir="$(mktemp -d)"

cleanup() {
  rm -rf "$backup_dir"
}
trap cleanup EXIT INT TERM

cd "$ROOT_DIR"

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T db \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > "$backup_dir/$dump_file"

docker run --rm \
  -e AWS_ACCESS_KEY_ID="$R2_ACCESS_KEY_ID" \
  -e AWS_SECRET_ACCESS_KEY="$R2_SECRET_ACCESS_KEY" \
  -e AWS_DEFAULT_REGION=auto \
  -v "$backup_dir:/backup:ro" \
  "$AWS_CLI_IMAGE" \
  s3 cp "/backup/$dump_file" "s3://$R2_BACKUP_BUCKET/$object_key" \
  --endpoint-url "https://$R2_ACCOUNT_ID.r2.cloudflarestorage.com"

echo "Uploaded postgres backup to s3://$R2_BACKUP_BUCKET/$object_key"
