#!/usr/bin/env python3
"""Özgün ve üretilen SVG'yi yan yana PNG'ye çizer. onizle.py <tema dizini> <çıktı dizini> [dosya...]"""
import gzip, sys
from pathlib import Path
from PySide6.QtGui import QGuiApplication, QImage, QPainter, QColor
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QByteArray, QRectF
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
app = QGuiApplication([])
tema, cikti = Path(sys.argv[1]), Path(sys.argv[2]); cikti.mkdir(parents=True, exist_ok=True)
KAYNAK = Path("/usr/share/plasma/desktoptheme/default")
dosyalar = sys.argv[3:] or [str(f.relative_to(tema))[:-4] for f in sorted(tema.rglob("*.svg"))]
for d in dosyalar:
    a = QSvgRenderer(QByteArray(gzip.open(KAYNAK / (d + ".svgz")).read()))
    b = QSvgRenderer(str(tema / (d + ".svg")))
    vb = a.viewBoxF(); olcek = min(6, max(2, 900 / max(vb.width(), 1)))
    w, h = int(vb.width() * olcek), int(vb.height() * olcek)
    im = QImage(w, h * 2 + 6, QImage.Format_ARGB32); im.fill(QColor("#7a7a7a"))
    p = QPainter(im); a.render(p, QRectF(0, 0, w, h)); b.render(p, QRectF(0, h + 6, w, h)); p.end()
    im.save(str(cikti / (d.replace("/", "_") + ".png")))
print("tamam", len(dosyalar))
