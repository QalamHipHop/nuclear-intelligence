#!/usr/bin/env bash
set -Eeuo pipefail

# Reproducible installer for local development and Hugging Face Space parity.
# Secrets are never accepted as command-line arguments or written to disk.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-${ROOT_DIR}/.venv}"
REQUIREMENTS_FILE="${REQUIREMENTS_FILE:-${ROOT_DIR}/requirements.txt}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "Python executable not found: ${PYTHON_BIN}" >&2
  exit 1
fi

"${PYTHON_BIN}" -m venv "${VENV_DIR}"
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip setuptools wheel
python -m pip install --requirement "${REQUIREMENTS_FILE}"
python -m compileall -q "${ROOT_DIR}/core" "${ROOT_DIR}/scripts" "${ROOT_DIR}/api" "${ROOT_DIR}/tests"

echo "Installation complete. Activate with: source ${VENV_DIR}/bin/activate"
echo "Secrets must be supplied through environment variables or the deployment secret store."
