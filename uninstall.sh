#!/usr/bin/env bash
# TRS Obsidian Red — uninstaller
# Removes ONLY the files this project installed and restores the previous
# color scheme / widget style. Does not touch other themes or system files.
set -euo pipefail

THEME=TRSObsidianRed
COLORS_DST="$HOME/.local/share/color-schemes"
KV_DST="$HOME/.config/Kvantum"
BACKUP_ROOT="$HOME/.local/share/trs-theme-backup"
STATE="$BACKUP_ROOT/last-state.txt"

say()  { printf '\033[1;32m[uninstall]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[uyarı]\033[0m %s\n' "$*"; }

# --- previous state ---------------------------------------------------------
PREV_SCHEME=BreezeDark
PREV_STYLE=Breeze
if [[ -f "$STATE" ]]; then
  # shellcheck disable=SC1090
  PREV_SCHEME=$(grep -oP '(?<=^scheme=).*' "$STATE" || echo BreezeDark)
  PREV_STYLE=$(grep -oP '(?<=^style=).*' "$STATE" || echo Breeze)
  say "Kayıtlı önceki durum: scheme=$PREV_SCHEME style=$PREV_STYLE"
else
  warn "Kayıtlı durum yok; varsayılan BreezeDark/Breeze'e dönülüyor."
fi

# --- restore settings -------------------------------------------------------
if command -v plasma-apply-colorscheme >/dev/null; then
  plasma-apply-colorscheme "$PREV_SCHEME" || warn "Renk şeması geri yüklenemedi: $PREV_SCHEME"
  say "Renk şeması geri yüklendi: $PREV_SCHEME"
fi
if command -v kwriteconfig6 >/dev/null; then
  if [[ -n "$PREV_STYLE" ]]; then
    kwriteconfig6 --notify --file kdeglobals --group KDE --key widgetStyle "$PREV_STYLE"
  else
    kwriteconfig6 --notify --file kdeglobals --group KDE --key widgetStyle --delete
  fi
  say "Widget stili geri yüklendi: ${PREV_STYLE:-varsayılan}"
fi
# clear Kvantum selection only if it points at our theme
if grep -qs "theme=$THEME" "$KV_DST/kvantum.kvconfig" 2>/dev/null; then
  sed -i "s/^theme=$THEME\$/theme=/" "$KV_DST/kvantum.kvconfig"
  say "Kvantum tema seçimi temizlendi."
fi

# --- remove only our files --------------------------------------------------
for f in "$COLORS_DST/$THEME.colors"; do
  [[ -f "$f" ]] && { rm -v "$f"; say "Silindi: $f"; }
done
if [[ -d "$KV_DST/$THEME" ]]; then
  rm -rf "$KV_DST/$THEME"
  say "Silindi: $KV_DST/$THEME/"
fi
[[ -f "$STATE" ]] && rm -f "$STATE"

say "Tamamlandı. Açık uygulamalar yeniden başlatılınca eski görünüme döner."
say "Yedekler duruyor: $BACKUP_ROOT/ (proje dosyaları da ~/Projects/TRSObsidianRed/ altında korunuyor)"
