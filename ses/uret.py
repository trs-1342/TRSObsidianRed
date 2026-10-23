#!/usr/bin/python3
"""TRS Kare sistem ses temasını SIFIRDAN üretir:  uret.py [hedef dizin]

Bütün sesler kare dalgadır (eski oyun konsollarındaki köşeli ton): "kare" tasarım dilinin ses karşılığı.
Her olayın 3-5 notalık kısa bir ezgisi vardır; çok sık çalan olaylar (ses düzeyi, düğme, terminal zili)
bilerek tek-iki nota tutulur ki yormasın. Ton merkezi la minör; nota birimi 0,13 saniye.

Çıktı bir freedesktop ses temasıdır: index.theme + stereo/*.oga. Eksik olaylar Ocean temasından alınır.
Kurulu yer: ~/.local/share/sounds/trs-kare  ·  Sistem Ayarları → Sistem Sesleri'nde "TRS Kare".
"""
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

HIZ = 48000           # örnekleme hızı
BIRIM = 0.13          # bir notanın süresi (saniye)
TEPE = 0.30           # en yüksek genlik (kare dalga gür duyulur; bilerek kısık)
YANKI = (0.13, 0.22)  # yankı gecikmesi (sn) ve düzeyi; ezgilere derinlik verir

NOTA = {"C": -9, "C#": -8, "D": -7, "D#": -6, "E": -5, "F": -4, "F#": -3, "G": -2, "G#": -1,
        "A": 0, "A#": 1, "B": 2}


def frekans(ad):
    """'A4' → 440 Hz, 'D#5' → ..."""
    return 440.0 * 2 ** ((NOTA[ad[:-1]] + 12 * (int(ad[-1]) - 4)) / 12)


def kare(f, sure, dolgu=1.0):
    """Bant sınırlı kare dalga: tek harmoniklerin toplamı (köşeli ama cızırtısız)."""
    t = np.arange(int(HIZ * sure)) / HIZ
    dalga = np.zeros_like(t)
    k = 1
    while k * f < 15000 and k <= 41:
        dalga += np.sin(2 * np.pi * k * f * t) / k
        k += 2
    dalga *= 4 / np.pi * 0.78
    # zarf: sert giriş, üstel sönüm, tık yapmayan kısa çıkış
    zarf = np.exp(-t / (sure * 0.55 * dolgu))
    giris = int(HIZ * 0.002)
    cikis = int(HIZ * 0.010)
    zarf[:giris] *= np.linspace(0, 1, giris)
    zarf[-cikis:] *= np.linspace(1, 0, cikis)
    return dalga * zarf


