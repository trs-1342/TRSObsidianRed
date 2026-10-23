#!/usr/bin/python3
"""TRS Kare önyükleme ekranı (Plymouth) temasını SIFIRDAN üretir:  uret.py [hedef dizin]

Fedora yüklenirken ve disk parolası sorulurken HP logosu yerine kırmızı zemin ve ortada siyah kare.
  • Yüklenirken: ortadaki siyah karenin içinde dışa doğru akan iç içe kareler (işlem sürüyor işareti).
  • Parola:      kare yana doğru büyüyüp giriş kutusu olur. Ekranın her yerinden siyah kareler
                 küçülerek kutuya doğru çekilir ve kutuda kaybolur; döngü parola girilene kadar sürer.
                 Yazılan her tuş bitişik bir kırmızı kare ekler; kutu soldan sağa dolar.
  • Kapanırken:  açılışın tersi. Siyah kareler ortadaki kareden çıkıp büyüyerek ekranın her yerine
                 saçılır; karenin içindeki iç içe kareler de içe doğru akar.
Yalnızca kırmızı ve siyah kullanılır; bütün parçalar tam karedir (dikdörtgen yalnızca giriş kutusu).

Plymouth'un "script" eklentisini kullanır (paket: plymouth-plugin-script; kur.sh kurar). Hareketsiz,
eklentisiz eski sürüm: uret_sade.py.
"""
import random
import shutil
import sys
from pathlib import Path

from PIL import Image

KIRMIZI = (0xC1, 0x12, 0x1F)
KARE = 26             # kutuya çekilen kare sayısı (13 x 2)
TOHUM = 1342          # her açılışta aynı düzen
EN_COK_NOKTA = 26     # giriş kutusuna sığan kırmızı kare sayısı (13 x 2); her tuş bir kare

TEMA = """[Plymouth Theme]
Name=TRS Kare
Description=Red background; black squares shrink into the password box.
ModuleName=script

[script]
ImageDir=/usr/share/plymouth/themes/trs-kare
ScriptFile=/usr/share/plymouth/themes/trs-kare/trs-kare.script
"""

