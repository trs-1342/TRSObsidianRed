#!/usr/bin/env python3
"""TRS Keskin imleç temasını sıfırdan üretir (özgün, programla çizilmiş).

Her imleç 32x32'lik bir tuvalde SVG olarak tanımlanır (anma boyu 24).
Çıktı: Xcursor dosyaları (birçok boyda) + KWin'in ölçeklenebilir SVG imleçleri.
Takma adlar (sembolik bağlar) Breeze imleç temasındaki yapıdan alınır.

Kullanım: uret.py [hedef dizin] [--onizleme dosya.png]
Geri alma: plasma-apply-cursortheme <eski tema>
"""
import argparse, json, math, os, shutil, struct
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QByteArray, QRectF
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

# ----------------------------------------------------------------------------
# GÖRÜNÜM — renk ve kalınlıklar buradan değişir
# ----------------------------------------------------------------------------
GOVDE = "#000000"     # düz siyah dolgu (kullanıcı açık gri dolguyu beğenmedi)
AYRINTI = False       # gövde içi ince çizgiler (kullanıcı beğenmedi, kapalı)
KENAR = "#c4c4c4"     # ince dış çizgi
DETAY = "#5c5c5c"     # gövde içi ince ayrıntı çizgileri
VURGU = "#f2f2f2"     # canlandırmada etkin kare
SONUK = "#000000"     # canlandırmada bekleyen kareler
HALE = "#000000"      # açık zeminde seçilsin diye en dıştaki koyu iz
HALE_OPAKLIK = 0.35
KENAR_KALINLIK = 1.0  # ekran pikseli cinsinden (anma boyunda)
HALE_KALINLIK = 2.6
OLCEK = 0.8           # çizimin boyu; tuvalin ortası çevresinde küçülür

TUVAL, ANMA = 32, 24
BOYLAR = [24, 32, 36, 48, 64, 72, 96]
_ap = argparse.ArgumentParser(description="TRS Keskin imleç temasını üretir")
_ap.add_argument("hedef", nargs="?", type=Path,
                 default=Path.home() / ".local/share/icons/trs-keskin-imlec")
_ap.add_argument("--onizleme", metavar="DOSYA.png")
_arg = _ap.parse_args()
HEDEF, ONIZLEME = _arg.hedef, _arg.onizleme
BREEZE = Path("/usr/share/icons/breeze_cursors")


# ----------------------------------------------------------------------------
# Çizim yardımcıları
# ----------------------------------------------------------------------------
def hiza(v):
    """Koordinatı, küçültmeden SONRA tam piksel sınırına düşecek
    biçimde kaydırır; yatay ve dikey kenarlar bulanmadan, keskin çıkar."""
    son = round(16 + (v - 16) * OLCEK)
    return 16 + (son - 16) / OLCEK


KK = KENAR_KALINLIK / OLCEK      # küçültme sonrası tam KENAR_KALINLIK piksel
HK = HALE_KALINLIK / OLCEK


def nokta(pts):
    return " ".join(f"{x:g},{y:g}" for x, y in pts)


def govde(pts, ek=""):
    """Kapalı çokgen: koyu hale + düz dolgu + ince kenar."""
    d = f"M {nokta([(hiza(x), hiza(y)) for x, y in pts])} Z"
    return (f'<path d="{d}" fill="none" stroke="{HALE}" stroke-opacity="{HALE_OPAKLIK}" '
            f'stroke-width="{HK:g}" stroke-linejoin="miter"/>'
            # kenar dolgunun DIŞINA çizilir (önce çift kalın çizgi, üstüne dolgu):
            # ince parçalar (metin imleci, artı) kenar yüzünden kaybolmaz
            f'<path d="{d}" fill="none" stroke="{KENAR}" '
            f'stroke-width="{2 * KK:g}" stroke-linejoin="miter"/>'
            f'<path d="{d}" fill="{GOVDE}"/>' + ek)


