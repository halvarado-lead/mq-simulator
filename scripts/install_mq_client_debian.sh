#!/usr/bin/env bash
set -euo pipefail

# Instala IBM MQ Client desde los .deb locales (Debian/Ubuntu x86_64)
# Requiere sudo y que existan los .deb en ./Client

if [[ $(uname -s) != "Linux" ]]; then
  echo "Este instalador es solo para Linux (Debian/Ubuntu)." >&2
  exit 1
fi

if ! command -v sudo >/dev/null 2>&1; then
  echo "Se requiere 'sudo' para instalar paquetes." >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "$0")"/.. && pwd)"
cd "$ROOT_DIR"

for f in \
  Client/ibmmq-runtime_9.3.0.0_amd64.deb \
  Client/ibmmq-gskit_9.3.0.0_amd64.deb \
  Client/ibmmq-client_9.3.0.0_amd64.deb \
  Client/ibmmq-sdk_9.3.0.0_amd64.deb
do
  if [[ ! -f "$f" ]]; then
    echo "Falta el archivo: $f" >&2
    exit 1
  fi
done

echo "Instalando dependencias del sistema..."
sudo apt-get update
sudo apt-get install -y ./Client/ibmmq-runtime_9.3.0.0_amd64.deb \
                        ./Client/ibmmq-gskit_9.3.0.0_amd64.deb \
                        ./Client/ibmmq-client_9.3.0.0_amd64.deb \
                        ./Client/ibmmq-sdk_9.3.0.0_amd64.deb

echo "Listo. Exporta estas variables en tu sesión si hace falta:"
echo "  export LD_LIBRARY_PATH=/opt/mqm/lib64:/opt/mqm/lib"
echo "  export PATH=\$PATH:/opt/mqm/bin"

