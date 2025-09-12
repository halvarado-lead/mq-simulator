#!/usr/bin/env bash
set -euo pipefail

# Ejecuta mq_consumer.py fuera de Docker
# Requisitos (Linux x86_64):
#  - Cliente IBM MQ instalado en /opt/mqm (usa scripts/install_mq_client_debian.sh)
#  - Python 3 y pip disponibles

OS=$(uname -s)
ARCH=$(uname -m)

if [[ "$OS" == "Darwin" ]]; then
  echo "Advertencia: macOS no tiene cliente IBM MQ nativo. Usa Docker o una VM Linux." >&2
  echo "Puedes seguir con SEND_MODE=print, pero no conectará a MQ." >&2
fi

if [[ "$OS" == "Linux" && ! -d "/opt/mqm/lib64" ]]; then
  echo "No encuentro /opt/mqm/lib64. Instala el cliente IBM MQ primero:" >&2
  echo "  bash scripts/install_mq_client_debian.sh" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "$0")"/.. && pwd)"
cd "$ROOT_DIR"

python3 -m venv .venv || true
source .venv/bin/activate
pip install --quiet --no-cache-dir pymqi

export LD_LIBRARY_PATH=${LD_LIBRARY_PATH:-/opt/mqm/lib64:/opt/mqm/lib}

# Variables por defecto (puedes sobreescribirlas al invocar el script)
export MQ_QMGR_NAME=${MQ_QMGR_NAME:-AUTORIZA}
export MQ_CHANNEL=${MQ_CHANNEL:-DEV.APP.SVRCONN}
export MQ_HOST=${MQ_HOST:-localhost}
export MQ_PORT=${MQ_PORT:-1414}
export MQ_QUEUE=${MQ_QUEUE:-BOFTD_ENV}
export MQ_USER=${MQ_USER:-app}
export MQ_PASSWORD=${MQ_PASSWORD:-passw0rd}

echo "Conectando a MQ $MQ_QMGR_NAME@$MQ_HOST:$MQ_PORT canal $MQ_CHANNEL cola $MQ_QUEUE ..."
python mq_consumer.py

