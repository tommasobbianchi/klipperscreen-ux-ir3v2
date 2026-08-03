#!/bin/bash
# Install the u1 KlipperScreen theme onto a device.
# Seeds images/ from the stock material-dark theme (so icons resolve), then overlays
# this theme's style.css + style.conf. Sets theme=u1 surgically in KlipperScreen.conf,
# preserving every other setting/macro. Idempotent.
#
# Usage (run ON the device, or over ssh):  bash install.sh [KS_DIR] [CONF]
set -euo pipefail
KS="${1:-$HOME/KlipperScreen}"
CONF="${2:-$HOME/printer_data/config/KlipperScreen.conf}"
SRC="$(cd "$(dirname "$0")" && pwd)"

dst="$KS/styles/u1"
mkdir -p "$dst/images"
# seed icons from the stock theme, don't clobber our overlays
cp -rn "$KS/styles/material-dark/images/." "$dst/images/" 2>/dev/null || true
cp -f "$SRC/style.css" "$dst/style.css"
cp -f "$SRC/style.conf" "$dst/style.conf"
echo "theme files in $dst"

# flip theme to u1 in the auto-generated [main] block, nothing else
if grep -qE '^\s*#~#\s*theme\s*=' "$CONF"; then
  sed -i -E 's|^(\s*#~#\s*theme\s*=\s*).*$|\1u1|' "$CONF"
  echo "theme set to u1 in $CONF"
else
  echo "WARN: no '#~# theme =' line found in $CONF — set theme=u1 manually" >&2
fi
grep -nE '^\s*#~#\s*theme\s*=' "$CONF" || true
