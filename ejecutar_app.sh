#!/usr/bin/env bash
# Dashboard Catálogo Sísmico del Perú 1960–2025 · macOS / Linux (requiere Python 3.10+)
set -e
cd "$(dirname "$0")"
PY=$(command -v python3 || command -v python)
[ -z "$PY" ] && { echo "No se encontró Python 3."; exit 1; }
if [ ! -x .venv/bin/python ]; then
  "$PY" -m venv .venv
  .venv/bin/python -m pip install --upgrade pip >/dev/null
  .venv/bin/python -m pip install -r requirements.txt
fi
.venv/bin/python -m streamlit run app.py --server.port 8501 --server.headless false
