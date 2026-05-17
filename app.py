import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
import os
import json
import io
import csv
import uuid
import re 
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

app = Flask(__name__)
app.secret_key = "mimar_proje_takip_gizli_key_123"

# Dosya yolları tanımlamaları
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_PROFIL = os.path.join(BASE_DIR, 'static', 'uploads', 'profil')
UPLOAD_PROJE = os.path.join(BASE_DIR, 'static', 'uploads', 'projeler')

class MimarTakipSistemi:
    def __init__(self, app):
        self.app = app
        self.setup_routes()
        self.create_folders()

    def create_folders(self):
        """Gerekli klasörleri otomatik oluşturur."""
        for path in [UPLOAD_PROFIL, UPLOAD_PROJE]:
            if not os.path.exists(path):
                os.makedirs(path)

    def get_db(self):
        """Veritabanı bağlantısını sağlayan merkezi metod."""
        db_path = os.path.join(os.path.dirname(__file__), 'data.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def setup_routes(self):
        """
        Tüm URL yönlendirmelerini merkezi olarak tanımlar.
        HTML dosyalarındaki url_for() çağrıları ile buradaki endpoint isimleri eşleşmelidir.
        """
        
        # --- GENEL VE KİMLİK DOĞRULAMA ---
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/login', 'login', self.login, methods=['GET', 'POST'])
        self.app.add_url_rule('/logout', 'logout', self.logout)
        self.app.add_url_rule('/register', 'register', self.register, methods=['GET', 'POST'])
        
        # --- MÜŞTERİ YÖNETİMİ ---
        self.app.add_url_rule('/musteriler', 'musteriler', self.musteriler, methods=['GET', 'POST'])
        self.app.add_url_rule('/musteri_ekle', 'musteri_ekle', self.musteri_ekle, methods=['POST'])
        self.app.add_url_rule('/musteri_duzenle/<int:id>', 'musteri_duzenle', self.musteri_duzenle, methods=['GET', 'POST'])
        self.app.add_url_rule('/musteri_sil/<int:id>', 'musteri_sil', self.musteri_sil)
        
        # --- PROJE YÖNETİMİ ---
        self.app.add_url_rule('/projelerim', 'projelerim', self.projelerim)
        self.app.add_url_rule('/proje_ekle', 'proje_ekle', self.proje_ekle, methods=['GET', 'POST'])
        self.app.add_url_rule('/proje_detay/<int:id>', 'proje_detay', self.proje_detay)
        self.app.add_url_rule('/proje_duzenle/<int:id>', 'proje_duzenle', self.proje_duzenle, methods=['GET', 'POST'])
        self.app.add_url_rule('/proje_sil/<int:id>', 'proje_sil', self.proje_sil)
        self.app.add_url_rule('/proje_indir/<int:id>', 'proje_indir', self.proje_indir)
        
        # --- SÜREÇ, FİNANS VE DOSYA İŞLEMLERİ ---
        self.app.add_url_rule('/asama_guncelle', 'asama_guncelle', self.asama_guncelle, methods=['POST'])
        self.app.add_url_rule('/odeme_ekle/<int:proje_id>', 'odeme_ekle', self.odeme_ekle, methods=['POST'])
        self.app.add_url_rule('/proje_dosya_yukle/<int:proje_id>', 'dosya_yukle', self.proje_dosya_yukle, methods=['POST'])
        
        # --- ADMİN VE KULLANICI YÖNETİMİ ---
        # HTML dosyalarında url_for('kullanicilar') kullanıldığı için endpoint ismini 'kullanicilar' yaptık
        self.app.add_url_rule('/kullanicilar', 'kullanicilar', self.kullanici_sayfasi, methods=['GET', 'POST'])
        self.app.add_url_rule('/kullanici_ekle', 'kullanici_ekle', self.kullanici_ekle, methods=['POST'])
        self.app.add_url_rule('/kullanici_sil/<int:id>', 'kullanici_sil', self.kullanici_sil)
        
        # --- AYARLAR VE PROFİL ---
        self.app.add_url_rule('/ayarlar', 'ayarlar', self.ayarlar, methods=['GET', 'POST'])
        self.app.add_url_rule('/profil_resmi_guncelle', 'profil_resmi_guncelle', self.profil_resmi_guncelle, methods=['POST'])
        self.app.add_url_rule('/asama_varsayilan_ekle', 'asama_varsayilan_ekle', self.asama_varsayilan_ekle, methods=['POST'])
        self.app.add_url_rule('/asama_sil/<int:id>', 'asama_sil', self.asama_sil)
        self.app.add_url_rule('/profil_guncelle', 'profil_guncelle', self.profil_guncelle, methods=['POST'])

        # --- DİNAMİK VERİ (API) ROTALARI ---
        # İl/İlçe seçimi için gerekli olan rotalar
        self.app.add_url_rule('/api/iller', 'get_iller', self.get_iller)
        self.app.add_url_rule('/api/ilceler/<il_adi>', 'get_ilceler', self.get_ilceler)

    # --- YARDIMCI METODLAR ---
    def tc_no_dogrula(self, tc):
        """T.C. Kimlik numarasının algoritmasını kontrol eder."""
        if not tc or len(tc) != 11 or not tc.isdigit() or tc[0] == '0':
            return False
        digits = [int(d) for d in tc]
        tekler = sum(digits[0:9:2])
        ciftler = sum(digits[1:8:2])
        if (tekler * 7 - ciftler) % 10 != digits[9]:
            return False
        if sum(digits[:10]) % 10 != digits[10]:
            return False
        return True


    # --- KAYIT VE GİRİŞ İŞLEMLERİ ---
    def register(self):
        if request.method == 'POST':
            ad_soyad = request.form.get('ad_soyad')
            tc_no = request.form.get('tc_no')
            sifre = request.form['sifre']
            gecerli, mesaj = self.sifre_kontrol(sifre) # Özel metot çağrılıyor
            
            if not gecerli:
                flash("Kayıt Başarısız: Şifreler eşleşmiyor.", "danger")
                return redirect(url_for('register'))

            if not self.tc_no_dogrula(tc_no):
                flash("Kayıt Başarısız: Geçersiz T.C. Kimlik No.", "danger")
                return redirect(url_for('register'))

            hashed_sifre = generate_password_hash(sifre)
            conn = self.get_db()
            try:
                conn.execute("INSERT INTO Kullanicilar (ad_soyad, kullanici_adi, sifre, rol) VALUES (?, ?, ?, 'mimar')", 
                             (ad_soyad, tc_no, hashed_sifre))
                conn.commit()
                flash("Kaydınız başarıyla oluşturuldu!", "success")
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash("Bu T.C. No zaten kayıtlı.", "danger")
            finally:
                conn.close()
        return render_template('register.html')

    def login(self):
        if request.method == 'POST':
            u = request.form.get('username')
            p = request.form.get('password')
            
            # Statik admin kontrolü
            if u == "admin" and p == "1234":
                session.update({'logged_in': True, 'user_role': 'admin', 'user_name': 'Yönetici', 'user_id': 0, 'profil_resmi': 'default.png'})
                return redirect(url_for('index'))
                
            conn = self.get_db()
            user = conn.execute("SELECT * FROM Kullanicilar WHERE kullanici_adi = ?", (u,)).fetchone()
            conn.close()
            
            if user and check_password_hash(user['sifre'], p):
                session.update({
                    'logged_in': True, 'user_role': user['rol'], 'user_id': user['id'], 
                    'user_name': user['ad_soyad'], 'profil_resmi': user['profil_resmi'] or 'default.png'
                })
                return redirect(url_for('index'))
                
            flash("Kullanıcı adı veya şifre hatalı.", "danger")
        return render_template('login.html')

    def logout(self):
        session.clear() # Oturum verilerini temizler
        flash("Başarıyla çıkış yapıldı.", "success") # Kullanıcıya bilgi verir
        return redirect(url_for('login')) # Kullanıcıyı giriş sayfasına yönlendirir
    
    # --- MÜŞTERİ YÖNETİMİ METODLARI ---

    def musteriler(self):
        """Sistemdeki müşterileri listeler. Arama filtresi destekler."""
        if not session.get('logged_in'): 
            return redirect(url_for('login'))
        
        # URL'den gelen arama parametresini al (varsayılan boş)
        search_query = request.args.get('search', '').strip()
        user_id = session.get('user_id')
        user_role = session.get('user_role')
        
        conn = self.get_db()
        
        # Admin her müşteriyi, mimar ise sadece kendi eklediği müşteriyi görür
        if user_role == 'admin':
            base_query = "SELECT * FROM Musteriler WHERE (ad_soyad LIKE ? OR tc_no LIKE ?)"
            params = ('%' + search_query + '%', '%' + search_query + '%')
        else:
            base_query = "SELECT * FROM Musteriler WHERE ekleyen_id = ? AND (ad_soyad LIKE ? OR tc_no LIKE ?)"
            params = (user_id, '%' + search_query + '%', '%' + search_query + '%')
        
        musteriler = conn.execute(base_query + " ORDER BY ad_soyad", params).fetchall()
        conn.close()
        
        return render_template('musteriler.html', musteriler=musteriler, search_query=search_query)

    def musteri_ekle(self):
        """Yeni bir müşteri kaydı oluşturur."""
        if not session.get('logged_in'): 
            return redirect(url_for('login'))
        
        # Formdan gelen verileri al
        ad_soyad = request.form.get('ad_soyad', '').strip()
        tc_no = request.form.get('tc_no', '').strip()
        telefon = request.form.get('telefon', '').strip()
        eposta = request.form.get('eposta', '').strip()
        ekleyen_id = session.get('user_id')
        
        # Temel veri doğrulamaları
        if not ad_soyad:
            flash("Ad Soyad alanı boş bırakılamaz.", "danger")
            return redirect(url_for('musteriler'))
        
        if tc_no and not self.tc_no_dogrula(tc_no):
            flash("Geçersiz T.C. Kimlik Numarası.", "danger")
            return redirect(url_for('musteriler'))

        conn = self.get_db()
        try:
            conn.execute("""
                INSERT INTO Musteriler (ad_soyad, tc_no, telefon, eposta, ekleyen_id) 
                VALUES (?, ?, ?, ?, ?)
            """, (ad_soyad, tc_no, telefon, eposta, ekleyen_id))
            conn.commit()
            flash(f"{ad_soyad} başarıyla kaydedildi.", "success")
        except Exception as e:
            flash(f"Veritabanı hatası: {str(e)}", "danger")
        finally:
            conn.close()
        
        return redirect(url_for('musteriler'))

    def musteri_duzenle(self, id):
        """Mevcut müşterinin bilgilerini günceller."""
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        
        conn = self.get_db()
        
        if request.method == 'POST':
            ad_soyad = request.form.get('ad_soyad')
            tc_no = request.form.get('tc_no')
            telefon = request.form.get('telefon')
            eposta = request.form.get('eposta')

            # T.C. No girilmişse doğrula
            if tc_no and not self.tc_no_dogrula(tc_no):
                flash("Hata: Geçersiz T.C. Kimlik Numarası!", "danger")
                return redirect(url_for('musteri_duzenle', id=id))

            conn.execute("""
                UPDATE Musteriler 
                SET ad_soyad=?, tc_no=?, telefon=?, eposta=?
                WHERE id=?
            """, (ad_soyad, tc_no, telefon, eposta, id))
            conn.commit()
            conn.close()
            
            flash(f"{ad_soyad} bilgileri güncellendi.", "success")
            return redirect(url_for('musteriler'))

        # Sayfa ilk açıldığında mevcut verileri çek
        musteri = conn.execute("SELECT * FROM Musteriler WHERE id = ?", (id,)).fetchone()
        conn.close()
        
        return render_template('musteri_duzenle.html', musteri=musteri)

    def musteri_sil(self, id):
        """Seçilen müşteriyi sistemden siler."""
        if not session.get('logged_in'): 
            return redirect(url_for('login'))
        
        conn = self.get_db()
        try:
            conn.execute("DELETE FROM Musteriler WHERE id = ?", (id,))
            conn.commit()
            flash("Müşteri başarıyla silindi.", "success")
        except Exception as e:
            flash(f"Silme hatası: {e}", "danger")
        finally:
            conn.close()
        
        return redirect(url_for('musteriler'))
    # --- PROJE YÖNETİMİ METODLARI ---

    def projelerim(self):
        """
        Kullanıcının yetkisine göre projeleri filtreleyerek listeler.
        Arama ve şehir filtresi özelliklerini barındırır.
        """
        # Giriş kontrolü: Oturum açılmamışsa login sayfasına gönder
        if not session.get('logged_in'): 
            return redirect(url_for('login'))
        
        # URL'den (GET metoduyla) gelen filtreleme parametrelerini alıyoruz
        search_query = request.args.get('search', '').strip() # Arama kutusu içeriği
        city_filter = request.args.get('city', '').strip()    # Şehir seçimi
        
        conn = self.get_db() # Veritabanı bağlantısını aç
        user_id = session.get('user_id')     # Oturumdaki kullanıcı ID'si
        user_role = session.get('user_role') # Oturumdaki kullanıcı Rolü (admin/mimar)
        
        # Temel SQL sorgusu: Proje ve Müşteri tablolarını JOIN ile birleştiriyoruz [cite: 11]
        # Bu sayede proje tablosundaki 'musteri_id' üzerinden müşteri ismine ulaşıyoruz.
        query = """
            SELECT p.*, m.ad_soyad FROM Projeler p 
            LEFT JOIN Musteriler m ON p.musteri_id = m.id 
            WHERE 1=1
        """
        params = []

        # YETKİ KONTROLÜ: 
        # Giriş yapan kullanıcı admin değilse, sadece kendi 'kullanici_id'sine ait projeleri görür. [cite: 11]
        if user_role != 'admin':
            query += " AND p.kullanici_id = ?"
            params.append(user_id)

        # ARAMA FİLTRESİ: Proje adı veya Müşteri adında arama yapar [cite: 11]
        if search_query:
            query += " AND (p.proje_adi LIKE ? OR m.ad_soyad LIKE ?)"
            params.append(f'%{search_query}%')
            params.append(f'%{search_query}%')

        # ŞEHİR FİLTRESİ: Belirli bir ile göre süzme yapar [cite: 11]
        if city_filter:
            query += " AND p.il = ?"
            params.append(city_filter)

        # Sorguyu çalıştır ve sonuçları al
        projeler_raw = conn.execute(query, params).fetchall()

        devam_edenler = [] # %100 olmayan projeler için liste
        tamamlananlar = [] # %100 olan projeler için liste
        
        # Arayüzdeki filtre menüsü için 'iller.json' dosyasından şehir listesini okuyoruz [cite: 14]
        try:
            with open('iller.json', 'r', encoding='utf-8') as f:
                # JSON dosyasındaki anahtarları (il isimlerini) alfabetik sıralayarak al
                iller_listesi = sorted(list(json.load(f).keys()))
        except:
            iller_listesi = []

        # Her bir projenin ilerleme yüzdesini hesaplayarak listelere ayırıyoruz
        for p in projeler_raw:
            # Toplam aşama sayısını bul [cite: 11]
            t = conn.execute("SELECT COUNT(*) FROM Asamalar WHERE proje_id = ?", (p['id'],)).fetchone()[0]
            # Tamamlanan aşama sayısını bul [cite: 11]
            c = conn.execute("SELECT COUNT(*) FROM Asamalar WHERE proje_id = ? AND tamamlandi = 1", (p['id'],)).fetchone()[0]
            
            # Yüzdeyi hesapla (0'a bölünme hatasını engellemek için kontrol ekledik)
            yuzde = int((c / t * 100) if t > 0 else 0)
            
            # SQLite 'Row' objesini Python 'dict' objesine çeviriyoruz (Üzerinde değişiklik yapabilmek için)
            p_dict = dict(p)
            p_dict['yuzde'] = yuzde
            
            # Proje durumuna göre ilgili listeye ekle
            if yuzde == 100:
                tamamlananlar.append(p_dict)
            else:
                devam_edenler.append(p_dict)
                
        conn.close() # Veritabanı bağlantısını kapat
        # Verileri 'projelerim.html' şablonuna gönderiyoruz
        return render_template('projelerim.html', 
                            devam_edenler=devam_edenler, 
                            tamamlananlar=tamamlananlar, 
                            iller_listesi=iller_listesi,
                            search_query=search_query,
                            city_filter=city_filter)

    def proje_ekle(self):
        """
        Yeni bir mimari proje kaydı oluşturur ve 
        proje için varsayılan şablon aşamalarını otomatik atar. [cite: 11]
        """
        if not session.get('logged_in'): 
            return redirect(url_for('login'))
        
        conn = self.get_db()
        user_id = session.get('user_id')
        user_role = session.get('user_role')

        # Eğer form gönderildiyse (POST metodu)
        if request.method == 'POST':
            # Form verilerini topluyoruz
            musteri_id = request.form.get('musteri_id')
            # Projeyi yöneten kişi admin ise formdan seçilen kişiyi, mimar ise kendi ID'sini kullanır
            kullanici_id = request.form.get('kullanici_id') if user_role == 'admin' else user_id
            
            proje_adi = request.form.get('proje_adi')
            proje_tipi = request.form.get('proje_tipi') 
            toplam_bedel = request.form.get('toplam_bedel')
            
            # Lokasyon ve Tapu Bilgileri
            il = request.form.get('il')
            ilce = request.form.get('ilce')
            mahalle = request.form.get('mahalle')
            ada = request.form.get('ada')
            parsel = request.form.get('parsel')
            teslim_tarihi = request.form.get('teslim_tarihi')
            
            try:
                cur = conn.cursor()
                # 1. Projeyi ana tabloya kaydet [cite: 11]
                cur.execute("""
                    INSERT INTO Projeler (
                        musteri_id, kullanici_id, proje_adi, proje_tipi, 
                        il, ilce, mahalle, ada, parsel, teslim_tarihi, toplam_bedel
                    ) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    musteri_id, kullanici_id, proje_adi, proje_tipi, 
                    il, ilce, mahalle, ada, parsel, teslim_tarihi, toplam_bedel
                ))
                
                # Yeni eklenen projenin ID'sini (kimliğini) alıyoruz
                proje_id = cur.lastrowid 
                
                # 2. VARSAYILAN AŞAMALARI ATAMA: 
                # Her yeni proje için 'VarsayilanAsamalar' tablosundaki şablonu kopyalıyoruz [cite: 11]
                varsayilanlar = conn.execute("SELECT asama_adi FROM VarsayilanAsamalar").fetchall()
                if varsayilanlar:
                    for v in varsayilanlar:
                        conn.execute("INSERT INTO Asamalar (proje_id, asama_adi, tamamlandi) VALUES (?, ?, 0)", 
                                    (proje_id, v['asama_adi']))
                else:
                    # Şablon yoksa güvenlik için temel bir başlangıç aşaması ekle
                    conn.execute("INSERT INTO Asamalar (proje_id, asama_adi, tamamlandi) VALUES (?, 'Proje Başlatıldı', 0)", (proje_id,))
                
                conn.commit() # Değişiklikleri kaydet
                flash("Proje başarıyla oluşturuldu ve süreçler başlatıldı.", "success")
                return redirect(url_for('index'))
                
            except Exception as e:
                conn.rollback() # Hata durumunda işlemi geri al
                flash(f"Proje ekleme hatası: {str(e)}", "danger")

        # Sayfa yüklenirken (GET metodu) formdaki seçim kutularını dolduruyoruz
        if user_role == 'admin':
            # Admin tüm müşterileri ve mimarları görebilir [cite: 11]
            musteriler = conn.execute("SELECT * FROM Musteriler ORDER BY ad_soyad").fetchall()
            kullanicilar = conn.execute("SELECT * FROM Kullanicilar ORDER BY ad_soyad").fetchall()
        else:
            # Mimar sadece kendi eklediği müşterileri seçebilir [cite: 11]
            musteriler = conn.execute("SELECT * FROM Musteriler WHERE ekleyen_id = ? ORDER BY ad_soyad", (user_id,)).fetchall()
            kullanicilar = []

        # İller listesini formdaki şehir seçimi için tekrar oku
        try:
            with open('iller.json', 'r', encoding='utf-8') as f:
                iller_listesi = sorted(list(json.load(f).keys()))
        except:
            iller_listesi = []
            
        conn.close() 
        return render_template('proje_ekle.html', musteriler=musteriler, kullanicilar=kullanicilar, iller_listesi=iller_listesi)
    
    # --- EKSİK PROJE VE API METODLARI ---
    
    def proje_duzenle(self, id):
        """Mevcut bir projenin bilgilerini günceller."""
        if not session.get('logged_in'):
            return redirect(url_for('login'))

        conn = self.get_db()
        conn.row_factory = sqlite3.Row

        if request.method == 'POST':
            proje_adi = request.form.get('proje_adi')
            proje_tipi = request.form.get('proje_tipi')
            toplam_bedel = request.form.get('toplam_bedel')
            il = request.form.get('il')
            ilce = request.form.get('ilce')
            ada = request.form.get('ada')
            parsel = request.form.get('parsel')

            try:
                conn.execute("""
                    UPDATE Projeler
                    SET proje_adi=?, proje_tipi=?, toplam_bedel=?, il=?, ilce=?, ada=?, parsel=?
                    WHERE id=?
                """, (proje_adi, proje_tipi, toplam_bedel, il, ilce, ada, parsel, id))
                conn.commit()
                flash("Proje bilgileri başarıyla güncellendi.", "success")
            except Exception as e:
                conn.rollback()
                flash(f"Güncelleme hatası: {str(e)}", "danger")
            finally:
                conn.close()

            return redirect(url_for('proje_detay', id=id))

        # GET isteği: Formu doldurmak için mevcut verileri çek
        proje = conn.execute("SELECT * FROM Projeler WHERE id = ?", (id,)).fetchone()
        conn.close()

        if not proje:
            flash("Proje bulunamadı.", "danger")
            return redirect(url_for('projelerim'))

        return render_template('proje_duzenle.html', proje=proje)

    def get_iller(self):
        """API: İller json dosyasını döndürür."""
        try:
            with open('iller.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            return json.dumps(data)
        except:
            return json.dumps({})

    def get_ilceler(self, il_adi):
        """API: Seçilen ile ait ilçeleri JSON formatında döndürür."""
        try:
            with open('iller.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Seçilen il JSON dosyasında varsa ilçelerini, yoksa boş liste döndür
            return json.dumps(data.get(il_adi, []))
        except Exception as e:
            return json.dumps([])
    
    def proje_detay(self, id):
        """
        Belirli bir projenin tüm detaylarını (müşteri bilgileri, aşamalar, 
        ödemeler ve dosyalar) tek bir ekranda toplar.
        """
        # Güvenlik kontrolü: Kullanıcı giriş yapmamışsa erişimi engelle
        if not session.get('logged_in'): 
            return redirect(url_for('login'))
        
        conn = self.get_db()
        # Veritabanından gelen verileri sözlük (dict) yapısında kullanabilmek için row_factory ayarı
        conn.row_factory = sqlite3.Row
        
        # 1. ADIM: Proje ve Müşteri bilgilerini birleştirerek çek (JOIN işlemi) [cite: 13, 15]
        # Müşterinin telefon ve e-posta gibi iletişim bilgilerini de buradan alıyoruz.
        proje = conn.execute("""
            SELECT p.*, m.ad_soyad, m.telefon, m.eposta 
            FROM Projeler p 
            JOIN Musteriler m ON p.musteri_id = m.id 
            WHERE p.id = ?
        """, (id,)).fetchone()

        # Eğer veritabanında böyle bir ID'ye sahip proje yoksa ana sayfaya yönlendir
        if not proje:
            conn.close()
            flash("Aradığınız proje sistemde bulunamadı.", "danger")
            return redirect(url_for('index'))

        # 2. ADIM: Projeye ait tüm süreç aşamalarını çek [cite: 13, 14]
        tum_asamalar = conn.execute("SELECT * FROM Asamalar WHERE proje_id = ? ORDER BY id ASC", (id,)).fetchall()
        
        # 3. ADIM: Akıllı Metin Analizi ile Aşamaları Gruplama [cite: 13]
        # Bu mantık, veritabanında hiyerarşik bir bağ olmasa bile isimdeki sayıya bakarak
        # (Örn: "1- Temel") ana başlık ve alt başlık ayrımı yapar.
        import re
        asamalar = []
        current_parent = None

        for a in tum_asamalar:
            asama_dict = dict(a)
            asama_dict['alt_asamalar'] = [] # Alt aşamalar için boş bir liste tanımla
            
            # Düzenli İfade (Regex) Kontrolü: Metin sayı ile mi başlıyor? (Örn: 1-, 2. gibi)
            if re.match(r'^\d+[-). ]', asama_dict['asama_adi'].strip()):
                asamalar.append(asama_dict) # Ana başlık listesine ekle
                current_parent = asama_dict  # Yeni ana başlığı hafızaya al
            else:
                # Sayı ile başlamıyorsa, en son bulunan ana başlığın altına ekle
                if current_parent is not None:
                    current_parent['alt_asamalar'].append(asama_dict)
                else:
                    # Başıboş kalmaması için mecburen ana başlık olarak kabul et
                    asamalar.append(asama_dict)
                    current_parent = asama_dict

        # 4. ADIM: Finansal Durum Hesaplamaları [cite: 12, 16]
        # Proje için o ana kadar yapılmış toplam ödemeyi topla
        odeme_sorgu = conn.execute("SELECT SUM(miktar) as toplam FROM Odemeler WHERE proje_id = ?", (id,)).fetchone()
        toplam_odenen = odeme_sorgu['toplam'] if odeme_sorgu['toplam'] is not None else 0
        
        # Kalan borcu hesapla
        proje_bedeli = proje['toplam_bedel'] if proje['toplam_bedel'] is not None else 0
        kalan_bakiye = proje_bedeli - toplam_odenen
        # Ödemenin tamamen bitip bitmediğini kontrol et
        odeme_tamamlandi = 1 if (proje_bedeli > 0 and kalan_bakiye <= 0) else 0

        # 5. ADIM: Dosyaları ve Ödeme Geçmişini Çek [cite: 12, 13]
        dosyalar = conn.execute("SELECT * FROM ProjeDosyalari WHERE proje_id = ? ORDER BY yukleme_tarihi DESC", (id,)).fetchall()
        odemeler = conn.execute("SELECT * FROM Odemeler WHERE proje_id = ? ORDER BY odeme_tarihi DESC", (id,)).fetchall()

        conn.close()
        # Tüm hesaplanan ve çekilen verileri arayüze (detay.html) gönder
        return render_template('detay.html', 
                            proje=proje, 
                            asamalar=asamalar, 
                            toplam_odenen=toplam_odenen, 
                            kalan_bakiye=kalan_bakiye, 
                            odeme_tamamlandi=odeme_tamamlandi,
                            dosyalar=dosyalar, 
                            odemeler=odemeler)

    def proje_sil(self, id):
        """Seçilen projeyi ve ona bağlı tüm aşama/dosya/ödeme kayıtlarını siler."""
        if not session.get('logged_in'):
            return redirect(url_for('login'))

        conn = self.get_db()
        try:
            # Önce projeye bağlı alt tabloları temizleyelim (Veritabanı kuralları gereği)
            conn.execute("DELETE FROM Asamalar WHERE proje_id = ?", (id,))
            conn.execute("DELETE FROM Odemeler WHERE proje_id = ?", (id,))
            conn.execute("DELETE FROM ProjeDosyalari WHERE proje_id = ?", (id,))
            
            # Sonra ana projeyi silelim
            conn.execute("DELETE FROM Projeler WHERE id = ?", (id,))
            conn.commit()
            flash("Proje ve bağlı tüm veriler başarıyla silindi.", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Proje silinirken hata oluştu: {str(e)}", "danger")
        finally:
            conn.close()

        return redirect(url_for('projelerim'))

    def asama_guncelle(self):
        """
        Proje aşamalarının (checkbox) tamamlanma durumunu günceller.
        Ayrıca bir aşamanın önceki aşamalar bitmeden seçilmesini engelleyen bir kontrol içerir.
        """
        if not session.get('logged_in'): 
            return redirect(url_for('login'))
        
        proje_id = request.form.get('proje_id')
        conn = self.get_db()
        
        # Formdan gelen 'asama_ID' şeklindeki anahtarları ayıklayıp liste yapıyoruz
        secili_id_listesi = []
        for key in request.form.keys():
            if key.startswith('asama_'):
                secili_id_listesi.append(int(key.split('_')[1]))
        
        try:
            # İş mantığı gereği, aşamalar sırayla gitmelidir.
            tum_asamalar = conn.execute("SELECT id, asama_adi FROM Asamalar WHERE proje_id = ? ORDER BY id ASC", (proje_id,)).fetchall()
            
            # --- SIRALAMA KONTROL MEKANİZMASI ---
            for i, asama in enumerate(tum_asamalar):
                # Eğer bir aşama işaretlenmişse, listede ondan önce gelenlerin de işaretli olması zorunludur.
                if asama['id'] in secili_id_listesi:
                    for j in range(i):
                        onceki_asama = tum_asamalar[j]
                        if onceki_asama['id'] not in secili_id_listesi:
                            flash(f"Hata: '{asama['asama_adi']}' için önce '{onceki_asama['asama_adi']}' tamamlanmalı!", "danger")
                            return redirect(url_for('proje_detay', id=proje_id))
            
            # Tüm kontroller geçildiyse veritabanını güncelle
            conn.execute("UPDATE Asamalar SET tamamlandi = 0 WHERE proje_id = ?", (proje_id,))
            for aid in secili_id_listesi:
                conn.execute("UPDATE Asamalar SET tamamlandi = 1 WHERE id = ?", (aid,))
            
            conn.commit()
            flash("Proje ilerleme durumu başarıyla kaydedildi.", "success")
        except Exception as e:
            conn.rollback() # Hata oluşursa işlemleri geri al
            flash(f"Güncelleme sırasında bir hata oluştu: {str(e)}", "danger")
        finally:
            conn.close()
            
        return redirect(url_for('proje_detay', id=proje_id))

   
    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'dwg', 'png', 'jpg', 'jpeg', 'gif', 'docx', 'xlsx'}

    
    def proje_dosya_yukle(self, proje_id):
        if 'dosya' in request.files:
            file = request.files['dosya']
            if file and file.filename != '' and self.allowed_file(file.filename): # Boş dosya kontrolü eklendi
                uzanti = file.filename.rsplit('.', 1)[1].lower()
                yeni_ad = f"proje_{proje_id}_{uuid.uuid4().hex[:8]}.{uzanti}"
                file.save(os.path.join(UPLOAD_PROJE, yeni_ad))
                
                tip = 'resim' if uzanti in ['jpg', 'jpeg', 'png', 'gif'] else 'dokuman'
                
                conn = self.get_db()
                conn.execute("INSERT INTO ProjeDosyalari (proje_id, dosya_adi, dosya_yolu, dosya_tipi) VALUES (?, ?, ?, ?)",
                            (proje_id, file.filename, yeni_ad, tip))
                conn.commit()
                conn.close()
                flash("Dosya başarıyla sisteme yüklendi.", "success")
            else:
                flash("Geçersiz dosya formatı veya dosya seçilmedi.", "danger")
        return redirect(url_for('proje_detay', id=proje_id))
    
    def get_proje(self, id):
        conn = self.get_db()
        # JOIN yerine LEFT JOIN kullanıyoruz
        proje = conn.execute("""
            SELECT p.*, m.ad_soyad, m.telefon, m.eposta 
            FROM Projeler p 
            LEFT JOIN Musteriler m ON p.musteri_id = m.id 
            WHERE p.id = ?
        """, (id,)).fetchone()
        conn.close()
        return proje

    def proje_indir(self, id):
        if not session.get('logged_in'):
            return redirect(url_for('login'))

        proje = self.get_proje(id)
        if not proje:
            flash("Proje bulunamadı.", "danger")
            return redirect(url_for('projelerim'))

        conn = self.get_db()
        # HATA DÜZELTME: Tablo adı 'Asamalar' olarak güncellendi
        asamalar = conn.execute("SELECT * FROM Asamalar WHERE proje_id = ?", (id,)).fetchall()
        conn.close()

        output = io.StringIO()
        # Türkçe karakterlerin Excel'de düzgün görünmesi için BOM ekliyoruz
        output.write('\ufeff') 
        writer = csv.writer(output, delimiter=';') # Excel için noktalı virgül daha uygundur
        
        writer.writerow(['Aşama Adı', 'Durum']) 

        for a in asamalar:
            durum = 'Tamamlandı' if a['tamamlandi'] == 1 else 'Bekliyor'
            writer.writerow([a['asama_adi'], durum]) 

        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={proje['proje_adi']}_rapor.csv"}
        )
    # --- ADMIN VE SİSTEM YÖNETİMİ METODLARI ---

    def kullanici_sayfasi(self):
        """
        Sadece admin yetkisine sahip kullanıcıların erişebildiği, 
        sistemdeki tüm mimarları ve istatistiklerini listeleyen sayfadır.
        """
        # YETKİ KONTROLÜ: Admin değilse ana sayfaya geri gönder (Güvenlik Katmanı)
        if session.get('user_role') != 'admin': 
            return redirect(url_for('index'))
        
        # Arama kutusundan gelen veriyi al
        search_query = request.args.get('search', '').strip()
        conn = self.get_db()
        
        # SQL Alt Sorgu (Subquery) Kullanımı: 
        # Her kullanıcının toplam proje ve müşteri sayısını o anda hesaplıyoruz.
        query = """
            SELECT k.*, 
            (SELECT COUNT(*) FROM Projeler WHERE kullanici_id = k.id) as p_sayisi,
            (SELECT COUNT(*) FROM Musteriler WHERE ekleyen_id = k.id) as m_sayisi
            FROM Kullanicilar k
            WHERE k.ad_soyad LIKE ? OR k.kullanici_adi LIKE ?
            ORDER BY k.id DESC
        """
        kullanicilar = conn.execute(query, ('%' + search_query + '%', '%' + search_query + '%')).fetchall()
        conn.close()
        
        return render_template('kullanicilar.html', kullanicilar=kullanicilar, search_query=search_query)

    def kullanici_ekle(self):
        """
        Yeni bir mimar kullanıcısını sisteme dahil eder. 
        T.C. No doğrulaması ve şifre hashleme işlemlerini yapar.
        """
        if session.get('user_role') != 'admin': 
            return redirect(url_for('index'))
        
        ad_soyad = request.form.get('ad_soyad').strip()
        tc_no = request.form.get('kullanici_adi').strip() # Kullanıcı adı olarak T.C. No kullanılır
        sifre = request.form.get('sifre').strip()
        rol = request.form.get('rol')

        # 1. DOĞRULAMA: T.C. Kimlik No matematiksel olarak geçerli mi? 
        if not self.tc_no_dogrula(tc_no):
            flash("Hata: Geçersiz T.C. Kimlik Numarası!", "danger")
            return redirect(url_for('kullanici_sayfasi'))

        # 2. GÜVENLİK: Şifreyi açık metin olarak değil, hash'lenmiş (şifrelenmiş) saklıyoruz.
        hashed_sifre = generate_password_hash(sifre)

        conn = self.get_db()
        try:
            conn.execute("""
                INSERT INTO Kullanicilar (ad_soyad, kullanici_adi, sifre, rol, tema_tercihi) 
                VALUES (?, ?, ?, ?, 'light')
            """, (ad_soyad, tc_no, hashed_sifre, rol))
            
            conn.commit()
            flash(f"{ad_soyad} başarıyla eklendi.", "success")
        except sqlite3.IntegrityError:
            # T.C. No kolonu UNIQUE (Benzersiz) olduğu için aynı no girilirse bu hata düşer.
            flash("Hata: Bu T.C. No zaten sistemde kayıtlı!", "danger")
        finally:
            conn.close()
            
        return redirect(url_for('kullanici_sayfasi'))

    # --- EKSİK YÖNETİM VE AYAR METODLARI ---

    def kullanici_sil(self, id):
        """Sistemden kullanıcı siler (Sadece Admin)."""
        if session.get('user_role') != 'admin': 
            return redirect(url_for('login'))
        
        conn = self.get_db()
        try:
            conn.execute("DELETE FROM Kullanicilar WHERE id = ?", (id,))
            conn.commit()
            flash("Kullanıcı başarıyla sistemden silindi.", "success")
        except Exception as e:
            flash("Hata: Kullanıcı silinemedi.", "danger")
        finally:
            conn.close()
            return redirect(url_for('kullanicilar'))

    def asama_varsayilan_ekle(self):
        """Ayarlar sayfasından sisteme yeni varsayılan aşama şablonu ekler."""
        if session.get('user_role') != 'admin': 
            return redirect(url_for('ayarlar'))
            
        asama_adi = request.form.get('asama_adi')
        ust_id = request.form.get('ust_id') or None
        
        conn = self.get_db()
        conn.execute("INSERT INTO VarsayilanAsamalar (asama_adi, ust_id) VALUES (?, ?)", (asama_adi, ust_id))
        conn.commit()
        conn.close()
        
        flash("Yeni aşama şablona başarıyla eklendi.", "success")
        return redirect(url_for('ayarlar'))

    def asama_sil(self, id):
        """Ayarlar sayfasından varsayılan şablon aşamasını siler."""
        if session.get('user_role') != 'admin': 
            return redirect(url_for('ayarlar'))
            
        conn = self.get_db()
        conn.execute("DELETE FROM VarsayilanAsamalar WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        
        flash("Aşama şablondan silindi.", "success")
        return redirect(url_for('ayarlar'))

    # --- FİNANSAL İŞLEMLER ---

    def odeme_ekle(self, proje_id):
        """
        Bir projeye ait ödeme girişini kaydeder. 
        Kalan bakiye kontrolü yaparak fazla ödeme alınmasını engeller.
        """
        if not session.get('logged_in'): 
            return redirect(url_for('login'))
        
        miktar_str = request.form.get('miktar')
        aciklama = request.form.get('aciklama')
        
        try:
            yeni_miktar = float(miktar_str)
        except ValueError:
            flash("Hata: Geçersiz miktar formatı!", "danger")
            return redirect(url_for('proje_detay', id=proje_id))

        conn = self.get_db()
        try:
            # MANTIKSAL KONTROL: Toplam bedel ve o ana kadar ödenen miktarı karşılaştır
            proje = conn.execute("SELECT toplam_bedel FROM Projeler WHERE id = ?", (proje_id,)).fetchone()
            odenen_toplam = conn.execute("SELECT SUM(miktar) FROM Odemeler WHERE proje_id = ?", (proje_id,)).fetchone()[0] or 0
            
            kalan_bakiye = proje['toplam_bedel'] - odenen_toplam

            # Eğer girilen miktar kalan borçtan fazlaysa işlemi reddet
            if yeni_miktar > kalan_bakiye:
                flash(f"Hata: Fazla ödeme girilemez! Kalan bakiye: {kalan_bakiye:,.2f} TL", "danger")
            else:
                conn.execute("INSERT INTO Odemeler (proje_id, miktar, acıklama) VALUES (?, ?, ?)",
                            (proje_id, yeni_miktar, aciklama))
                conn.commit()
                flash("Ödeme kaydı başarıyla eklendi.", "success")
        finally:
            conn.close()
        
        return redirect(url_for('proje_detay', id=proje_id))

    # --- VERİ ANALİZİ VE GÖRSELLEŞTİRME (PANDAS & MATPLOTLIB) ---

    def proje_analiz_grafigi_olustur(self, user_id=None, role='admin'):
        """
        Veritabanındaki verileri Pandas ile analiz eder ve 
        Matplotlib kullanarak bir sütun grafiği (Bar Chart) üretir.
        """
        conn = self.get_db()
        
        # Rol kontrolü: Admin genel tabloyu, Mimar sadece kendi verilerini görür. 
        if role == 'admin':
            query = "SELECT proje_tipi FROM Projeler"
            df = pd.read_sql_query(query, conn)
        else:
            query = "SELECT proje_tipi FROM Projeler WHERE kullanici_id = ?"
            df = pd.read_sql_query(query, conn, params=(user_id,))
        
        conn.close()

        # Eğer veri yoksa grafik oluşturma
        if df.empty: return False

        # Veri setini analiz et: Proje tiplerine göre adetleri say
        tip_sayilari = df['proje_tipi'].value_counts()
        
        plt.figure(figsize=(10, 6)) # Grafik boyutu
        renk = '#3498db' if role == 'admin' else '#2ecc71'
        
        # Grafik çizimi
        tip_sayilari.plot(kind='bar', color=renk, edgecolor='#2c3e50')
        
        # Akademik etiketleme ve başlıklar
        baslik = 'Sistem Geneli Proje Dağılımı' if role == 'admin' else 'Kişisel Portföy Analizi'
        plt.title(baslik, fontsize=14, fontweight='bold') 
        plt.xlabel('Proje Kategorisi', fontsize=12)
        plt.ylabel('Proje Sayısı', fontsize=12)
        plt.xticks(rotation=30, ha='right') # Kategori isimlerini yan yatır
        plt.tight_layout()

        # Grafiği statik dosyalar altına kaydet (Her kullanıcı için benzersiz isim)
        filename = f"analiz_{user_id}.png"
        grafik_yolu = os.path.join(BASE_DIR, 'static', 'uploads', filename)
        plt.savefig(grafik_yolu)
        plt.close() # Belleği temizle
        return filename
    # --- ANA SAYFA (DASHBOARD) MANTIĞI ---

    # --- ANA SAYFA (DASHBOARD) MANTIĞI ---

    def index(self):
        """
        Kullanıcının karşısına çıkan ilk ekran (Dashboard).
        İstatistik özetlerini hesaplar ve teslim tarihi yaklaşan projeleri listeler.
        """
        if not session.get('logged_in'): 
            return redirect(url_for('login'))
        
        conn = self.get_db()
        user_id = session.get('user_id')
        user_role = session.get('user_role')
        
        grafik_dosyasi = self.proje_analiz_grafigi_olustur(user_id, user_role)
        
        try:
            # 1. TEMEL İSTATİSTİKLER VE FİNANSAL HESAPLAMALAR
            if user_role == 'admin':
                projeler_raw_data = conn.execute("""
                    SELECT p.*, m.ad_soyad FROM Projeler p 
                    LEFT JOIN Musteriler m ON p.musteri_id = m.id
                    ORDER BY p.teslim_tarihi ASC
                """).fetchall()
                toplam_kullanici = conn.execute("SELECT COUNT(*) FROM Kullanicilar").fetchone()[0]
                toplam_musteri = conn.execute("SELECT COUNT(*) FROM Musteriler").fetchone()[0]
                
                # Admin için ofis geneli finans
                tahsilat = conn.execute("SELECT SUM(miktar) FROM Odemeler").fetchone()[0]
                bedel = conn.execute("SELECT SUM(toplam_bedel) FROM Projeler").fetchone()[0]
            else:
                projeler_raw_data = conn.execute("""
                    SELECT p.*, m.ad_soyad FROM Projeler p 
                    LEFT JOIN Musteriler m ON p.musteri_id = m.id 
                    WHERE p.kullanici_id = ?
                    ORDER BY p.teslim_tarihi ASC
                """, (user_id,)).fetchall()
                toplam_kullanici = 0
                toplam_musteri = conn.execute("SELECT COUNT(*) FROM Musteriler WHERE ekleyen_id = ?", (user_id,)).fetchone()[0]
                
                # Mimar için sadece kendi projelerinin finansı
                tahsilat = conn.execute("""
                    SELECT SUM(o.miktar) FROM Odemeler o
                    JOIN Projeler p ON o.proje_id = p.id
                    WHERE p.kullanici_id = ?
                """, (user_id,)).fetchone()[0]
                bedel = conn.execute("SELECT SUM(toplam_bedel) FROM Projeler WHERE kullanici_id = ?", (user_id,)).fetchone()[0]

            # None (Boş) dönme ihtimaline karşı 0 atıyoruz
            toplam_tahsilat = tahsilat if tahsilat else 0
            toplam_bedel = bedel if bedel else 0
            bekleyen_odemeler = toplam_bedel - toplam_tahsilat

            # 2. PROJE YÜZDELERİ VE DURUM AYRIMI
            projeler_listesi = []
            yaklasan_projeler = []
            tamamlanan_proje_sayisi = 0
            
            for p in projeler_raw_data:
                p_dict = dict(p)
                t = conn.execute("SELECT COUNT(*) FROM Asamalar WHERE proje_id = ?", (p['id'],)).fetchone()[0]
                c = conn.execute("SELECT COUNT(*) FROM Asamalar WHERE proje_id = ? AND tamamlandi = 1", (p['id'],)).fetchone()[0]
                
                yuzde = int((c / t * 100) if t > 0 else 0)  
                p_dict['yuzde'] = yuzde
                
                if not p_dict['ad_soyad']: 
                    p_dict['ad_soyad'] = "Tanımsız Müşteri"
                
                projeler_listesi.append(p_dict)
                
                if yuzde == 100: 
                    tamamlanan_proje_sayisi += 1
                else:
                    yaklasan_projeler.append(p_dict)
                
            return render_template('index.html', 
                                yaklasan_projeler=yaklasan_projeler[:4],
                                projeler_raw=projeler_listesi, 
                                toplam_proje_sayisi=len(projeler_listesi),
                                tamamlanan_proje_sayisi=tamamlanan_proje_sayisi,
                                toplam_kullanici_sayisi=toplam_kullanici,
                                toplam_musteri_sayisi=toplam_musteri,
                                grafik_dosyasi=grafik_dosyasi,
                                toplam_tahsilat=toplam_tahsilat,         # HATA ÇÖZÜMÜ BURADA
                                bekleyen_odemeler=bekleyen_odemeler)     # HATA ÇÖZÜMÜ BURADA
        finally:
            conn.close()    

    # --- AYARLAR VE PROFİL YÖNETİMİ ---

    def ayarlar(self):
        """Kullanıcının profil bilgilerini gördüğü ve adminlerin süreçleri yönettiği sayfa."""
        if not session.get('logged_in'): 
            return redirect(url_for('login'))
        
        # URL'den hangi sekmenin (profil/süreç) açık olacağını al
        active_tab = request.args.get('tab', 'profile')
        
        conn = self.get_db()
        # Admin için sistemdeki varsayılan aşama şablonlarını getir
        varsayilan_asamalar = conn.execute("SELECT * FROM VarsayilanAsamalar").fetchall()
        # Kullanıcının tercihlerini çek (tema vb.)
        user = conn.execute("SELECT tema_tercihi, email_bildirim FROM Kullanicilar WHERE id = ?", (session.get('user_id'),)).fetchone()
        conn.close()
        
        return render_template('ayarlar.html', varsayilan_asamalar=varsayilan_asamalar, user_pref=user, active_tab=active_tab)


    def profil_resmi_guncelle(self):
        if 'foto' in request.files:
            file = request.files['foto']
            if file and file.filename != '' and self.allowed_file(file.filename):
                # Dosya adını güvenli hale getir ve uzantıyı al
                uzanti = file.filename.rsplit('.', 1)[1].lower()
                filename = f"user_{session['user_id']}_{uuid.uuid4().hex[:5]}.{uzanti}"
                
                # Klasör kontrolü (zaten __init__ içinde var ama güvenlik için)
                if not os.path.exists(UPLOAD_PROFIL):
                    os.makedirs(UPLOAD_PROFIL)
                    
                file.save(os.path.join(UPLOAD_PROFIL, filename))
                
                conn = self.get_db()
                conn.execute("UPDATE Kullanicilar SET profil_resmi = ? WHERE id = ?", (filename, session['user_id']))
                conn.commit()
                conn.close()
                
                session['profil_resmi'] = filename # Oturumu güncelle
                flash("Profil fotoğrafınız başarıyla güncellendi.", "success")
            else:
                flash("Lütfen geçerli bir görsel dosyası seçin.", "danger")
        return redirect(url_for('ayarlar'))
    
    # --- Şifre Kontrol Metodu ---
    def sifre_kontrol(self, sifre):
        # Şifre uzunluk ve karakter kuralları
        if len(sifre) < 4:
            return False, "Şifre en az 4 karakter olmalıdır!"
        if not any(char.isdigit() for char in sifre):
            return False, "Şifre en az bir rakam içermelidir!"
        if not any(char.isupper() for char in sifre):
            return False, "Şifre en az bir büyük harf içermelidir!"
        return True, ""

    # --- Profil Güncelleme Metodu ---
    def profil_guncelle(self):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        ad_soyad = request.form.get('ad_soyad')
        yeni_sifre = request.form.get('yeni_sifre')
        conn = self.get_db()
        
        try:
            if yeni_sifre: # Eğer yeni şifre girildiyse kuralları kontrol et
                gecerli, mesaj = self.sifre_kontrol(yeni_sifre)
                if not gecerli:
                    flash(mesaj, "danger")
                    return redirect(url_for('ayarlar'))
                
                # Şifre geçerliyse hem adı hem şifreyi güncelle
                conn.execute("UPDATE Kullanicilar SET ad_soyad = ?, sifre = ? WHERE id = ?", 
                             (ad_soyad, yeni_sifre, session['user_id']))
            else:
                # Şifre boşsa sadece adı güncelle
                conn.execute("UPDATE Kullanicilar SET ad_soyad = ? WHERE id = ?", 
                             (ad_soyad, session['user_id']))
            
            conn.commit()
            session['user_name'] = ad_soyad # Oturumu güncelle
            flash("Profiliniz başarıyla güncellendi.", "success")
        except Exception as e:
            flash(f"Bir hata oluştu: {str(e)}", "danger")
        finally:
            conn.close()
            
        return redirect(url_for('ayarlar'))
# --- UYGULAMAYI BAŞLATMA ---

# MimarTakipSistemi sınıfından bir nesne oluşturuyoruz (OOP Başlangıcı)
sistem = MimarTakipSistemi(app)

# Python dosyasının doğrudan çalıştırılıp çalıştırılmadığını kontrol eder
if __name__ == '__main__':
    # Debug modu açık: Hata olduğunda detaylı gösterir ve dosya değişiminde otomatik yenilenir
    app.run(debug=True)