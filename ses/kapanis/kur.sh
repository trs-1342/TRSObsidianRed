#!/bin/bash
# Kapanış sesini kapanış animasyonuna bağlar. ROOT gerekir.
#   sudo bash kur.sh        kur / güncelle
#   sudo bash kur.sh geri   kaldır (ses yeniden kapanma isteği anında, oturum içinden çalar)
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "root gerekli: sudo bash $0 $*"; exit 1; }
KAYNAK=$(cd "$(dirname "$(readlink -f "$0")")" && pwd)
if [ "${1:-}" = "geri" ]; then
  systemctl disable trs-kapanis-sesi.service 2>/dev/null || true
  rm -f /etc/systemd/system/trs-kapanis-sesi.service /usr/local/libexec/trs-kapanis-sesi /usr/local/share/trs/kapanis.wav
  systemctl daemon-reload
  echo "Kaldırıldı."
  exit 0
fi
for f in kapanis.wav trs-kapanis-sesi-kok trs-kapanis-sesi.service; do
  [ -s "$KAYNAK/$f" ] || { echo "kaynak eksik: $f"; exit 1; }
done
install -d -m 755 /usr/local/libexec /usr/local/share/trs
install -m 755 -o root -g root "$KAYNAK/trs-kapanis-sesi-kok" /usr/local/libexec/trs-kapanis-sesi
install -m 644 -o root -g root "$KAYNAK/kapanis.wav" /usr/local/share/trs/kapanis.wav
install -m 644 -o root -g root "$KAYNAK/trs-kapanis-sesi.service" /etc/systemd/system/trs-kapanis-sesi.service
restorecon -R /usr/local/libexec/trs-kapanis-sesi /usr/local/share/trs /etc/systemd/system/trs-kapanis-sesi.service 2>/dev/null || true
systemctl daemon-reload
systemctl enable trs-kapanis-sesi.service
echo "Kuruldu. Bir sonraki kapatma ya da yeniden başlatmada ses kapanış animasyonuyla birlikte çalar."
echo "Geri alma: sudo bash $0 geri"
