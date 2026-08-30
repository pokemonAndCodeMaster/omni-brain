#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PG_BIN="/usr/lib/postgresql/16/bin"
RUNTIME="$ROOT/.runtime/postgres"
DATA="$RUNTIME/data"
SOCKET="$RUNTIME/socket"
LOG_DIR="$RUNTIME/log"
LOG_FILE="$LOG_DIR/postgres.log"
TCP_MARKER="$RUNTIME/tcp.enabled"
TCP_HBA="$RUNTIME/pg_hba_tcp.conf"
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
  local listen_addresses=""
  local options
  if [[ -f "$TCP_MARKER" ]]; then
    listen_addresses="127.0.0.1"
  fi
  options="-c listen_addresses='$listen_addresses' -c unix_socket_directories='$SOCKET' -p $PORT"
  if [[ -f "$TCP_MARKER" ]]; then
    options="$options -c hba_file='$TCP_HBA'"
  fi
  "$PG_BIN/pg_ctl" \
    -D "$DATA" \
    -l "$LOG_FILE" \
    -o "$options" \
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
      if [[ -f "$TCP_MARKER" ]]; then
        echo "quality_lab PostgreSQL is ready: socket=$SOCKET tcp=127.0.0.1:$PORT database=$DATABASE"
      else
        echo "quality_lab PostgreSQL is ready: socket=$SOCKET tcp=disabled database=$DATABASE"
      fi
    else
      echo "quality_lab PostgreSQL is not ready"
      exit 1
    fi
    ;;
  enable-tcp)
    if [[ ! -f "$DATA/PG_VERSION" ]]; then
      echo "数据库尚未初始化，请先执行 scripts/postgres.sh init" >&2
      exit 1
    fi
    if [[ -z "${QC_DB_PASSWORD:-}" ]]; then
      echo "请通过 QC_DB_PASSWORD 提供 Navicat 本地连接密码；脚本不会把密码写入文件。" >&2
      exit 2
    fi
    if [[ ! "$USER_NAME" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
      echo "QC_DB_USER 不是安全的 PostgreSQL 标识符：$USER_NAME" >&2
      exit 2
    fi
    start_cluster
    printf '%s\n' "ALTER ROLE \"$USER_NAME\" PASSWORD :'role_password';" |
      "$PG_BIN/psql" \
      -h "$SOCKET" \
      -p "$PORT" \
      -U "$USER_NAME" \
      -d postgres \
      --set=role_password="$QC_DB_PASSWORD"
    umask 077
    {
      printf '%s\n' "local all all trust"
      printf '%s\n' "host $DATABASE $USER_NAME 127.0.0.1/32 scram-sha-256"
      printf '%s\n' "host all all 0.0.0.0/0 reject"
      printf '%s\n' "host all all ::0/0 reject"
    } > "$TCP_HBA"
    : > "$TCP_MARKER"
    "$PG_BIN/pg_ctl" -D "$DATA" -m fast -w stop
    start_cluster
    PGPASSWORD="$QC_DB_PASSWORD" "$PG_BIN/psql" \
      -h 127.0.0.1 \
      -p "$PORT" \
      -U "$USER_NAME" \
      -d "$DATABASE" \
      -Atqc "SELECT current_database(), current_user"
    echo "Navicat: host=127.0.0.1 port=$PORT database=$DATABASE user=$USER_NAME"
    ;;
  disable-tcp)
    if [[ ! -f "$DATA/PG_VERSION" ]]; then
      echo "数据库尚未初始化" >&2
      exit 1
    fi
    if is_ready; then
      "$PG_BIN/pg_ctl" -D "$DATA" -m fast -w stop
    fi
    rm -f "$TCP_MARKER" "$TCP_HBA"
    start_cluster
    echo "已关闭 TCP；项目仍可通过 Unix socket 访问数据库。"
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
    echo "用法：scripts/postgres.sh {init|start|stop|status|enable-tcp|disable-tcp|reset}" >&2
    exit 2
    ;;
esac
