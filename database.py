import sqlite3
import os

def init_db():
    print("Veritabanı kurulumu başlatılıyor...")
    if os.path.exists('data.db'):
        os.remove('data.db')
        print("Eski 'data.db' silindi.")

    conn = sqlite3.connect('data.db')
    with open('schema.sql', 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    
    # PDF'teki Aşamaları Sisteme Yükle
    asamalar = [
        # (Aşama Adı, Üst ID) -> Üst ID None ise Ana Başlıktır
        ("1- Aplikasyon Krokisi", None),
        ("Evraklar Gönderildi", 1), ("Evrak Alındı", 1),
        
        ("2- İmar Durumu", None),
        ("Başvuru Yapıldı", 4), ("Evrak Alındı", 4),
        
        ("3- Taslak Çizildi - Uygulama Başlandı", None),
        
        ("4- Tus Dosyası", None),
        ("Evraklar Gönderildi", 8), ("Evraklar Alındı", 8),
        
        ("5- Numarataj Belgesi", None),
        ("Başvuru Yapıldı", 11), ("Evrak Alındı", 11),
        
        ("6- Mimari Proje Ön Onay Başvurusu", None),
        ("7- Kanal Kotu (Başvuru ve Evrak)", None),
        ("8- Zemin Etüdü (Mühendise Gönderildi)", None),
        ("9- Mimari Proje Onayı Alındı", None),
        ("10- Diğer Projeler Müelliflere Gönderildi", None),
        
        ("11- İzsu Kanal Katılım", None),
        ("Başvuru Yapıldı", 18), ("Evrak Alındı", 18),
        
        ("12- Projenin YDS Kaydı Oluşturuldu", None),
        ("13- Yapı Denetimi Atandı / Anlaşma Sağlandı", None),
        ("14- Tüm Çizimler Tamamlandı ve Onaylandı", None),
        ("15- Hafriyat Başvurusu Yapıldı", None),
        
        ("16- Yapı Ruhsatı", None),
        ("Başvuru Yapıldı", 24), ("Ruhsat Alındı", 24),
        
        ("17- Vize Başvuruları Yapıldı", None),
        
        ("18- Kat İrtifakı / Tapular", None),
        ("Başvuru Yapıldı", 28), ("Tapular Çıkarıldı", 28),
        
        ("19- İzsu Karşı Ruhsatı (Başvuru ve Evrak)", None),
        ("20- İş Bitirme Başvurusu / Onayı", None),
        ("21- Yapı Kullanma Ruhsatı (İskan)", None)
    ]
    
    for ad, ust in asamalar:
        conn.execute("INSERT INTO VarsayilanAsamalar (asama_adi, ust_id) VALUES (?, ?)", (ad, ust))
    
    conn.commit()
    conn.close()
    print("BAŞARILI: Hiyerarşik aşamalar ve otomatik finansal takip yapısı kuruldu!")

if __name__ == "__main__":
    init_db()