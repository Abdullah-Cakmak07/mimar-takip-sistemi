# 🏛️ Mimar Takip - Proje Takip ve Otomasyon Sistemi

Bu proje, mimarlık ofislerinin kurumsal operasyonlarını, müşteri portföylerini, hiyerarşik proje süreçlerini, şantiye/doküman arşivlerini ve finansal hakedişlerini tek bir merkezden yönetebilmeleri için geliştirilmiş web tabanlı bir otomasyon sistemidir. 

Samsun Üniversitesi Yazılım Mühendisliği dönemi kapsamında, modern yazılım mimarilerine ve güvenlik standartlarına uygun olarak geliştirilmiştir.

## 🚀 Öne Çıkan Teknik ve Mühendislik Yaklaşımları

Projenin backend mimarisi ve iş mantığı tamamen nesne yönelimli programlama (OOP), ilişkisel veritabanı yönetimi ve veri analitiği prensipleri üzerine inşa edilmiştir:

* **Merkezi OOP Mimarisi (`app.py`):** Tüm uygulama süreçleri, Flask rotaları (`setup_routes`) ve veritabanı yönetim mekanizmaları `MimarTakipSistemi` sınıfı (Class) altında kapsüllenmiştir (Encapsulation). Kodun sürdürülebilirliği ve modülerliği üst seviyededir.
* **İlişkisel Veritabanı ve Akıllı Süreç Kopyalama (`schema.sql` & `database.py`):** `SQLite3` üzerinde Foreign Key ilişkileri kurularak bütünleşik bir veri yapısı tasarlanmıştır. Sistem, yeni bir proje başlatıldığında `VarsayilanAsamalar` şablonundaki hiyerarşik süreç adımlarını otomatik olarak ilgili projeye (`Asamalar` tablosuna) kopyalar.
* **Gelişmiş Sıralı İş Mantığı (Algoritma):** Proje aşamalarının güncellenmesinde (`asama_guncelle`) ardışık kontrol mekanizması uygulanmıştır. Bir mimar, önceki süreç adımlarını tamamlamadan bir sonraki aşamayı (Checkbox) işaretleyemez; sistem dinamik olarak hata yönetimini tetikler.
* **Akıllı Metin Analizi ve Regex:** Veritabanında katı bir hiyerarşik bağ olmasa bile, backend katmanında Düzenli İfadeler (Regex) kullanılarak aşama isimlerindeki numerik yapılara göre (Örn: "1- Aplikasyon Krokisi") ana başlık ve alt başlık ayrımı dinamik olarak web arayüzüne gruplanarak yansıtılır.
* **Finansal Doğrulama Kapısı:** Ödeme girişlerinde (`odeme_ekle`) projenin toplam bedeli ve o ana kadar yapılan tahsilatlar anlık hesaplanır. Kullanıcının kalan bakiyeden daha fazla ödeme girişi yapması mantıksal kontrol bloklarıyla engellenir.
* **Veri Analitiği ve Dinamik Grafikler (`Pandas` & `Matplotlib`):** Sistemdeki ham veriler `Pandas` veri çerçevelerine (`DataFrame`) aktarılarak analiz edilir. Giriş yapan kullanıcının rolüne göre (Admin veya Mimar), `Matplotlib` motoru arka planda dinamik birer sütun grafiği (Bar Chart) üreterek Dashboard ekranında görselleştirir. Memory sızıntılarını önlemek için çizim sonrası matplotlib bellek temizliği otomatik yapılır.
* **Yüksek Güvenlik Standartları:** * Kullanıcı şifreleri veritabanına asla açık metin (plain text) olarak yazılmaz; `werkzeug.security` kütüphanesi yardımıyla SHA256 tabanlı güvenli hash algoritmalarıyla kriptolanır.
    * Sisteme yüklenen tüm proje dosyaları ve profil resimleri, dosya adı çakışmalarını ve siber güvenlik açıklarını (Insecure File Upload) önlemek amacıyla `uuid.uuid4` ile izole edilerek ve uzantı doğrulamalarından geçirilerek sunucuya kaydedilir.
* **Teknik Rapor İhracatı (CSV Export):** Proje ilerleme durumları Excel ve kurumsal sistemlerle tam uyumlu, noktalı virgül (;) ayraçlı CSV formatında dışa aktarılabilir. Türkçe karakterlerin Excel'de bozulmaması için çıktıya UTF-8 BOM (`\ufeff`) entegre edilmiştir.

## 🤖 Geliştirme Süreci 
* Sistem mimarisi, ilişkisel veritabanı tablolarının tasarımı, veri doğrulama algoritmaları (T.C. Kimlik doğrulaması dahil), OOP sınıf kurgusu ve backend veri akış süreçleri tarafımdan kodlanmıştır.
* Kullanıcı deneyimi (UX) odaklı frontend tasarımları (Bootstrap 5, Jinja2 şablon motoru mimarisi) ve asenkron veri çekme süreçlerinde yapay zeka araçları efektif birer asistan olarak kullanılarak operasyonel süreç hızlandırılmıştır.

## 🛠️ Kullanılan Teknolojiler ve Kütüphaneler

* **Backend Framework:** Python, Flask
* **Veri Analizi & Grafik:** Pandas, Matplotlib (Agg Backend)
* **Veritabanı Katmanı:** SQLite3, SQL, Kapsamlı Foreign Key Yapıları
* **Güvenlik Protokolleri:** Werkzeug Security (Kriptografik Şifreleme), UUID, Regex Validation
* **Frontend Teknolojileri:** Bootstrap 5, Jinja2 Template Engine, FontAwesome 6, Vanilla JavaScript, HTML5 & CSS3
* **Veri Dosyaları:** JSON (Dinamik il/ilçe API veri yönetimi için), CSV (Veri Transferi)

## 📂 Proje Dizin Yapısı

* `app.py`: Uygulamanın kalbi. Merkezi OOP kurgusu, Flask rotaları, iş mantığı doğrulamaları ve veri analizi metotları.
* `database.py` & `schema.sql`: Veritabanı tablolarının sıfırdan oluşturulması ve hiyerarşik mimari süreç şablonunun sisteme enjekte edilmesi.
* `models.py`: Veritabanı satırlarını anlamlı yazılım nesnelerine dönüştüren veri modelleri (Proje, Müşteri sınıfları).
* `iller.json`: Dinamik şehir/ilçe API rotalarında kullanılan veri seti.
* `templates/`: Jinja2 mimarisiyle backend verilerini dinamik işleyen tüm arayüz bileşenleri (`index.html`, `detay.html`, `musteriler.html`, `ayarlar.html` vb.).
* `static/`: Profil resimleri, yüklenen dokümanlar ve dinamik üretilen analiz grafiklerinin tutulduğu izole depolama alanı.

