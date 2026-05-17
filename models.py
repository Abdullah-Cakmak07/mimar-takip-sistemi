class Proje:
    def __init__(self, id, proje_adi, musteri_adi, yuzde, teslim_tarihi, il, ilce):
        self.id = id
        self.proje_adi = proje_adi
        self.musteri_adi = musteri_adi if musteri_adi else "Tanımsız Müşteri"
        self.yuzde = int(yuzde)
        self.teslim_tarihi = teslim_tarihi
        self.lokasyon = f"{il} / {ilce}"

    def durum_etiketi(self):
        """Projenin ilerlemesine göre Bootstrap badge sınıfı döndürür."""
        if self.yuzde == 100: return "success"
        if self.yuzde > 70: return "info"
        if self.yuzde > 30: return "primary"
        return "warning"

    def tamamlandi_mi(self):
        return self.yuzde == 100

class Musteri:
    def __init__(self, id, ad_soyad, tc_no, telefon, eposta):
        self.id = id
        self.ad_soyad = ad_soyad
        self.tc_no = tc_no
        self.telefon = telefon
        self.eposta = eposta