#!/bin/bash
# Deploy the ux reflows + theme onto an IdeaFormer IR3 V2 running the JansenCXM
# KlipperScreen fork. Idempotent: the first run saves each stock file as <name>.stock
# and later runs never overwrite those, so revert always lands on the true original.
#
# Usage (run ON the device, or over ssh):  bash deploy.sh [KS_DIR] [CONF]
set -euo pipefail
KS="${1:-$HOME/KlipperScreen}"
CONF="${2:-$HOME/printer_data/config/KlipperScreen.conf}"
SRC="$(cd "$(dirname "$0")" && pwd)"

[ -d "$KS/panels" ] || { echo "✗ no KlipperScreen at $KS" >&2; exit 1; }

# repo file -> path under $KS.  panel_<name>.py maps to panels/<name>.py, except
# panel_base.py which replaces the chrome (panels/base_panel.py).
deploy() {
  local src="$SRC/$1" dst="$KS/$2"
  [ -f "$src" ] || { echo "✗ missing $1" >&2; return 1; }
  [ -f "$dst" ] && [ ! -f "$dst.stock" ] && cp "$dst" "$dst.stock" && echo "  saved $2.stock"
  cp -f "$src" "$dst"
  echo "  $1 -> $2"
}

echo "▶ panels"
deploy panel_base.py       panels/base_panel.py
for n in extrude fine_tune gcodes job_status limits main_menu menu move network temperature; do
  deploy "panel_$n.py" "panels/$n.py"
done

echo "▶ widgets + menu tree"
deploy ks_includes/KlippyGtk.py ks_includes/KlippyGtk.py
deploy config/main_menu.conf    config/main_menu.conf

echo "▶ theme"
bash "$SRC/styles/ux/install.sh" "$KS" "$CONF"

echo "▶ restart"
sudo systemctl restart KlipperScreen && echo "✓ deployed"
