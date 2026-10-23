#!/usr/bin/env python3
"""TRS Keskin Plasma stilini üretir.

Breeze'in (default) SVG'lerini alır, yuvarlak köşeleri dik açıya çevirir ve
yüzeyleri opak yapar. Kaynak dosyalara dokunmaz; çıktı ev dizinindeki ayrı bir
temadır. Renk dosyası konmaz: tema sistem renk şemasını (TRS Obsidian Red)
izler.

Kullanım: uret.py <sürüm> [hedef dizin]
Geri alma: plasma-apply-desktoptheme breeze-dark
"""
import gzip, json, math, re, shutil, sys
import xml.etree.ElementTree as ET
from pathlib import Path

KAYNAK = Path("/usr/share/plasma/desktoptheme/default")
SURUM = sys.argv[1] if len(sys.argv) > 1 else "1"
HEDEF = Path(sys.argv[2]) if len(sys.argv) > 2 else \
    Path.home() / ".local/share/plasma/desktoptheme/trs-keskin"

# Panel, menü, ipucu yüzeylerinin opaklığı (Breeze: 0.85). Sınama sonrası
# buradan değiştirilir.
OPAKLIK = "1"

# 6x6 köşeli "yeni kuşak" çerçeveler (viewBox 157x64): köşe ve maske elle.
YUZEYLER = [
    "dialogs/background", "widgets/panel-background", "widgets/tooltip",
    "solid/dialogs/background", "solid/widgets/panel-background",
    "solid/widgets/tooltip", "solid/widgets/background",
    "translucent/dialogs/background", "translucent/widgets/panel-background",
    "translucent/widgets/tooltip",
]
# İç parçalar: genel dönüştürücü (eğri köşe -> dik köşe, rx/ry silinir).
PARCALAR = [
    "widgets/background", "translucent/widgets/background",
    "widgets/button", "widgets/lineedit", "widgets/viewitem",
    "widgets/listitem", "widgets/tasks", "widgets/slider", "widgets/switch",
    "widgets/scrollbar", "widgets/tabbar", "widgets/menubaritem",
    "widgets/toolbar", "widgets/frame", "widgets/plasmoidheading",
    "widgets/pager", "widgets/actionbutton", "widgets/margins-highlight",
    "widgets/bar_meter_horizontal", "widgets/bar_meter_vertical",
    "widgets/media-delegate", "widgets/scrollwidget", "widgets/picker",
    "widgets/plot-background", "widgets/containment-controls",
]
# Yuvarlak kalması gereken öğeler (kimlikte geçen sözcükler).
DOKUNMA = ("shadow", "radiobutton")

# Daireleri de kareye çevrilecek dosyalar (tutamaçlar).
DAIRE_KARE = {"widgets/slider", "widgets/switch"}
DAIRE = re.compile(r"<circle\b[^>]*?/>", re.S)

MASKE = {"mask-topleft": (113, 10), "mask-topright": (151, 10),
         "mask-bottomleft": (113, 48), "mask-bottomright": (151, 48)}
KOSE_D = {"M 0,6 H 6 V 0 C 2,0 0,2 0,6 Z", "M 0,0 V 6 H 6 C 6,2 4,0 0,0 Z",
          "M 6,6 V 0 H 0 c 0,4 2,6 6,6 z", "M 0,6 V 0 H 6 C 6,4 4,6 0,6 Z"}
YOL = re.compile(r"<path\b[^>]*>", re.S)
DIKDORTGEN = re.compile(r"<rect\b[^>]*>", re.S)
D = re.compile(r'(?<![\w:-])d="([^"]*)"')


def oku(yol):
    return gzip.open(KAYNAK / (yol + ".svgz")).read().decode()


def yaz(yol, metin):
    cikti = HEDEF / (yol + ".svg")
    cikti.parent.mkdir(parents=True, exist_ok=True)
    cikti.write_text(metin)


# --- yol (path) verisi: eğri köşeleri dik köşeye çevir -----------------------
SAYI = r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?"
PARCA = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|" + SAYI)
ADET = dict(M=2, L=2, H=1, V=1, C=6, S=4, Q=4, T=2, A=7, Z=0)


def bic(x):
    s = f"{x:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def kose_bul(p0, t0, t1, p1):
    """p0'dan t0 yönünde, p1'e t1 yönünde varan iki teğetin kesişimi."""
    det = t0[0] * t1[1] - t0[1] * t1[0]
    n0, n1 = math.hypot(*t0), math.hypot(*t1)
    if n0 < 1e-9 or n1 < 1e-9:
        return None
    aci = math.degrees(math.acos(max(-1, min(1,
          (t0[0] * t1[0] + t0[1] * t1[1]) / (n0 * n1)))))
    if not 60 <= aci <= 120:
        return None
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    a = (dx * t1[1] - dy * t1[0]) / det
    b = (t0[0] * dy - t0[1] * dx) / det
    if a <= 0 or b <= 0:
        return None
    return (p0[0] + a * t0[0], p0[1] + a * t0[1])


