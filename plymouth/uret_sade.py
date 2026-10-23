#!/usr/bin/python3
"""(ESKİ, yalın sürüm: hareketsiz parola ekranı, two-step eklentisi.) Geri dönmek için: python3 uret_sade.py && sudo bash kur.sh

TRS Kare önyükleme ekranı (Plymouth) temasını SIFIRDAN üretir:  uret_sade.py [hedef dizin]

Fedora yüklenirken ve disk parolası sorulurken HP logosu yerine kırmızı zemin ve ortada siyah kare gösterir.
Plymouth'un hazır "two-step" eklentisini kullanır (Fedora'nın kendi temasıyla aynı), yeni eklenti gerekmez.
  • Yüklenirken: ortadaki karenin içinde dışa doğru akan iç içe kareler (siyah/kırmızı sırayla).
  • Parola:      ortada siyah şerit (kare + giriş alanı), yazılan her tuş için kırmızı küçük kare.
"""
import shutil
import sys
from pathlib import Path

from PIL import Image

KIRMIZI = (0xC1, 0x12, 0x1F)
SIYAH = (0, 0, 0, 255)
BOS = (0, 0, 0, 0)
KENAR = 90            # orta kare (1080 / 12)
HALKA = 15            # iç içe karelerin kalınlığı
KARE_SAYISI = 2 * HALKA   # bir tam döngü
GIRIS_EN = 4 * KENAR
HAZIR = Path("/usr/share/plymouth/themes/spinner")   # klavye/caps simgeleri buradan alınır

TEMA = """[Plymouth Theme]
Name=TRS Kare
Description=Red background, black square in the center.
ModuleName=two-step

[two-step]
Font=Cantarell 12
TitleFont=Cantarell Light 30
ImageDir=/usr/share/plymouth/themes/trs-kare
DialogHorizontalAlignment=.5
DialogVerticalAlignment=.5
TitleHorizontalAlignment=.5
TitleVerticalAlignment=.382
HorizontalAlignment=.5
VerticalAlignment=.5
Transition=none
TransitionDuration=0.0
BackgroundStartColor=0xc1121f
BackgroundEndColor=0xc1121f
ProgressBarBackgroundColor=0x8a0d16
ProgressBarForegroundColor=0x000000
MessageBelowAnimation=true

[boot-up]
UseEndAnimation=false

[shutdown]
UseEndAnimation=false

[reboot]
UseEndAnimation=false

[updates]
SuppressMessages=true
ProgressBarShowPercentComplete=true
UseProgressBar=true
Title=Installing Updates...
SubTitle=Do not turn off your computer

[system-upgrade]
SuppressMessages=true
ProgressBarShowPercentComplete=true
UseProgressBar=true
Title=Upgrading System...
SubTitle=Do not turn off your computer

[firmware-upgrade]
SuppressMessages=true
ProgressBarShowPercentComplete=true
UseProgressBar=true
Title=Upgrading Firmware...
SubTitle=Do not turn off your computer

[system-reset]
SuppressMessages=true
ProgressBarShowPercentComplete=true
UseProgressBar=true
Title=Resetting System...
SubTitle=Do not turn off your computer
"""


def halkali_kare(kayma):
    """Merkezden dışa akan iç içe kareler; en dış halka hep siyah kalır ki kare sınırı sabit dursun."""
    im = Image.new("RGBA", (KENAR, KENAR), BOS)
    px = im.load()
    orta = (KENAR - 1) / 2
    for y in range(KENAR):
        for x in range(KENAR):
            d = max(abs(x - orta), abs(y - orta))          # kare biçimli uzaklık
            if d > orta - 3 or int((d - kayma) // HALKA) % 2 == 0:
                px[x, y] = SIYAH
    return im


def uret(hedef):
    if hedef.exists():
        if not (hedef / "trs-kare.plymouth").exists():
            sys.exit(f"{hedef} bir TRS Kare teması değil, silinmedi")
        shutil.rmtree(hedef)
    hedef.mkdir(parents=True)
    (hedef / "trs-kare.plymouth").write_text(TEMA)
    for i in range(KARE_SAYISI):
        halkali_kare(i).save(hedef / f"throbber-{i + 1:04d}.png")
    duz = Image.new("RGBA", (KENAR, KENAR), SIYAH)
    duz.save(hedef / "animation-0001.png")
    duz.save(hedef / "lock.png")
    Image.new("RGBA", (GIRIS_EN, KENAR), SIYAH).save(hedef / "entry.png")
    Image.new("RGBA", (14, 14), KIRMIZI + (255,)).save(hedef / "bullet.png")
    for ad in ("capslock.png", "keyboard.png", "keymap-render.png"):
        shutil.copy(HAZIR / ad, hedef / ad)
    return hedef


def onizle(tema, dosya):
    """İki durumu yan yana gösteren yaklaşık önizleme (yerleşim Plymouth'unkiyle birebir olmayabilir)."""
    W, H = 1920, 1080
    tuval = Image.new("RGB", (W, 2 * H), KIRMIZI)
    kare = Image.open(tema / "throbber-0008.png")
    tuval.paste(kare, ((W - KENAR) // 2, (H - KENAR) // 2), kare)
    kilit, giris, nokta = (Image.open(tema / f"{a}.png") for a in ("lock", "entry", "bullet"))
    x0 = (W - KENAR - GIRIS_EN) // 2
    y0 = H + (H - KENAR) // 2
    tuval.paste(kilit, (x0, y0), kilit)
    tuval.paste(giris, (x0 + KENAR, y0), giris)
    for i in range(9):
        tuval.paste(nokta, (x0 + KENAR + 24 + i * 26, y0 + (KENAR - 14) // 2), nokta)
    tuval.resize((W // 2, H)).save(dosya)


if __name__ == "__main__":
    hedef = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "trs-kare"
    uret(hedef)
    onizle(hedef, Path(__file__).parent / "onizleme.png")
    print(f"üretildi: {hedef} ({len(list(hedef.iterdir()))} dosya)")
