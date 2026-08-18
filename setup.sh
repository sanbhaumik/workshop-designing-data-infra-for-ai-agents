#!/usr/bin/env bash
# NovaBridge workshop — one-shot environment setup.
#
# Provisions everything the labs need on a Debian/Ubuntu box (Google Colab or
# GitHub Codespaces): Python deps, a local Postgres, and Ollama with the model.
# Idempotent — safe to re-run after a Colab disconnect.
#
# Usage:  bash setup.sh
# Then:   export DATABASE_URL=postgresql://postgres@localhost:5432/nova
#         export NOVA_LLM=ollama
set -euo pipefail

MODEL="${OLLAMA_MODEL:-llama3.2:1b}"
PGPORT="${PGPORT:-5432}"
DB_NAME="${DB_NAME:-nova}"
# SKIP_OLLAMA=1 provisions the participant path: real Postgres + recorded model
# fixtures (NOVA_LLM=frozen), skipping the slow Ollama install and model pull.
# The facilitator runs the full setup (live model) by leaving SKIP_OLLAMA unset.
SKIP_OLLAMA="${SKIP_OLLAMA:-0}"

echo "==> [1/5] Python dependencies"
pip install -q -r requirements.txt

echo "==> [2/5] Postgres server"
if ! command -v psql >/dev/null 2>&1; then
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq postgresql postgresql-contrib >/dev/null
fi
# Start the default cluster (Debian packages ship one). Works as root (Colab) or
# via sudo (Codespaces). Ignore "already running".
if command -v pg_ctlcluster >/dev/null 2>&1; then
  PG_VER="$(ls /etc/postgresql 2>/dev/null | head -1)"
  (sudo -n pg_ctlcluster "${PG_VER}" main start 2>/dev/null \
    || pg_ctlcluster "${PG_VER}" main start 2>/dev/null \
    || service postgresql start 2>/dev/null) || true
else
  (service postgresql start 2>/dev/null) || true
fi

echo "==> [3/5] Postgres role + database ('${DB_NAME}')"
# Run SQL as the postgres OS user; create a trust-auth 'postgres' login role and
# the nova database if they don't exist.
run_pg() { (sudo -n -u postgres psql -p "${PGPORT}" -tc "$1" 2>/dev/null \
          || su -c "psql -p ${PGPORT} -tc \"$1\"" postgres 2>/dev/null) || true; }
run_pg "ALTER ROLE postgres WITH LOGIN;"
if ! run_pg "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}';" | grep -q 1; then
  run_pg "CREATE DATABASE ${DB_NAME};"
fi

if [ "$SKIP_OLLAMA" = "1" ]; then
  echo "==> [4/4] Skipping Ollama (participant path: recorded fixtures, NOVA_LLM=frozen)"
  echo
  echo "======================================================================"
  echo "  ✅ SETUP COMPLETE (participant path). Next:"
  echo "     export DATABASE_URL=postgresql://postgres@localhost:${PGPORT}/${DB_NAME}"
  echo "     export NOVA_LLM=frozen"
  echo "     python preflight.py     # expect a GREEN banner"
  echo "======================================================================"
  exit 0
fi

echo "==> [4/5] Ollama"
if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.com/install.sh | sh
fi
# Start the server in the background if it isn't answering yet.
if ! curl -fsS "http://localhost:11434/api/version" >/dev/null 2>&1; then
  nohup ollama serve >/tmp/ollama_serve.log 2>&1 &
  for _ in $(seq 1 30); do
    curl -fsS "http://localhost:11434/api/version" >/dev/null 2>&1 && break
    sleep 1
  done
fi

echo "==> [5/5] Pull model '${MODEL}' (this is the slow step on first run)"
ollama pull "${MODEL}"

echo
echo "======================================================================"
echo "  ✅ SETUP COMPLETE (facilitator path). Next:"
echo "     export DATABASE_URL=postgresql://postgres@localhost:${PGPORT}/${DB_NAME}"
echo "     export NOVA_LLM=ollama"
echo "     export OLLAMA_MODEL=${MODEL}"
echo "     python preflight.py     # expect a GREEN banner"
echo "======================================================================"
