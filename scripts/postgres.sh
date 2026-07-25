#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PG_BIN="/usr/lib/postgresql/16/bin"
RUNTIME="$ROOT/.runtime/postgres"
DATA="$RUNTIME/data"
SOCKET="$RUNTIME/socket"
LOG_DIR="$RUNTIME/log"
LOG_FILE="$LOG_DIR/postgres.log"
PORT="${QC_DB_PORT:-55432}"
USER_NAME="${QC_DB_USER:-quality_lab}"
DATABASE="${QC_DB_NAME:-quality_lab}"

mkdir -p "$RUNTIME" "$SOCKET" "$LOG_DIR"
chmod 700 "$RUNTIME" "$SOCKET" "$LOG_DIR"

is_ready() {
  "$PG_BIN/pg_isready" -h "$SOCKET" -p "$PORT" -U "$USER_NAME" -d "$DATABASE" >/dev/null 2>&1
}

start_cluster() {
  if is_ready; then
    return
  fi
  "$PG_BIN/pg_ctl" \
    -D "$DATA" \
    -l "$LOG_FILE" \
    -o "-c listen_addresses='' -c unix_socket_directories='$SOCKET' -p $PORT" \
    -w start
}

case "${1:-status}" in
  init)
    if [[ ! -f "$DATA/PG_VERSION" ]]; then
      "$PG_BIN/initdb" \
        -D "$DATA" \
        -U "$USER_NAME" \
        --encoding=UTF8 \
        --locale=C.UTF-8 \
        --auth-local=trust \
        --auth-host=reject
    fi
    start_cluster
    if ! "$PG_BIN/psql" -h "$SOCKET" -p "$PORT" -U "$USER_NAME" -d postgres -Atqc \
      "SELECT 1 FROM pg_database WHERE datname = '$DATABASE'" | grep -q 1; then
      "$PG_BIN/createdb" -h "$SOCKET" -p "$PORT" -U "$USER_NAME" "$DATABASE"
    fi
    "$PG_BIN/pg_isready" -h "$SOCKET" -p "$PORT" -U "$USER_NAME" -d "$DATABASE"
    ;;
  start)
    if [[ ! -f "$DATA/PG_VERSION" ]]; then
      echo "数据库尚未初始化，请先执行 scripts/postgres.sh init" >&2
      exit 1
    fi
    start_cluster
    "$PG_BIN/pg_isready" -h "$SOCKET" -p "$PORT" -U "$USER_NAME" -d "$DATABASE"
    ;;
  stop)
    if [[ -f "$DATA/PG_VERSION" ]]; then
      "$PG_BIN/pg_ctl" -D "$DATA" -m fast -w stop
    fi
    ;;
  status)
    if is_ready; then
      echo "quality_lab PostgreSQL is ready: socket=$SOCKET port=$PORT database=$DATABASE"
    else
      echo "quality_lab PostgreSQL is not ready"
      exit 1
    fi
    ;;
  reset)
    if [[ "${RESET_QUALITY_LAB:-}" != "yes" ]]; then
      echo "该操作会删除全部实验数据。确认时使用 RESET_QUALITY_LAB=yes scripts/postgres.sh reset" >&2
      exit 2
    fi
    if [[ -f "$DATA/PG_VERSION" ]]; then
      "$PG_BIN/pg_ctl" -D "$DATA" -m fast -w stop || true
    fi
    rm -rf "$RUNTIME"
    echo "已删除 $RUNTIME"
    ;;
  *)
    echo "用法：scripts/postgres.sh {init|start|stop|status|reset}" >&2
    exit 2
    ;;
esac