BETIK = """# TRS Kare — Plymouth betiği. Bu dosya uret.py tarafından üretilir, elle düzenleme.

Window.SetBackgroundTopColor (%(r).3f, %(g).3f, %(b).3f);
Window.SetBackgroundBottomColor (%(r).3f, %(g).3f, %(b).3f);

siyah = Image ("siyah.png");
kirmizi = Image ("kirmizi.png");

ekran.x = Window.GetX ();
ekran.y = Window.GetY ();
ekran.w = Window.GetWidth ();
ekran.h = Window.GetHeight ();
orta.x = ekran.x + ekran.w / 2;
orta.y = ekran.y + ekran.h / 2;

KENAR = Math.Int (Math.Min (ekran.w, ekran.h) / 12);   # orta karenin kenarı
GIRIS_EN = KENAR * 4;                                  # giriş kutusunun kareye eklenen eni
KARE = %(kare)d;
EN_COK = %(en_cok)d;

durum = "normal";
# Kapatma ve yeniden başlatmada her şey tersine akar
kip = Plymouth.GetMode ();
kapanis = 0;
if (kip == "shutdown" || kip == "reboot")
  kapanis = 1;
sayac = 0;              # saniye cinsinden geçen süre (yaklaşık)
# Giriş kutusu: EN_COK tane bitişik kare sığar; kareler kutunun yarı boyundadır
NOKTA_BOY = Math.Int (KENAR / 2);
KUTU_PAY = Math.Int ((KENAR - NOKTA_BOY) / 2);
KUTU_EN = EN_COK * NOKTA_BOY + 2 * KUTU_PAY;
hedef_en = KENAR;       # orta kutunun eni: kare iken KENAR, parola istenince KUTU_EN
kutu_en = KENAR;
govde_en = 0;

#----------------------------------------- Çekilen kareler ----------------------------
# bx, by: başlangıç (ekranın oranı) · hx: kutuda vardığı nokta (kutu eninin oranı, -0.5..0.5)
# boy: başlangıç kenarı (orta karenin katı) · hiz: saniyede tur · faz: döngüdeki yeri

%(kareler)s
for (i = 0; i < KARE; i++)
  {
    kare[i] = Sprite ();
    kare[i].SetOpacity (0);
    kson[i] = 0;
  }

fun kareler_ciz ()
  {
    for (k = 0; k < KARE; k++)
      {
        u = global.sayac * khiz[k] + kfaz[k];
        u = u - Math.Int (u);
        if (kapanis)
          u = 1 - u;                                   # tersine: kutudan çıkıp dışarı saçılır
        yak = u * u;                                   # kutuya yakınken hızlı, uzakta yavaş
        boy = Math.Int (kboy[k] * KENAR * (1 - yak)) + 2;
        x0 = ekran.x + ekran.w * kbx[k];
        y0 = ekran.y + ekran.h * kby[k];
        x = x0 + (orta.x + khx[k] * (global.kutu_en - KENAR / 2) - x0) * yak;
        y = y0 + (orta.y - y0) * yak;
        if (boy != global.kson[k])
          {
            global.kson[k] = boy;
            kare[k].SetImage (siyah.Scale (boy, boy));
          }
        kare[k].SetPosition (x - boy / 2, y - boy / 2, 10);
        kare[k].SetOpacity (Math.Min (1, u * 8));      # döngü başında birden belirmesin
      }
  }

fun kareler_gizle ()
  {
    for (k = 0; k < KARE; k++)
      kare[k].SetOpacity (0);
  }

#----------------------------------------- Orta kutu ----------------------------------

govde = Sprite ();

fun govde_ciz ()
  {
    genislik = Math.Int (global.kutu_en);
    if (genislik != global.govde_en)
      {
        global.govde_en = genislik;
        govde.SetImage (siyah.Scale (genislik, KENAR));
        govde.SetPosition (orta.x - genislik / 2, orta.y - KENAR / 2, 1000);
      }
  }

# Her tuş için bir kırmızı kare; aralarında boşluk yoktur, kutu soldan sağa dolar
nokta_resim = kirmizi.Scale (NOKTA_BOY, NOKTA_BOY);
nokta_sol = orta.x - KUTU_EN / 2 + KUTU_PAY;
for (i = 0; i < EN_COK; i++)
  {
    nokta[i] = Sprite (nokta_resim);
    nokta[i].SetPosition (nokta_sol + i * NOKTA_BOY, orta.y - NOKTA_BOY / 2, 1001);
    nokta[i].SetOpacity (0);
  }

#----------------------------------------- Karenin içi --------------------------------
# Yüklenirken orta karenin içinde dışa doğru akan iç içe kareler (siyah/kırmızı sırayla).
# Büyükten küçüğe üst üste beş dolu kare çizilir; en dıştaki ince siyah kenar hep kalır.

IC = 5;
IC_KALIN = Math.Int (KENAR / 6);
IC_SINIR = Math.Int (KENAR / 2) - 3;
ic_acik = 0;
for (i = 0; i < IC; i++)
  {
    ic[i] = Sprite ();
    ic[i].SetOpacity (0);
    icson[i] = 0;
  }

fun ic_ciz ()
  {
    kayma = global.sayac - Math.Int (global.sayac);    # saniyede bir tur
    if (kapanis)
      kayma = 1 - kayma;                               # kapanırken içe doğru akar
    kayma = kayma * 2 * IC_KALIN;
    for (k = 0; k < IC; k++)
      {
        yari = Math.Int (Math.Min (kayma + IC_KALIN * (3 - k), IC_SINIR));
        if (yari < 1)
          ic[k].SetOpacity (0);
        else
          {
            if (yari != global.icson[k])
              {
                global.icson[k] = yari;
                if (k - 2 * Math.Int (k / 2) == 0)
                  ic[k].SetImage (siyah.Scale (2 * yari, 2 * yari));
                else
                  ic[k].SetImage (kirmizi.Scale (2 * yari, 2 * yari));
              }
            ic[k].SetPosition (orta.x - yari, orta.y - yari, 1002 + k);
            ic[k].SetOpacity (1);
          }
      }
    global.ic_acik = 1;
  }

fun ic_gizle ()
  {
    if (global.ic_acik)
      {
        for (k = 0; k < IC; k++)
          ic[k].SetOpacity (0);
        global.ic_acik = 0;
      }
  }

yazi = Sprite ();
yazi.SetOpacity (0);

fun yazi_goster (metin)
  {
    if (metin)
      {
        resim = Image.Text (metin, 0, 0, 0);
        yazi.SetImage (resim);
        yazi.SetPosition (orta.x - resim.GetWidth () / 2, orta.y + KENAR, 1001);
        yazi.SetOpacity (1);
      }
    else
      yazi.SetOpacity (0);
  }

#----------------------------------------- Döngü --------------------------------------

fun yenile ()
  {
    global.sayac += 0.02;                              # saniyede 50 çizim
    # kare ile giriş kutusu arasında yumuşak geçiş
    global.kutu_en += (global.hedef_en - global.kutu_en) * 0.18;
    if (global.hedef_en - global.kutu_en < 1 && global.kutu_en - global.hedef_en < 1)
      global.kutu_en = global.hedef_en;
    govde_ciz ();
    if (global.durum != "normal" || kapanis)
      kareler_ciz ();
    # iç içe kareler yalnızca yüklenirken ve kutu yeniden kare olduğunda görünür
    if (global.durum == "normal" && global.kutu_en == KENAR)
      ic_ciz ();
    else
      ic_gizle ();
  }

Plymouth.SetRefreshFunction (yenile);

#----------------------------------------- Durumlar -----------------------------------

fun normal_goster ()
  {
    global.durum = "normal";
    global.hedef_en = KENAR;
    if (!kapanis)
      kareler_gizle ();
    for (i = 0; i < EN_COK; i++)
      nokta[i].SetOpacity (0);
    yazi.SetOpacity (0);
  }

fun parola_goster (istem, nokta_sayisi)
  {
    global.durum = "parola";
    global.hedef_en = KUTU_EN;
    for (i = 0; i < EN_COK; i++)
      {
        if (i < nokta_sayisi)
          nokta[i].SetOpacity (1);
        else
          nokta[i].SetOpacity (0);
      }
    yazi_goster (istem);
  }

fun soru_goster (istem, girilen)
  {
    global.durum = "soru";
    global.hedef_en = KUTU_EN;
    for (i = 0; i < EN_COK; i++)
      nokta[i].SetOpacity (0);
    yazi_goster (istem + " " + girilen);
  }

Plymouth.SetDisplayNormalFunction (normal_goster);
Plymouth.SetDisplayPasswordFunction (parola_goster);
Plymouth.SetDisplayQuestionFunction (soru_goster);

#----------------------------------------- İletiler -----------------------------------

ileti = Sprite ();

fun ileti_goster (metin)
  {
    resim = Image.Text (metin, 0, 0, 0);
    ileti.SetImage (resim);
    ileti.SetPosition (orta.x - resim.GetWidth () / 2, ekran.y + ekran.h * 0.9, 1001);
    ileti.SetOpacity (1);
  }

fun ileti_gizle (metin)
  {
    ileti.SetOpacity (0);
  }

Plymouth.SetDisplayMessageFunction (ileti_goster);
Plymouth.SetHideMessageFunction (ileti_gizle);

#----------------------------------------- Güncelleme ilerlemesi ----------------------

cubuk = Sprite ();
cubuk_en = 0;

fun guncelleme (yuzde)
  {
    en = Math.Int (GIRIS_EN * yuzde / 100);
    if (en >= 1 && en != global.cubuk_en)
      {
        global.cubuk_en = en;
        cubuk.SetImage (siyah.Scale (en, Math.Max (2, Math.Int (KENAR / 16))));
        cubuk.SetPosition (orta.x - GIRIS_EN / 2, ekran.y + ekran.h * 0.8, 1001);
      }
  }

Plymouth.SetSystemUpdateFunction (guncelleme);
"""