def kutu(x, y, w, h, dolgu=GOVDE):
    x2, y2 = hiza(x + w), hiza(y + h)
    x, y = hiza(x), hiza(y)
    w, h = max(x2 - x, 1 / OLCEK), max(y2 - y, 1 / OLCEK)
    return (f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="none" '
            f'stroke="{HALE}" stroke-opacity="{HALE_OPAKLIK}" stroke-width="{HK:g}"/>'
            f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="none" '
            f'stroke="{KENAR}" stroke-width="{2 * KK:g}"/>'
            f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="{dolgu}"/>')


def cizgi(d, kalin=1.9):
    """Açık yol: kenarlı kalın çizgi (hale + kenar + gövde)."""
    ort = 'fill="none" stroke-linecap="butt" stroke-linejoin="miter"'
    if GOVDE == "none":   # gövdesiz: tek ince çizgi + hale
        return (f'<path d="{d}" {ort} stroke="{HALE}" stroke-opacity="{HALE_OPAKLIK}" '
                f'stroke-width="{KK * 1.5 + 1.4:g}"/>'
                f'<path d="{d}" {ort} stroke="{KENAR}" stroke-width="{KK * 1.5:g}"/>')
    return (f'<path d="{d}" {ort} stroke="{HALE}" stroke-opacity="{HALE_OPAKLIK}" '
            f'stroke-width="{kalin + 2 * KK + 1.6:g}"/>'
            f'<path d="{d}" {ort} stroke="{KENAR}" stroke-width="{kalin + 2 * KK:g}"/>'
            f'<path d="{d}" {ort} stroke="{GOVDE}" stroke-width="{kalin:g}"/>')


def ince(d, renk=DETAY, kalin=0.8):
    if not AYRINTI:
        return ""
    return (f'<path d="{d}" fill="none" stroke="{renk}" stroke-width="{kalin:g}" '
            f'stroke-linecap="butt"/>')


def dondur(ic, aci, olcek=1.0):
    return f'<g transform="rotate({aci:g} 16 16) translate(16 16) scale({olcek:g}) translate(-16 -16)">{ic}</g>'


def ayna(ic):
    return f'<g transform="matrix(-1 0 0 1 32 0)">{ic}</g>'


# ----------------------------------------------------------------------------
# Biçimler
# ----------------------------------------------------------------------------
# Ok dik yukarı bakar, sapı (gövdesi) yoktur: içi dolu, altı hafif çentikli
# üçgen. Kullanıcı sola yatık oku, sapı ve iç çizgileri beğenmedi.
OK_UC = (16, 2)
OK_PTS = [(16, 2), (25, 25), (16, 20.5), (7, 25)]
OK = govde(OK_PTS)

YUKARI_OK = govde([(16, 3), (23.5, 12.5), (18.2, 12.5), (18.2, 28), (13.8, 28),
                   (13.8, 12.5), (8.5, 12.5)], ince("M 16,7 V 26"))

EL_AYRINTI = ince("M 15.2,12 V 17.5") + ince("M 19,13 V 17.5") + ince("M 22.8,14 V 17.5")
EL = govde([(11.4, 3), (15.2, 3), (15.2, 11), (19, 11), (19, 12), (22.8, 12), (22.8, 13),
            (26.4, 13), (26.4, 22), (23.6, 28.4), (13.2, 28.4), (7, 20.2), (7, 16.2),
            (9.4, 16.2), (11.4, 18.4)], EL_AYRINTI + ince("M 13.3,5 V 15"))
ACIK_EL = govde([(9.8, 8), (13.4, 8), (13.4, 6), (17, 6), (17, 7), (20.6, 7), (20.6, 9),
                 (24.2, 9), (24.2, 22), (21.4, 28.4), (12, 28.4), (5.8, 19.4), (5.8, 15.4),
                 (8, 15.4), (9.8, 17.4)],
                ince("M 13.4,8 V 16") + ince("M 17,7 V 16") + ince("M 20.6,9 V 16"))
KAPALI_EL = govde([(9.8, 13), (13.4, 13), (13.4, 12), (17, 12), (17, 12.5), (20.6, 12.5),
                   (20.6, 13.5), (24.2, 13.5), (24.2, 22), (21.4, 28.4), (12, 28.4),
                   (7.4, 21.4), (7.4, 17), (9.8, 17)],
                  ince("M 13.4,13 V 17.5") + ince("M 17,12.5 V 17.5") + ince("M 20.6,13.5 V 17.5"))

METIN = govde([(10.5, 4), (15, 4), (16, 5), (17, 4), (21.5, 4), (21.5, 6.2), (17.1, 6.2),
               (17.1, 25.8), (21.5, 25.8), (21.5, 28), (17, 28), (16, 27), (15, 28),
               (10.5, 28), (10.5, 25.8), (14.9, 25.8), (14.9, 6.2), (10.5, 6.2)])

ARTI_IMLEC = (kutu(15.1, 3, 1.8, 9.6) + kutu(15.1, 19.4, 1.8, 9.6) + kutu(3, 15.1, 9.6, 1.8)
              + kutu(19.4, 15.1, 9.6, 1.8)
              + f'<rect x="15.3" y="15.3" width="1.4" height="1.4" fill="{KENAR}"/>')
HUCRE = govde([(13.8, 5), (18.2, 5), (18.2, 13.8), (27, 13.8), (27, 18.2), (18.2, 18.2),
               (18.2, 27), (13.8, 27), (13.8, 18.2), (5, 18.2), (5, 13.8), (13.8, 13.8)])

YATAY = govde([(2.6, 16), (9, 9.6), (9, 14.2), (23, 14.2), (23, 9.6), (29.4, 16),
               (23, 22.4), (23, 17.8), (9, 17.8), (9, 22.4)], ince("M 10.5,16 H 21.5"))
SUTUN = (govde([(2.6, 16), (8.4, 10.2), (8.4, 14.4), (12.6, 14.4), (12.6, 17.6), (8.4, 17.6),
                (8.4, 21.8)])
         + govde([(29.4, 16), (23.6, 10.2), (23.6, 14.4), (19.4, 14.4), (19.4, 17.6),
                  (23.6, 17.6), (23.6, 21.8)])
         + kutu(15, 4.5, 2, 23))
DORT_YON = govde([(16, 2), (20.6, 7.6), (17.6, 7.6), (17.6, 14.4), (24.4, 14.4), (24.4, 11.4),
                  (30, 16), (24.4, 20.6), (24.4, 17.6), (17.6, 17.6), (17.6, 24.4),
                  (20.6, 24.4), (16, 30), (11.4, 24.4), (14.4, 24.4), (14.4, 17.6),
                  (7.6, 17.6), (7.6, 20.6), (2, 16), (7.6, 11.4), (7.6, 14.4), (14.4, 14.4),
                  (14.4, 7.6), (11.4, 7.6)],
                 f'<rect x="15.2" y="15.2" width="1.6" height="1.6" fill="{DETAY}"/>')

YASAK = cizgi("M 16,6 A 10,10 0 1 1 15.99,6 Z M 8.93,8.93 L 23.07,23.07", 2.2)
CARPI = govde([(6, 8.6), (8.6, 6), (16, 13.4), (23.4, 6), (26, 8.6), (18.6, 16), (26, 23.4),
               (23.4, 26), (16, 18.6), (8.6, 26), (6, 23.4), (13.4, 16)])

KALEM = govde([(5, 27), (6.6, 20.6), (20, 7.2), (24.8, 12), (11.4, 25.4)],
              ince("M 6.6,20.6 L 11.4,25.4") + ince("M 17.6,9.6 L 22.4,14.4")
              + ince("M 9.4,22.2 L 20.4,11.2"))
DAMLALIK = govde([(5, 27), (6.2, 22), (16.4, 11.8), (20.2, 15.6), (10, 25.8)],
                 ince("M 8.4,23 L 17.4,14")) + \
    f'<g transform="rotate(45 21.5 10.5)">{kutu(17.4, 7.2, 8.2, 6.6)}</g>'


def buyutec(isaret):
    ic = cizgi("M 13,5.4 A 7.6,7.6 0 1 1 12.99,5.4 Z M 18.6,18.6 L 27,27", 2.0)
    # cam içi koyu dolgu: işaret açık zeminde de okunur
    if GOVDE != "none":
        ic += f'<circle cx="13" cy="13" r="6.7" fill="{GOVDE}"/>'
    yatay = f'<rect x="9.6" y="12.3" width="6.8" height="1.4" fill="{KENAR}"/>'
    dikey = f'<rect x="12.3" y="9.6" width="1.4" height="6.8" fill="{KENAR}"/>'
    return ic + yatay + (dikey if isaret == "+" else "")


def dortlu(etkin, x=7, y=7, k=8, bosluk=2):
    """2x2 kare; `etkin` sıradaki kare açık renk (saat yönünde 0..3)."""
    yerler = [(0, 0), (1, 0), (1, 1), (0, 1)]
    return "".join(kutu(x + i * (k + bosluk), y + j * (k + bosluk), k, k,
                        VURGU if n == etkin else SONUK)
                   for n, (i, j) in enumerate(yerler))


# Okun sağ altına eklenen küçük rozetler
ROZET_ARTI = kutu(18.6, 18.6, 10.4, 10.4) + \
    f'<path d="M 23.8,20.8 V 26.8 M 20.8,23.8 H 26.8" stroke="{KENAR}" stroke-width="1.4"/>'
ROZET_BAG = kutu(18.6, 18.6, 10.4, 10.4) + \
    f'<path d="M 21.4,26.2 L 26,21.6 M 22.6,21.4 H 26.2 V 25" fill="none" stroke="{KENAR}" stroke-width="1.3"/>'
ROZET_MENU = kutu(18.6, 18.6, 10.4, 10.4) + \
    f'<path d="M 20.8,21.4 H 26.8 M 20.8,23.8 H 26.8 M 20.8,26.2 H 26.8" stroke="{KENAR}" stroke-width="1.1"/>'
ROZET_SORU = kutu(18.6, 18.6, 10.4, 10.4) + \
    (f'<path d="M 21.6,22.6 V 20.8 H 26 V 23.8 H 23.8 V 25" fill="none" stroke="{KENAR}" stroke-width="1.3"/>'
     f'<rect x="23.1" y="26" width="1.4" height="1.4" fill="{KENAR}"/>')
ROZET_YASAK = cizgi("M 23.8,18.4 A 5.4,5.4 0 1 1 23.79,18.4 Z M 20,20 L 27.6,27.6", 1.3)

def yana(ic):
    """Rozeti okun sapına değmeyecek kadar sağa kaydırır."""
    return f'<g transform="translate(2.2 1.4)">{ic}</g>'


# ad -> (kareler, (sıcak nokta x, y), gecikme ms)
BICIM = {
    "default": ([OK], OK_UC, 0),
    "right_ptr": ([OK], OK_UC, 0),
    "draft": ([OK], OK_UC, 0),
    "wayland-cursor": ([OK], OK_UC, 0),
    "center_ptr": ([YUKARI_OK], (16, 3), 0),
    "up-arrow": ([YUKARI_OK], (16, 3), 0),
    "right-arrow": ([dondur(YUKARI_OK, 90)], (29, 16), 0),
    "down-arrow": ([dondur(YUKARI_OK, 180)], (16, 29), 0),
    "left-arrow": ([dondur(YUKARI_OK, 270)], (3, 16), 0),
    "pointer": ([EL], (13, 4), 0),
    "openhand": ([ACIK_EL], (15, 16), 0),
    "dnd-move": ([KAPALI_EL], (15, 16), 0),
    "text": ([METIN], (16, 16), 0),
    "vertical-text": ([dondur(METIN, 90)], (16, 16), 0),
    "crosshair": ([ARTI_IMLEC], (16, 16), 0),
    "cell": ([HUCRE], (16, 16), 0),
    "size_hor": ([YATAY], (16, 16), 0),
    "left_side": ([YATAY], (16, 16), 0),
    "right_side": ([YATAY], (16, 16), 0),
    "size_ver": ([dondur(YATAY, 90)], (16, 16), 0),
    "top_side": ([dondur(YATAY, 90)], (16, 16), 0),
    "bottom_side": ([dondur(YATAY, 90)], (16, 16), 0),
    "size_fdiag": ([dondur(YATAY, 45, 0.92)], (16, 16), 0),
    "top_left_corner": ([dondur(YATAY, 45, 0.92)], (16, 16), 0),
    "bottom_right_corner": ([dondur(YATAY, 45, 0.92)], (16, 16), 0),
    "size_bdiag": ([dondur(YATAY, -45, 0.92)], (16, 16), 0),
    "top_right_corner": ([dondur(YATAY, -45, 0.92)], (16, 16), 0),
    "bottom_left_corner": ([dondur(YATAY, -45, 0.92)], (16, 16), 0),
    "col-resize": ([SUTUN], (16, 16), 0),
    "row-resize": ([dondur(SUTUN, 90)], (16, 16), 0),
    "all-scroll": ([DORT_YON], (16, 16), 0),
    "fleur": ([DORT_YON], (16, 16), 0),
    "not-allowed": ([YASAK], (16, 16), 0),
    "x-cursor": ([CARPI], (16, 16), 0),
    "pirate": ([CARPI], (16, 16), 0),
    "pencil": ([KALEM], (5, 27), 0),
    "color-picker": ([DAMLALIK], (5, 27), 0),
    "zoom-in": ([buyutec("+")], (13, 13), 0),
    "zoom-out": ([buyutec("-")], (13, 13), 0),
    "copy": ([OK + yana(ROZET_ARTI)], OK_UC, 0),
    "alias": ([OK + yana(ROZET_BAG)], OK_UC, 0),
    "context-menu": ([OK + yana(ROZET_MENU)], OK_UC, 0),
    "help": ([OK + yana(ROZET_SORU)], OK_UC, 0),
    "no-drop": ([OK + yana(ROZET_YASAK)], OK_UC, 0),
    "dnd-no-drop": ([KAPALI_EL + ROZET_YASAK], (15, 16), 0),
    "wait": ([dortlu(n) for n in range(4)], (16, 16), 160),
    "progress": ([OK + dortlu(n, 20.4, 19.6, 4.4, 1.4) for n in range(4)], OK_UC, 160),
}


def sicak_son(sicak):
    """Çizimdeki sıcak noktanın küçültme sonrası tuvaldeki yeri."""
    return tuple(round(16 + (v - 16) * OLCEK) for v in sicak)


def svg(ic, sicak=None):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{TUVAL}" height="{TUVAL}" '
            f'viewBox="0 0 {TUVAL} {TUVAL}"><g transform="translate(16 16) '
            f'scale({OLCEK:g}) translate(-16 -16)">{ic}</g></svg>')