def gurultu(sure, basamak):
    """Konsol tarzı gürültü: belirli aralıklarla değişen rastgele kare düzeyleri."""
    r = np.random.default_rng(1342)
    n = int(HIZ * sure)
    adim = max(1, int(HIZ / basamak))
    dalga = np.repeat(r.choice([-1.0, 1.0], n // adim + 1), adim)[:n] * 0.5
    t = np.arange(n) / HIZ
    zarf = np.exp(-t / (sure * 0.4))
    zarf[-int(HIZ * 0.01):] *= np.linspace(1, 0, int(HIZ * 0.01))
    return dalga * zarf


def ezgi(notalar, yanki=True):
    """notalar: (ad ya da None, birim sayısı[, 'g' = gürültü]) listesi."""
    parcalar = []
    for n in notalar:
        ad, uzunluk = n[0], n[1] * BIRIM
        if ad is None:
            parcalar.append(np.zeros(int(HIZ * uzunluk)))
        elif ad == "gurultu":
            parcalar.append(gurultu(uzunluk, n[2]))
        else:
            ses = kare(frekans(ad), uzunluk)
            if len(n) > 2:                         # ikinci ses: aralık (akor hissi)
                ses = ses * 0.7 + kare(frekans(n[2]), uzunluk) * 0.5
            parcalar.append(ses)
    ses = np.concatenate(parcalar)
    if yanki:
        gecikme = int(HIZ * YANKI[0])
        cikti = np.concatenate([ses, np.zeros(gecikme * 2)])
        cikti[gecikme:gecikme + len(ses)] += ses * YANKI[1]
        cikti[2 * gecikme:] += ses * YANKI[1] ** 2
        ses = cikti
    return ses / max(1e-9, np.max(np.abs(ses))) * TEPE


# Olay → ezgi. Yükselen ezgi = iyi/başlangıç, alçalan = kötü/bitiş, tekrar = uyarı.
SESLER = {
    # oturum
    "desktop-login":         ezgi([("A3", 1), ("E4", 1), ("A4", 1), ("C5", 1), ("E5", 3, "A5")]),
    "desktop-logout":        ezgi([("E5", 1), ("C5", 1), ("A4", 1), ("E4", 1), ("A3", 3, "E3")]),
    "service-login":         ezgi([("A4", 1), ("C5", 1), ("E5", 2)]),
    "service-logout":        ezgi([("E5", 1), ("C5", 1), ("A4", 2)]),
    # iletişim kutuları
    "dialog-information":    ezgi([("E5", 1), ("A5", 1), ("E5", 2)]),
    "dialog-question":       ezgi([("A4", 1), ("C5", 1), ("D5", 2)]),              # çözülmeden asılı kalır
    "dialog-warning":        ezgi([("E5", 1), ("E5", 1), ("F5", 2)]),              # yarım ses: gerginlik
    "dialog-warning-auth":   ezgi([("A4", 1), ("A4", 1)], yanki=False),
    "dialog-error":          ezgi([("A4", 1), ("D#4", 1), ("A3", 2)]),             # üçlü ses aralığı: "yanlış"
    "dialog-error-serious":  ezgi([("A3", 1, "D#4"), (None, 0.5), ("A3", 1, "D#4"), (None, 0.5), ("A2", 3, "D#3")]),
    # sonuçlar
    "completion-success":    ezgi([("A4", 1), ("C5", 1), ("E5", 1), ("A5", 2)]),
    "outcome-success":       ezgi([("C5", 1), ("E5", 1), ("A5", 2, "E5")]),
    "completion-partial":    ezgi([("A4", 1), ("C5", 1), ("B4", 2)]),
    "completion-fail":       ezgi([("E5", 1), ("C5", 1), ("A4", 1), ("F4", 2)]),
    "outcome-failure":       ezgi([("C5", 1), ("G#4", 1), ("F4", 2)]),
    "completion-rotation":   ezgi([("A4", 0.5), ("C5", 0.5), ("E5", 0.5), ("C5", 0.5), ("A4", 1)]),
    # aygıt ve güç
    "device-added":          ezgi([("E4", 1), ("A4", 1), ("E5", 2)]),
    "device-removed":        ezgi([("E5", 1), ("A4", 1), ("E4", 2)]),
    "power-plug":            ezgi([("A3", 1), ("A4", 1), ("E5", 2)]),
    "power-unplug":          ezgi([("E5", 1), ("A4", 1), ("A3", 2)]),
    "battery-low":           ezgi([("E4", 2), ("C4", 2), ("A3", 3)]),
    "battery-caution":       ezgi([("A4", 1), (None, 0.5), ("A4", 1), (None, 0.5), ("A4", 1), (None, 0.5), ("D#4", 3)]),
    # iletiler
    "message-new-instant":   ezgi([("E5", 1), ("A5", 1), ("C6", 2)]),
    "message-new-email":     ezgi([("C5", 1), ("E5", 1), ("A5", 1), ("E5", 2)]),
    # sık çalanlar: bilerek kısa
    "bell-window-system":    ezgi([("A5", 0.6), ("E5", 1)], yanki=False),
    "audio-volume-change":   ezgi([("A5", 0.5)], yanki=False),
    "button-pressed":        ezgi([("A4", 0.3)], yanki=False),
    "button-pressed-modifier": ezgi([("E5", 0.3)], yanki=False),
    # diğer
    "trash-empty":           ezgi([("gurultu", 1, 9000), ("gurultu", 1, 5000), ("gurultu", 2, 2400), ("A3", 2)]),
    "alarm-clock-elapsed":   ezgi([("A5", 1), ("E5", 1), ("A5", 1), ("E5", 1), (None, 2)] * 3 + [("A5", 3, "E5")]),
    "phone-incoming-call":   ezgi([("E5", 1, "A5"), ("C5", 1, "E5"), ("E5", 1, "A5"), ("C5", 1, "E5"), (None, 4)] * 3),
}

# Aynı sesi paylaşan olaylar (Ocean temasındaki eşleşmeler)
BAGLAR = {
    "bell": "bell-window-system", "battery-full": "outcome-success", "theme-demo": "desktop-login",
    "dialog-error-critical": "dialog-error-serious", "complete-media-burn": "outcome-success",
    "complete-media-error": "completion-partial", "game-over-loser": "outcome-failure",
    "game-over-winner": "service-login", "media-insert-request": "completion-rotation",
    "message-attention": "outcome-success", "message-contact-in": "completion-success",
    "message-contact-out": "completion-fail", "message-highlight": "completion-partial",
    "message-sent-instant": "service-login",
}

TEMA = """[Sound Theme]
Name=TRS Kare
Comment=Kare dalga sistem sesleri (TRS)
Inherits=ocean
Directories=stereo
Example=theme-demo

[stereo]
OutputProfile=stereo
"""


def yaz(ses, dosya):
    veri = (np.clip(ses, -1, 1) * 32767).astype("<i2")
    cift = np.column_stack([veri, veri]).tobytes()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as gecici:
        with wave.open(gecici, "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(HIZ)
            w.writeframes(cift)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", gecici.name, "-c:a", "libvorbis", "-q:a", "5",
                    "-f", "ogg", str(dosya)], check=True)
    Path(gecici.name).unlink()


def uret(hedef):
    if hedef.exists():
        if "TRS Kare" not in (hedef / "index.theme").read_text():
            sys.exit(f"{hedef} bir TRS Kare ses teması değil, silinmedi")
        shutil.rmtree(hedef)
    (hedef / "stereo").mkdir(parents=True)
    (hedef / "index.theme").write_text(TEMA)
    for ad, ses in SESLER.items():
        yaz(ses, hedef / "stereo" / f"{ad}.oga")
    for ad, asil in BAGLAR.items():
        (hedef / "stereo" / f"{ad}.oga").symlink_to(f"{asil}.oga")
    return hedef


if __name__ == "__main__":
    hedef = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / ".local/share/sounds/trs-kare"
    uret(hedef)
    print(f"üretildi: {hedef} ({len(SESLER)} ses, {len(BAGLAR)} bağ)")
    for ad, ses in sorted(SESLER.items(), key=lambda x: len(x[1])):
        print(f"  {ad:26} {len(ses) / HIZ:5.2f} sn")
