#!/usr/bin/env bash
# Install pollar-ticker for current user (pipx preferred, venv fallback). Adds app menu entry.
set -euo pipefail
cd "$(dirname "$0")"
if command -v pipx >/dev/null; then
  pipx install --force .
else
  python3 -m venv "$HOME/.local/share/pollar-ticker-venv"
  "$HOME/.local/share/pollar-ticker-venv/bin/pip" install .
  mkdir -p "$HOME/.local/bin"
  ln -sf "$HOME/.local/share/pollar-ticker-venv/bin/pollar-ticker" "$HOME/.local/bin/pollar-ticker"
fi
mkdir -p "$HOME/.local/share/applications"
cp data/pollar-ticker.desktop "$HOME/.local/share/applications/"
mkdir -p "$HOME/.local/share/icons/hicolor/scalable/apps"
cp data/pollar-ticker.svg "$HOME/.local/share/icons/hicolor/scalable/apps/"
gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
echo "Installed. Run: pollar-ticker   (ensure ~/.local/bin is in PATH)"