def ciz(ic, px, sicak):
    im = QImage(px, px, QImage.Format_ARGB32_Premultiplied)
    im.fill(QColor(0, 0, 0, 0))
    p = QPainter(im)
    p.setRenderHint(QPainter.Antialiasing, True)
    QSvgRenderer(QByteArray(svg(ic, sicak).encode())).render(p, QRectF(0, 0, px, px))
    p.end()
    return im


def xcursor(kareler, sicak, gecikme):
    """Xcursor ikili dosyası: her boy için tüm kareler."""
    parcalar = []
    for anma in BOYLAR:
        px = round(anma * TUVAL / ANMA)
        for ic in kareler:
            im = ciz(ic, px, sicak)
            veri = bytes(im.constBits())[:px * px * 4]
            bas = struct.pack("<9I", 36, 0xFFFD0002, anma, 1, px, px,
                              round(sicak_son(sicak)[0] * px / TUVAL), round(sicak_son(sicak)[1] * px / TUVAL),
                              gecikme)
            parcalar.append((anma, bas + veri))
    konum = 16 + 12 * len(parcalar)
    cikti = [struct.pack("<4sIII", b"Xcur", 16, 0x10000, len(parcalar))]
    for anma, veri in parcalar:
        cikti.append(struct.pack("<III", 0xFFFD0002, anma, konum))
        konum += len(veri)
    return b"".join(cikti + [v for _, v in parcalar])


