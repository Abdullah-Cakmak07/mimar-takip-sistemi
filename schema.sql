DROP TABLE IF EXISTS Kullanicilar;
DROP TABLE IF EXISTS Musteriler;
DROP TABLE IF EXISTS Projeler;
DROP TABLE IF EXISTS Asamalar;

-- Kullanicilar tablosuna kayit_tarihi eklendi
CREATE TABLE IF NOT EXISTS Kullanicilar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_soyad TEXT NOT NULL,
    kullanici_adi TEXT UNIQUE NOT NULL,
    sifre TEXT NOT NULL,
    rol TEXT DEFAULT 'mimar',
    tema_tercihi TEXT DEFAULT 'light',
    email_bildirim INTEGER DEFAULT 1,   
    kayit_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Proje sahipleri (Login olmazlar, sadece bilgi amaçlı)
CREATE TABLE IF NOT EXISTS Musteriler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ekleyen_id INTEGER,
    ad_soyad TEXT NOT NULL,
    tc_no TEXT,
    telefon TEXT,
    eposta TEXT,
    FOREIGN KEY (ekleyen_id) REFERENCES Kullanicilar (id)
);
CREATE TABLE Projeler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kullanici_id INTEGER, -- Projeyi yöneten mimar
    musteri_id INTEGER,   -- Proje sahibi müşteri
    proje_adi TEXT,
    proje_tipi TEXT,
    il TEXT, ilce TEXT, mahalle TEXT,
    ada TEXT, parsel TEXT,
    teslim_tarihi TEXT,
    FOREIGN KEY (kullanici_id) REFERENCES Kullanicilar (id),
    FOREIGN KEY (musteri_id) REFERENCES Musteriler (id)
);

-- 1. Varsayılan Şablon Tablosu
CREATE TABLE IF NOT EXISTS VarsayilanAsamalar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asama_adi TEXT NOT NULL,
    ust_id INTEGER DEFAULT NULL, -- Eğer ana başlıksa NULL, alt başlıksa ana başlığın ID'si
    FOREIGN KEY (ust_id) REFERENCES VarsayilanAsamalar(id)
);

-- 2. Projeye Özel Aşamalar Tablosu
-- Bu tablo, her yeni proje açıldığında yukarıdaki şablondan kopyalanacak
CREATE TABLE IF NOT EXISTS Asamalar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proje_id INTEGER,
    asama_adi TEXT NOT NULL,
    ust_id INTEGER DEFAULT NULL,
    tamamlandi INTEGER DEFAULT 0, -- 0: Bekliyor, 1: Tamamlandı
    FOREIGN KEY (proje_id) REFERENCES Projeler(id)
);


-- Proje Dosyaları ve Fotoğrafları İçin Tablo
CREATE TABLE IF NOT EXISTS ProjeDosyalari (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proje_id INTEGER,
    dosya_adi TEXT,
    dosya_yolu TEXT,
    dosya_tipi TEXT, -- 'resim' veya 'dokuman'
    yukleme_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (proje_id) REFERENCES Projeler(id)
);

-- Kullanıcılar tablosuna profil resmi sütununu ekle (Eğer yoksa)
ALTER TABLE Kullanicilar ADD COLUMN profil_resmi TEXT DEFAULT 'default.png';

CREATE TABLE IF NOT EXISTS Odemeler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proje_id INTEGER,
    miktar REAL NOT NULL,
    odeme_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
    acıklama TEXT,
    FOREIGN KEY (proje_id) REFERENCES Projeler(id)
);

-- Projeler tablosuna toplam proje bedelini saklayacak bir kolon ekleyelim (Eğer yoksa)
ALTER TABLE Projeler ADD COLUMN toplam_bedel REAL DEFAULT 0;

