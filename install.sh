#!/usr/bin/env bash
# ─── NativeUI KlipperScreen Theme Installer ───────────────────
# by Native Ricerca — nativericerca.com
set -e

THEME_NAME="nativeui"
KS_STYLES="${HOME}/KlipperScreen/styles"

echo "▶  NativeUI KlipperScreen Theme Installer"
echo "   Destinazione: ${KS_STYLES}/${THEME_NAME}"

# Verifica che KlipperScreen sia installato
if [ ! -d "${KS_STYLES}" ]; then
  echo "✗  Errore: cartella KlipperScreen/styles non trovata in ${HOME}"
  echo "   Assicurati che KlipperScreen sia installato."
  exit 1
fi

# Backup tema esistente se già presente
if [ -d "${KS_STYLES}/${THEME_NAME}" ]; then
  BACKUP="${KS_STYLES}/${THEME_NAME}.bak.$(date +%Y%m%d%H%M%S)"
  echo "⚠  Tema esistente trovato — backup in: ${BACKUP}"
  cp -r "${KS_STYLES}/${THEME_NAME}" "${BACKUP}"
fi

# Copia il tema
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -r "${SCRIPT_DIR}/${THEME_NAME}" "${KS_STYLES}/"
echo "✓  Tema copiato in ${KS_STYLES}/${THEME_NAME}"

# Restart KlipperScreen
if systemctl is-active --quiet KlipperScreen; then
  sudo systemctl restart KlipperScreen
  echo "✓  KlipperScreen riavviato"
else
  echo "ℹ  KlipperScreen non attivo — avvia manualmente o riavvia il sistema"
fi

echo ""
echo "✅ Installazione completata!"
echo "   → Vai su KlipperScreen › Impostazioni › Tema › NativeUI"