app = QGuiApplication([])
gercek = {p.name for p in (BREEZE / "cursors").iterdir() if not p.is_symlink()}
eksik = gercek - set(BICIM)
assert not eksik, f"çizimi olmayan imleç: {eksik}"

if HEDEF.exists():
    # Yalnızca daha önce bu betiğin ürettiği bir tema dizini silinir.
    assert HEDEF.is_dir() and (HEDEF / "index.theme").is_file() \
        and "TRS Keskin" in (HEDEF / "index.theme").read_text(), \
        f"{HEDEF} bu betiğin ürettiği bir tema değil, silinmedi"
    shutil.rmtree(HEDEF)
(HEDEF / "cursors").mkdir(parents=True)
(HEDEF / "cursors_scalable").mkdir()
for ad, (kareler, sicak, gecikme) in BICIM.items():
    (HEDEF / "cursors" / ad).write_bytes(xcursor(kareler, sicak, gecikme))
    d = HEDEF / "cursors_scalable" / ad
    d.mkdir()
    meta = []
    for n, ic in enumerate(kareler):
        dosya = f"{ad}-{n:02d}.svg" if len(kareler) > 1 else f"{ad}.svg"
        (d / dosya).write_text(svg(ic, sicak))
        kayit = {"filename": dosya, "hotspot_x": sicak_son(sicak)[0],
                 "hotspot_y": sicak_son(sicak)[1],
                 "nominal_size": ANMA}
        if len(kareler) > 1:
            kayit["delay"] = gecikme
        meta.append(kayit)
    (d / "metadata.json").write_text(json.dumps(meta, indent=4) + "\n")