def keskin_yol(d):
    """Yol verisini mutlak komutlarla yeniden yazar; köşe gibi duran her
    eğriyi iki doğru parçasına çevirir. Çözemezse özgün veriyi döndürür."""
    tok = PARCA.findall(d)
    cik, i = [], 0
    cur = bas = (0.0, 0.0)
    son_kontrol = None
    komut = None
    degisti = False
    try:
        while i < len(tok):
            if tok[i].isalpha():
                komut = tok[i]; i += 1
            elif komut is None:
                return d
            elif komut in "Mm":          # M'den sonraki örtük çiftler L'dir
                komut = "L" if komut == "M" else "l"
            K, goreli = komut.upper(), komut.islower()
            n = ADET[K]
            v = [float(t) for t in tok[i:i + n]]
            if len(v) != n or any(t.isalpha() for t in tok[i:i + n]):
                return d
            i += n
            ox, oy = cur if goreli else (0.0, 0.0)
            if K == "Z":
                cik.append("Z"); cur = bas; son_kontrol = None; continue
            if K == "M":
                cur = bas = (v[0] + ox, v[1] + oy)
                cik.append(f"M {bic(cur[0])},{bic(cur[1])}")
                son_kontrol = None; continue
            if K in "LHV":
                if K == "L": yeni = (v[0] + ox, v[1] + oy)
                elif K == "H": yeni = (v[0] + ox, cur[1])
                else: yeni = (cur[0], v[0] + oy)
                cik.append(f"L {bic(yeni[0])},{bic(yeni[1])}")
                cur = yeni; son_kontrol = None; continue
            if K in "CS":
                if K == "C":
                    c1 = (v[0] + ox, v[1] + oy); c2 = (v[2] + ox, v[3] + oy)
                    p1 = (v[4] + ox, v[5] + oy)
                else:
                    c1 = (2 * cur[0] - son_kontrol[0], 2 * cur[1] - son_kontrol[1]) \
                        if son_kontrol else cur
                    c2 = (v[0] + ox, v[1] + oy); p1 = (v[2] + ox, v[3] + oy)
                t0 = (c1[0] - cur[0], c1[1] - cur[1])
                if math.hypot(*t0) < 1e-9:
                    t0 = (c2[0] - cur[0], c2[1] - cur[1])
                t1 = (p1[0] - c2[0], p1[1] - c2[1])
                if math.hypot(*t1) < 1e-9:
                    t1 = (p1[0] - c1[0], p1[1] - c1[1])
                k = kose_bul(cur, t0, t1, p1)
                if k:
                    cik.append(f"L {bic(k[0])},{bic(k[1])} L {bic(p1[0])},{bic(p1[1])}")
                    degisti = True
                else:
                    cik.append("C " + " ".join(f"{bic(a)},{bic(b)}" for a, b in (c1, c2, p1)))
                son_kontrol = c2; cur = p1; continue
            if K in "QT":
                if K == "Q":
                    c = (v[0] + ox, v[1] + oy); p1 = (v[2] + ox, v[3] + oy)
                else:
                    c = (2 * cur[0] - son_kontrol[0], 2 * cur[1] - son_kontrol[1]) \
                        if son_kontrol else cur
                    p1 = (v[0] + ox, v[1] + oy)
                cik.append(f"Q {bic(c[0])},{bic(c[1])} {bic(p1[0])},{bic(p1[1])}")
                son_kontrol = c; cur = p1; continue
            if K == "A":
                rx, ry, rot, buyuk, yon = v[0], v[1], v[2], v[3], v[4]
                p1 = (v[5] + ox, v[6] + oy)
                dx, dy = p1[0] - cur[0], p1[1] - cur[1]
                ceyrek = (not buyuk and abs(abs(dx) - rx) < 0.02 * max(rx, 1)
                          and abs(abs(dy) - ry) < 0.02 * max(ry, 1))
                if ceyrek:
                    adaylar = [(cur[0], p1[1]), (p1[0], cur[1])]
                    def capraz(c):
                        return ((cur[0] - c[0]) * (p1[1] - c[1])
                                - (cur[1] - c[1]) * (p1[0] - c[0]))
                    merkez = [c for c in adaylar if (capraz(c) > 0) == bool(yon)]
                    kose = [c for c in adaylar if c not in merkez]
                    if len(kose) == 1:
                        k = kose[0]
                        cik.append(f"L {bic(k[0])},{bic(k[1])} L {bic(p1[0])},{bic(p1[1])}")
                        degisti = True; cur = p1; son_kontrol = None; continue
                cik.append(f"A {bic(rx)},{bic(ry)} {bic(rot)} {int(buyuk)} {int(yon)} "
                           f"{bic(p1[0])},{bic(p1[1])}")
                cur = p1; son_kontrol = None; continue
    except (ValueError, IndexError, KeyError):
        return d
    return " ".join(cik) if degisti else d


