# Sistem Analizi — 2026-07-18

| Bileşen | Değer |
|---|---|
| Fedora | 44 |
| Plasma | 6.7.3 (Wayland) |
| Qt | 6.11.1 (Qt5: qt5-qtbase 5.15.18 mevcut, az sayıda KF5 kütüphanesi) |
| Kvantum | 1.1.6 — yalnızca Qt6 eklentisi kurulu; `kvantum-qt5` depoda var, kurulu değil |
| qt5ct / qt6ct | kurulu değil (gerekmez; Plasma platform teması yönetiyor) |
| QT_QPA_PLATFORMTHEME | ayarlanmamış (doğru durum, dokunulmadı) |
| Önceki renk şeması | BreezeDark |
| Önceki widget stili | Breeze |
| Önceki Kvantum teması | (boş) |

## Dizinler

- Kullanıcı renk şemaları: `~/.local/share/color-schemes/`
- Kullanıcı Kvantum temaları: `~/.config/Kvantum/<Ad>/<Ad>.kvconfig + .svg`
- Sistem Kvantum temaları: `/usr/share/Kvantum/` (KvDarkRed burada; dokunulmadı)
- Kvantum Qt6 stil eklentisi: `/usr/lib64/qt6/plugins/styles/libkvantum.so`

## Teknik notlar (Kvantum)

- Menü öğesi hover/seçimi SVG'de `menuitem-pressed` elementiyle çizilir
  (`-focused` değil). Menubar: `menubaritem-*`.
- SVG'de eksik olan element Kvantum'un gömülü varsayılan temasına düşer
  (fallback) — tema bu yüzden kısmi SVG ile de çalışır.
- `focus-*` elementleri varsa ayrı `[Focus]` bölümü gerekmeden ince fokus
  çerçevesi olarak kullanılır.
- Frame elementleri 8 parça ister: top/bottom/left/right + 4 köşe.
  Köşe yarıçapı = köşe parçası boyutu = kvconfig `frame.top` vb. değeri.
- `transient_scrollbar=true` ise thumb `ss-*` elementleriyle çizilir.

## Yedekler

- `~/.local/share/trs-theme-backup/2026-07-18_21-24-56/` — ilk analiz yedeği
- `~/.local/share/trs-theme-backup/2026-07-18_21-28-21/` — kurulum öncesi
- `~/.local/share/trs-theme-backup/last-state.txt` — uninstall'un döneceği durum

## Test sonuçları (2026-07-18)

- Dolphin: kenar çubuğu seçimi kırmızı, URL girişi koyu/ince kenarlık, aktif
  sekme kırmızı vurgu, zoom slider kırmızı — logda SVG/Kvantum hatası yok.
- kvantumpreview: buton/toggle/disabled/progress/tab/combo/spin doğru.
- Konsole: menubar + toolbar koyu, tutarlı.
- Elle doğrulanacaklar: menü açılışı (ekran görüntüsü Wayland'da programatik
  alınamadı), tooltip, dosya seçim diyaloğu, aktif/pasif pencere farkı.