# Takma adlar: Breeze'deki bağ yapısının aynısı
for alt in ("cursors", "cursors_scalable"):
    for p in (BREEZE / alt).iterdir():
        if p.is_symlink() and not (HEDEF / alt / p.name).exists():
            hedef = os.readlink(p)
            if (HEDEF / alt / hedef).exists() or (HEDEF / alt / hedef).is_symlink() \
                    or (BREEZE / alt / hedef).is_symlink():
                os.symlink(hedef, HEDEF / alt / p.name)
kirik = [p.name for alt in ("cursors", "cursors_scalable")
         for p in (HEDEF / alt).iterdir() if p.is_symlink() and not p.exists()]
assert not kirik, f"kırık bağ: {kirik}"

(HEDEF / "index.theme").write_text(
    "[Icon Theme]\nName=TRS Keskin\n"
    "Comment=Düz, koyu gövdeli, ince kenarlı keskin imleçler\n"
    "Inherits=breeze_cursors\n")
print("üretildi:", HEDEF, "|", len(BICIM), "imleç,",
      sum(1 for p in (HEDEF / "cursors").iterdir() if p.is_symlink()), "takma ad")

if ONIZLEME:
    adlar = ["default", "pointer", "text", "openhand", "dnd-move", "crosshair", "cell",
             "size_hor", "size_ver", "size_fdiag", "size_bdiag", "col-resize", "row-resize",
             "all-scroll", "not-allowed", "x-cursor", "wait", "progress", "help",
             "context-menu", "copy", "alias", "no-drop", "dnd-no-drop", "pencil",
             "color-picker", "zoom-in", "zoom-out", "up-arrow", "right_ptr"]
    S, sutun = 96, 10
    satir = (len(adlar) + sutun - 1) // sutun
    zeminler = ["#000000", "#151515", "#808080", "#f2f2f2"]
    sayfa = QImage(sutun * S, satir * S * len(zeminler) + 40, QImage.Format_ARGB32)
    sayfa.fill(QColor("#000000"))
    p = QPainter(sayfa)
    for z, renk in enumerate(zeminler):
        p.fillRect(0, z * satir * S, sutun * S, satir * S, QColor(renk))
        for n, ad in enumerate(adlar):
            p.drawImage((n % sutun) * S, z * satir * S + (n // sutun) * S,
                        ciz(BICIM[ad][0][0], S, BICIM[ad][1]))
    for n, ad in enumerate(["default", "pointer", "text", "size_fdiag", "wait", "help"]):
        for k, px in enumerate([32, 43]):   # gerçek boy: anma 24 ve 32
            p.drawImage(10 + n * 110 + k * 50, satir * S * len(zeminler) + 2,
                        ciz(BICIM[ad][0][0], px, BICIM[ad][1]))
    p.end()
    sayfa.save(ONIZLEME)
    print("önizleme:", ONIZLEME)
