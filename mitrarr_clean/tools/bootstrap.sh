#!/usr/bin/env bash
set -euo pipefail

if [ -d ".venv" ]; then
  . .venv/Scripts/activate >/dev/null 2>&1 || . .venv/bin/activate
else
  python -m venv .venv
  . .venv/Scripts/activate >/dev/null 2>&1 || . .venv/bin/activate
fi

pip install --upgrade pip
pip install -r requirements-dev.txt
