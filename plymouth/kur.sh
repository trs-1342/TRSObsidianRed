#!/bin/bash
# TRS Kare önyükleme ekranı — kurulum / geri alma. ROOT gerekir (önyükleme dosyasını yeniden üretir).
#   sudo bash kur.sh        kur / güncelle
#   sudo bash kur.sh geri   önceki temaya (Fedora'nın HP logolu ekranı) dön
#
# Güvenlik: yalnızca ÇALIŞAN çekirdeğin önyükleme dosyası (initramfs) değişir ve değişmeden önce yedeklenir.
# Diğer çekirdeklerin dosyalarına dokunulmaz; bir şey ters giderse açılış menüsünden eski çekirdek seçilir.
# Tema bozuk olsa bile disk parolası düz yazı ekranında sorulur, sistem açılır.
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "root gerekli: sudo bash $0 $*"; exit 1; }
KAYNAK=$(cd "$(dirname "$(readlink -f "$0")")" && pwd)/trs-kare
HEDEF=/usr/share/plymouth/themes/trs-kare
YEDEK=/var/lib/trs-yedek/plymouth
CEKIRDEK=$(uname -r)
INITRD=/boot/initramfs-$CEKIRDEK.img

if [ "${1:-}" = "geri" ]; then
  ONCEKI=$(cat "$YEDEK/onceki-tema" 2>/dev/null || echo bgrt)
  plymouth-set-default-theme -R "$ONCEKI"
  echo "Geri alındı: tema = $(plymouth-set-default-theme). Bir sonraki açılışta geçerli."
  exit 0
fi

# Hareketli sürüm (script eklentisi) ile yalın sürümün (two-step) dosyaları farklıdır
[ -s "$KAYNAK/trs-kare.plymouth" ] || { echo "kaynak eksik (önce: python3 uret.py)"; exit 1; }
if grep -q "^ModuleName=script" "$KAYNAK/trs-kare.plymouth"; then
  GEREKEN="trs-kare.plymouth trs-kare.script siyah.png kirmizi.png"
else
  GEREKEN="trs-kare.plymouth throbber-0001.png lock.png entry.png bullet.png"
fi
for f in $GEREKEN; do
  [ -s "$KAYNAK/$f" ] || { echo "kaynak eksik: $f (önce: python3 uret.py)"; exit 1; }
done
[ -s "$INITRD" ] || { echo "önyükleme dosyası bulunamadı: $INITRD"; exit 1; }

# Hareketli tema Plymouth'un "script" eklentisini ister (Fedora deposundan, küçük bir paket)
if grep -q "^ModuleName=script" "$KAYNAK/trs-kare.plymouth" && [ ! -e /usr/lib64/plymouth/script.so ]; then
  echo "plymouth-plugin-script kuruluyor..."
  dnf install -y plymouth-plugin-script
  [ -e /usr/lib64/plymouth/script.so ] || { echo "eklenti kurulamadı, hiçbir şey değiştirilmedi"; exit 1; }
fi

mkdir -p "$YEDEK"
SIMDIKI=$(plymouth-set-default-theme)
if [ "$SIMDIKI" != trs-kare ]; then
  echo "$SIMDIKI" > "$YEDEK/onceki-tema"
  cp -a "$INITRD" "$YEDEK/$(basename "$INITRD")"
  echo "yedek: $YEDEK/$(basename "$INITRD") (önceki tema: $SIMDIKI)"
fi

rm -rf "$HEDEF"
install -d -m 755 "$HEDEF"
install -m 644 "$KAYNAK"/* "$HEDEF/"

plymouth-set-default-theme -R trs-kare

# Doğrulama: yeni dosyada tema var mı? Yoksa yedeği geri koy.
# (Liste önce değişkene alınır: "lsinitrd | grep -q" pipefail altında, grep erken çıkınca yanlış hata verir.)
ICERIK=$(lsinitrd "$INITRD" 2>/dev/null || true)
EKLENTI=$(sed -n 's/^ModuleName=//p' "$HEDEF/trs-kare.plymouth")
TAMAM=evet
for f in $GEREKEN; do
  grep -q "plymouth/themes/trs-kare/$f" <<<"$ICERIK" || TAMAM=hayir
done
grep -q "plymouth/$EKLENTI.so" <<<"$ICERIK" || TAMAM=hayir
if [ "$TAMAM" = evet ]; then
  echo "Kuruldu ve doğrulandı: $INITRD içinde trs-kare var. Bir sonraki açılışta geçerli."
  echo "Geri alma: sudo bash $0 geri"
else
  echo "DOĞRULAMA BAŞARISIZ: tema önyükleme dosyasına girmemiş, geri alınıyor."
  echo "--- dosyadaki plymouth girdileri (teşhis) ---"
  grep -iE "plymouth/themes|plymouth/[a-z-]+\.so" <<<"$ICERIK" | head -14 || true
  echo "liste satır sayısı: $(wc -l <<<"$ICERIK")"
  if [ -s "$YEDEK/$(basename "$INITRD")" ]; then
    cp -a "$YEDEK/$(basename "$INITRD")" "$INITRD"
    plymouth-set-default-theme "$(cat "$YEDEK/onceki-tema")"
    echo "Önyükleme dosyası yedekten geri kondu."
  fi
  exit 1
fi
