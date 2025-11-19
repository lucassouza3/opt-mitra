#!/usr/bin/env bash
set -euo pipefail

if ! command -v poetry >/dev/null 2>&1; then
  echo 'Poetry não encontrado. Instale antes de continuar.'
  exit 1
fi

poetry install
poetry run pre-commit install || true