def kareler():
    """Çekilen karelerin sabit tohumlu listesi; ekranın her yerinden, orta bölge hariç."""
    r = random.Random(TOHUM)
    liste = []
    while len(liste) < KARE:
        # dört çeyreğe sırayla dağıt ki ekranın bir yanı boş kalmasın
        ceyrek = len(liste) % 4
        bx = r.uniform(-0.03, 0.5) + (0.53 if ceyrek in (1, 3) else 0)
        by = r.uniform(-0.05, 0.5) + (0.55 if ceyrek in (2, 3) else 0)
        if abs(bx - 0.5) < 0.36 and abs(by - 0.5) < 0.2:
            continue                                   # kutunun dibinde doğmasın
        liste.append({
            "bx": bx, "by": by,
            "hx": r.uniform(-0.42, 0.42),
            "boy": r.uniform(0.45, 1.9),
            "hiz": 1 / r.uniform(2.6, 5.2),            # kenardan kutuya 2,6–5,2 saniye
            "faz": r.random(),
        })
    return liste


def uret(hedef):
    if hedef.exists():
        if not (hedef / "trs-kare.plymouth").exists():
            sys.exit(f"{hedef} bir TRS Kare teması değil, silinmedi")
        shutil.rmtree(hedef)
    hedef.mkdir(parents=True)
    (hedef / "trs-kare.plymouth").write_text(TEMA)
    satirlar = []
    for i, k in enumerate(kareler()):
        satirlar.append(f"kbx[{i}] = {k['bx']:.4f}; kby[{i}] = {k['by']:.4f}; khx[{i}] = {k['hx']:.4f}; "
                        f"kboy[{i}] = {k['boy']:.3f}; khiz[{i}] = {k['hiz']:.4f}; kfaz[{i}] = {k['faz']:.4f};")
    (hedef / "trs-kare.script").write_text(BETIK % {
        "r": KIRMIZI[0] / 255, "g": KIRMIZI[1] / 255, "b": KIRMIZI[2] / 255,
        "kare": KARE, "en_cok": EN_COK_NOKTA, "kareler": "\n".join(satirlar),
    })
    for ad, renk in (("siyah", (0, 0, 0)), ("kirmizi", KIRMIZI)):
        Image.new("RGBA", (8, 8), renk + (255,)).save(hedef / f"{ad}.png")
    return hedef


