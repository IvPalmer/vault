#!/bin/bash
# Sync medical report from health repo to vault public/
# Run this whenever the relatorio HTML is updated in the health repo
set -e

HEALTH="$HOME/Work/Dev/health/RELATORIO_PARA_MEDICO.html"
VAULT="$HOME/Work/Dev/vault/public/relatorio-palmer.html"

if [[ ! -f "$HEALTH" ]]; then
  echo "ERROR: source not found: $HEALTH"
  exit 1
fi

cp "$HEALTH" "$VAULT"
echo "synced: $HEALTH -> $VAULT"
echo "size: $(wc -c < $VAULT) bytes"
