# TRS Obsidian Red

Kişisel KDE Plasma 6 / Qt teması: neredeyse siyah zemin + koyu kırmızı vurgu.
İki parçadan oluşur ve ikisi birlikte kullanılmak üzere tasarlanmıştır:

| Parça | Ne kontrol eder | Dosya |
|---|---|---|
| KDE renk şeması | Palet: pencere/görünüm/seçim/tooltip renkleri, KWin başlık çubuğu | `color-scheme/TRSObsidianRed.colors` |
| Kvantum teması | Widget çizimi: buton, menü, sekme, scrollbar, checkbox… | `kvantum/TRSObsidianRed/` |

## Tasarım kuralları

- Düz (flat), gradientsiz, cam/neon efektsiz; ince 1 px kenarlıklar
- Köşe yuvarlaklığı: **6 px** (buton, giriş, menü, sekme), 4 px (menü öğesi, seçim, tooltip)
- Hover parlak değil: bir ton açık gri; kırmızı yalnızca seçim/vurgu için
- Scrollbar: transient (üzerine gelince belirir), 10 px, kapsül biçimli

## Renk paleti

| Rol | Hex | RGB |
|---|---|---|
| Görünüm zemini (view/base) | `#0B0B0B` | 11,11,11 |
| Pencere / menü zemini | `#151515` | 21,21,21 |
| Alternatif satır | `#1A1A1A` | 26,26,26 |
| Buton | `#1E1E1E` | 30,30,30 |
| Giriş alanı (lineedit) | `#0F0F0F` | 15,15,15 |
| Kenarlık | `#373737` | 55,55,55 |
| Ana vurgu (seçim) | `#C1121F` | 193,18,31 |
| Hover vurgusu | `#D72332` | 215,35,50 |
| Ana yazı | `#EEEEEE` | 238,238,238 |
| İkincil yazı | `#B4B4B4` | 180,180,180 |
| Pasif yazı | `#6E6E6E` | 110,110,110 |
| Negatif / Pozitif / Nötr / Uyarı | `#E0455A` / `#4CAF6E` / `#4FA3D6` / `#E5A50A` | — |

## Kurulum

```bash
~/Projects/TRSObsidianRed/install.sh
# veya
~/bin/install-trs-obsidian-red-theme.sh
```

Betik: mevcut ayarları `~/.local/share/trs-theme-backup/<zaman>/` altına yedekler,
dosyaları `~/.local/share/color-schemes/` ve `~/.config/Kvantum/TRSObsidianRed/`
konumuna kopyalar, ardından üç ayarı uygular:

1. `kvantummanager --set TRSObsidianRed`
2. `plasma-apply-colorscheme TRSObsidianRed`
3. `kdeglobals → [KDE] widgetStyle=kvantum`

İkinci kez çalıştırmak güvenlidir (idempotent). Paket kurmaz, sudo istemez,
sistem dosyalarına dokunmaz.

## Elle etkinleştirme (gerekirse)

- System Settings → Colors & Themes → **Colors** (TR: Renkler) → *TRS Obsidian Red*
- System Settings → Colors & Themes → **Application Style** (TR: Uygulama Biçemi) → *kvantum*
- Kvantum Manager → **Change/Delete Theme** → *TRSObsidianRed*

Açık uygulamalar widget stilini yeniden başlatılınca alır. Plasma paneli/masaüstü
için gerekirse oturumu kapatıp açın.

## Güncelleme (renk / radius / padding değiştirme)

| Ne değiştirmek istiyorsun | Dosya | Yer |
|---|---|---|
| Widget renkleri (buton, menü, thumb, vurgu…) | `scripts/gen_svg.py` | Baştaki `PALETTE` bloğu |
| Köşe yuvarlaklığı | `scripts/gen_svg.py` | `RADIUS = 6` |
| Palet (Qt palette; Dolphin görünüm alanı, seçim rengi) | `kvantum/TRSObsidianRed/TRSObsidianRed.kvconfig` | `[GeneralColors]` |
| Menü öğesi padding | aynı kvconfig | `[MenuItem] text.margin.*` |
| Buton padding / yüksekliği | aynı kvconfig | `[PanelButtonCommand] text.margin.*`, `min_height` |
| Scrollbar kalınlığı | aynı kvconfig | `[%General] scroll_width` |
| Slider kalınlığı / tutamaç | aynı kvconfig | `[%General] slider_*` |
| KDE paleti (Plasma, başlık çubuğu, KDE diyalogları) | `color-scheme/TRSObsidianRed.colors` | ilgili `[Colors:*]` grubu |

SVG'yi değiştirdikten sonra:

```bash
cd ~/Projects/TRSObsidianRed
python3 scripts/gen_svg.py > kvantum/TRSObsidianRed/TRSObsidianRed.svg
./install.sh   # dosyaları kopyalar ve yeniden uygular
```

Not: `TRSObsidianRed.svg` elle düzenlenmez; üreteci (`gen_svg.py`) düzenlenir.
Kvantum SVG önbelleğini tazelemek için uygulamayı yeniden başlatmak yeterlidir.

## Kaldırma

```bash
~/Projects/TRSObsidianRed/uninstall.sh
# veya
~/bin/remove-trs-obsidian-red-theme.sh
```

Yalnızca bu projenin kurduğu dosyaları siler ve kurulumdan önceki şemaya
(kayıtlı: BreezeDark + Breeze) döner. Yedekler ve proje dizini korunur.

## Qt5 / Qt6 notları

- Plasma 6 oturumu Qt6'dır; Kvantum'un Qt6 eklentisi kuruludur
  (`/usr/lib64/qt6/plugins/styles/libkvantum.so`).
- `QT_QPA_PLATFORMTHEME` / `QT_STYLE_OVERRIDE` **bilinçli olarak ayarlanmadı**;
  Plasma kendi platform teması üzerinden stili ve paleti tüm KDE/Qt6
  uygulamalarına dağıtır. qt5ct/qt6ct gerekmez ve önerilmez.
- Sistemde KF5/Qt5 kütüphaneleri var; bir Qt5 uygulaması temayı almazsa
  (Fusion/Breeze görünür), kullanıcı onayıyla şu paket kurulabilir:
  `sudo dnf install kvantum-qt5`  → aynı tema adını otomatik kullanır.
- Root/`pkexec` ile çalışan uygulamalar kullanıcı temasını okumaz; bu normaldir.

## Sorun giderme

- **Beyaz kalan Qt penceresi** → uygulama Qt5 olabilir (`ldd $(which app) | grep Qt5`);
  yukarıdaki kvantum-qt5 notuna bak.
- **Tema Kvantum Manager listesinde yok** → klasör ve dosya adları birebir
  `TRSObsidianRed` olmalı: `~/.config/Kvantum/TRSObsidianRed/TRSObsidianRed.kvconfig`.
- **Plasma güncellemesi sonrası bozulma** → tema tamamen `$HOME` altında;
  sistem güncellemeleri ezemez. `install.sh`'ı yeniden çalıştırmak yeterli.
- **Ayar kayboldu** → `kreadconfig6 --file kdeglobals --group KDE --key widgetStyle`
  çıktısı `kvantum` olmalı; değilse `install.sh` tekrar çalıştırılır.

## Değişiklik günlüğü

- **2026-07-18** — İlk sürüm. Sistem analizi (Plasma 6.7.3, Qt 6.11.1, Fedora 44,
  Kvantum 1.1.6), renk şeması + Kvantum teması sıfırdan üretildi (SVG programatik,
  497 element), kurulum/kaldırma betikleri, Dolphin + kvantumpreview ile test.
  Ekran görüntüleri `screenshots/` altında.