def an_ciz(tuval, ust, sayac, parola):
    """Betikteki hesabın aynısıyla tek bir anı çizer (önizleme için; yazılar hariç)."""
    W, H = 1920, 1080
    ox, oy = W / 2, ust + H / 2
    kenar = min(W, H) // 12
    nokta = kenar // 2
    pay = (kenar - nokta) // 2
    kutu = EN_COK_NOKTA * nokta + 2 * pay
    px = tuval.load()

    def doldur(x, y, w, h, renk):
        for yy in range(max(ust, int(y)), min(ust + H, int(y) + int(h))):
            for xx in range(max(0, int(x)), min(W, int(x) + int(w))):
                px[xx, yy] = renk

    if parola:
        for k in kareler():
            u = (sayac * k["hiz"] + k["faz"]) % 1
            yak = u * u
            boy = int(k["boy"] * kenar * (1 - yak)) + 2
            x0, y0 = W * k["bx"], ust + H * k["by"]
            x = x0 + (ox + k["hx"] * (kutu - kenar / 2) - x0) * yak
            y = y0 + (oy - y0) * yak
            doldur(x - boy / 2, y - boy / 2, boy, boy, (0, 0, 0))
    en = kutu if parola else kenar
    doldur(ox - en / 2, oy - kenar / 2, en, kenar, (0, 0, 0))
    if parola:
        for i in range(17):                            # örnek: 17 tuş yazılmış
            doldur(ox - kutu / 2 + pay + i * nokta, oy - nokta / 2, nokta, nokta, KIRMIZI)
    else:
        kalin, sinir = kenar // 6, kenar // 2 - 3
        kayma = (sayac % 1) * 2 * kalin
        for k in range(5):
            yari = int(min(kayma + kalin * (3 - k), sinir))
            if yari >= 1:
                doldur(ox - yari, oy - yari, 2 * yari, 2 * yari, (0, 0, 0) if k % 2 == 0 else KIRMIZI)


def onizle(dosya):
    """Üstte yüklenme, altta parola anı."""
    W, H = 1920, 1080
    tuval = Image.new("RGB", (W, 2 * H + 8), KIRMIZI)
    an_ciz(tuval, 0, 0.3, False)
    an_ciz(tuval, H + 8, 7.3, True)
    for x in range(W):
        for y in range(H, H + 8):
            tuval.putpixel((x, y), (60, 60, 60))
    tuval.resize((W // 2, H + 4)).save(dosya)


if __name__ == "__main__":
    hedef = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "trs-kare"
    uret(hedef)
    onizle(Path(__file__).parent / "onizleme.png")
    print(f"üretildi: {hedef} ({len(list(hedef.iterdir()))} dosya)")
