#!/usr/bin/env bash
# TRS Obsidian Red — installer (idempotent)
# Installs the KDE color scheme + Kvantum theme into user directories and
# activates them. Never touches system files, never installs packages.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THEME=TRSObsidianRed
COLORS_SRC="$PROJECT_DIR/color-scheme/$THEME.colors"
KV_SRC="$PROJECT_DIR/kvantum/$THEME"
COLORS_DST="$HOME/.local/share/color-schemes"
KV_DST="$HOME/.config/Kvantum"
BACKUP_ROOT="$HOME/.local/share/trs-theme-backup"
STATE="$BACKUP_ROOT/last-state.txt"

say()  { printf '\033[1;32m[install]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[uyarı]\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m[hata]\033[0m %s\n' "$*" >&2; exit 1; }

[[ -f "$COLORS_SRC" ]] || die "Kaynak bulunamadı: $COLORS_SRC"
[[ -f "$KV_SRC/$THEME.kvconfig" && -f "$KV_SRC/$THEME.svg" ]] \
  || die "Kvantum tema dosyaları eksik: $KV_SRC"

# --- dependency checks (report only, never install) -------------------------
missing=()
for cmd in kvantummanager plasma-apply-colorscheme kwriteconfig6 kreadconfig6; do
  command -v "$cmd" >/dev/null || missing+=("$cmd")
done
if ((${#missing[@]})); then
  warn "Eksik komutlar: ${missing[*]}"
  warn "Fedora paketleri: kvantum (kvantummanager), plasma-workspace (plasma-apply-colorscheme), kf6-kconfig"
  die  "Bağımlılıklar eksik; paket kurulumu kullanıcı onayı gerektirir, betik kurmaz."
fi

# --- backup current settings + any previous copy of this theme --------------
TS=$(date +%F_%H-%M-%S)
BK="$BACKUP_ROOT/$TS"
mkdir -p "$BK"
cp -a "$HOME/.config/kdeglobals" "$BK/" 2>/dev/null || true
cp -a "$KV_DST/kvantum.kvconfig" "$BK/" 2>/dev/null || true
[[ -f "$COLORS_DST/$THEME.colors" ]] && cp -a "$COLORS_DST/$THEME.colors" "$BK/"
[[ -d "$KV_DST/$THEME" ]] && cp -a "$KV_DST/$THEME" "$BK/kvantum-$THEME"
say "Yedek: $BK"

# --- remember pre-theme state once (used by uninstall) ----------------------
CUR_SCHEME=$(kreadconfig6 --file kdeglobals --group General --key ColorScheme || true)
CUR_STYLE=$(kreadconfig6 --file kdeglobals --group KDE --key widgetStyle || true)
if [[ ! -f "$STATE" && "$CUR_SCHEME" != "$THEME" ]]; then
  mkdir -p "$BACKUP_ROOT"
  printf 'scheme=%s\nstyle=%s\n' "${CUR_SCHEME:-BreezeDark}" "${CUR_STYLE:-Breeze}" > "$STATE"
  say "Önceki durum kaydedildi: $STATE (scheme=$CUR_SCHEME, style=$CUR_STYLE)"
fi

# --- install ----------------------------------------------------------------
mkdir -p "$COLORS_DST" "$KV_DST/$THEME"
cp -f "$COLORS_SRC" "$COLORS_DST/"
cp -f "$KV_SRC/$THEME.kvconfig" "$KV_SRC/$THEME.svg" "$KV_DST/$THEME/"
say "Renk şeması  -> $COLORS_DST/$THEME.colors"
say "Kvantum tema -> $KV_DST/$THEME/"

# --- activate ---------------------------------------------------------------
kvantummanager --set "$THEME"
say "Kvantum teması seçildi: $THEME"
plasma-apply-colorscheme "$THEME" || warn "plasma-apply-colorscheme başarısız; System Settings → Colors üzerinden seçin."
kwriteconfig6 --notify --file kdeglobals --group KDE --key widgetStyle kvantum
say "Widget stili: kvantum (kdeglobals)"

say "Tamamlandı. Açık uygulamalar yeniden başlatılınca yeni stili alır."
say "Geri almak için: $PROJECT_DIR/uninstall.sh"