def dokunulmayacaklar(metin):
    """Gölge gibi yuvarlak kalması gereken öğelerin altındaki yolların
    kimlikleri (kimliği yoksa yol verisi)."""
    atla = set()
    def gez(e, yasak):
        yasak = yasak or any(s in (e.get("id") or "") for s in DOKUNMA)
        if yasak and e.get("d"):
            atla.add(e.get("id") or e.get("d"))
        for c in e:
            gez(c, yasak)
    gez(ET.fromstring(metin.encode()), False)
    return atla


def daire_degistir(m, atla):
    """Tutamaç dairelerini aynı boyda kareye çevirir."""
    oge = m.group(0)
    kimlik = re.search(r'(?<![\w:-])id="([^"]*)"', oge)
    if (kimlik and kimlik.group(1) in atla) or any(s in oge for s in DOKUNMA):
        return oge
    al = lambda ad: re.search(r'(?<![\w:-])%s="([^"]*)"' % ad, oge)
    cx, cy, r = al("cx"), al("cy"), al("r")
    if not (cx and cy and r):
        return oge
    x, y, k = float(cx.group(1)), float(cy.group(1)), float(r.group(1))
    yeni = re.sub(r'\s+(?<![\w:-])(cx|cy|r)="[^"]*"', "", oge)
    yeni = yeni.replace("<circle", f'<rect x="{bic(x - k)}" y="{bic(y - k)}" '
                        f'width="{bic(2 * k)}" height="{bic(2 * k)}"', 1)
    return yeni


def parca_keskinlestir(yol):
    metin = oku(yol)
    atla = dokunulmayacaklar(metin)
    n = [0, 0]
    def yol_degistir(m):
        oge = m.group(0)
        d = D.search(oge)
        kimlik = re.search(r'(?<![\w:-])id="([^"]*)"', oge)
        anahtar = kimlik.group(1) if kimlik else (d.group(1) if d else None)
        if not d or anahtar in atla:
            return oge
        yeni = keskin_yol(d.group(1))
        if yeni == d.group(1):
            return oge
        n[0] += 1
        return oge[:d.start(1)] + yeni + oge[d.end(1):]
    def rect_degistir(m):
        oge = m.group(0)
        if any(s in oge for s in DOKUNMA):
            return oge
        yeni = re.sub(r'\s+r[xy]="[^"]*"', "", oge)
        n[1] += yeni != oge
        return yeni
    # Metin üzerinde çalışır: dosyanın geri kalanı bayt bayt aynı kalmalı,
    # yoksa Plasma renk şemasını (current-color-scheme) uygulayamıyor.
    metin = DIKDORTGEN.sub(rect_degistir, YOL.sub(yol_degistir, metin))
    if yol in DAIRE_KARE:
        metin = DAIRE.sub(lambda m: daire_degistir(m, atla), metin)
    yaz(yol, metin)
    return n


def yuzey_keskinlestir(yol):
    metin = oku(yol)
    n = 0
    def degistir(m):
        nonlocal n
        oge = m.group(0)
        d = D.search(oge)
        if not d:
            return oge
        maske = re.search(r'id="(mask-(?:top|bottom)(?:left|right))"', oge)
        if maske:
            x, y = MASKE[maske.group(1)]
            yeni_d = f"M {x},{y} h 6 v 6 h -6 z"
        elif "ColorScheme-Background" in oge and d.group(1) in KOSE_D:
            yeni_d = "M 0,0 H 6 V 6 H 0 Z"
        else:
            return oge
        n += 1
        return oge[:d.start(1)] + yeni_d + oge[d.end(1):]
    metin = YOL.sub(degistir, metin)
    assert n == 8, (yol, n)
    metin = metin.replace("opacity:0.85;fill:currentColor",
                          f"opacity:{OPAKLIK};fill:currentColor")
    yaz(yol, metin)


if HEDEF.exists():
    shutil.rmtree(HEDEF)
HEDEF.mkdir(parents=True)
for y in YUZEYLER:
    yuzey_keskinlestir(y)
for y in PARCALAR:
    yol_sayisi, rect_sayisi = parca_keskinlestir(y)
    print(f"  {y}: {yol_sayisi} yol, {rect_sayisi} dikdörtgen")
shutil.copy(KAYNAK / "plasmarc", HEDEF / "plasmarc")
(HEDEF / "metadata.json").write_text(json.dumps({
    "KPlugin": {"Id": "trs-keskin", "Name": "TRS Keskin",
                "Description": "Keskin köşeli, sistem renklerini izleyen Plasma stili",
                "Authors": [{"Name": "trs"}], "License": "LGPL",
                "Version": SURUM},
    "X-Plasma-API": "5.0"}, ensure_ascii=False, indent=4) + "\n")
print("üretildi:", HEDEF, "sürüm", SURUM)
