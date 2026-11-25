#!/bin/sh
# Installs the PibbyGlitchCursor cursor theme for the current user and selects it.
set -e
cd "$(dirname "$0")"
mkdir -p "$HOME/.icons"
rm -rf "$HOME/.icons/PibbyGlitchCursor"
tar -xzf PibbyGlitchCursor.tar.gz -C "$HOME/.icons"
mkdir -p "$HOME/.icons/default"
printf '[Icon Theme]\nInherits=PibbyGlitchCursor\n' > "$HOME/.icons/default/index.theme"
if command -v gsettings >/dev/null 2>&1; then
  gsettings set org.gnome.desktop.interface cursor-theme 'PibbyGlitchCursor' 2>/dev/null || true
fi
if command -v plasma-apply-cursortheme >/dev/null 2>&1; then
  plasma-apply-cursortheme PibbyGlitchCursor || true
fi
echo "Installed PibbyGlitchCursor. Log out and back in if some apps still show the old cursor."
