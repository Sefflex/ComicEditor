# ComicEditör - Profesyonel Çizgi Roman Dizgi ve Çeviri Aracı

**ComicEditör**, çeviri siteleri (scanlation) ve çizgi roman toplulukları için süreçleri ışık hızına çıkarmak amacıyla özel olarak geliştirdiğim tam kapsamlı, yapay zeka destekli otonom bir dizgi aracıdır. OCR (Optik Karakter Tanıma), pürüzsüz inpainting (arka plan silme) ve interaktif özel tuval özellikleriyle donatılmış bu program; Photoshop başında saatler süren manuel silme, yazma ve ortalama işlemlerini tek tıkla saniyelere indirmek için kodlanmıştır.

## 🎯 Geliştirme Amacım

Kendi çizgi roman arşiv sitemdeki (_cizgiarsiv.com_) devasa iş yükünü hafifletmek ve çevirmen arkadaşlarıma "yapay zekalı bir asistan" sunmak için bu projeye başladım. İngilizce, Japonca veya Korece serilerde çevirmeni ve editörü iki ayrı rol olmaktan çıkarıp, tek bir kişinin aynı anda hem çeviri edip hem de balonları saniyeler içinde dizebilmesi temel vizyonumdu.

---

## 📷 Görseller

<table><tr><td width="60%"><img src="https://github.com/user-attachments/assets/ea633bf5-5cc9-4713-95eb-7b62a8a6da4e" width="100%"></td><td width="40%"><img src="https://github.com/user-attachments/assets/8dd1e056-efde-4440-8399-676a987f4774" width="100%"><br><br><img src="https://github.com/user-attachments/assets/6de29e00-0809-45c6-8a60-5c61637abda4" width="100%"></td></tr></table>

---

## 🚀 Özellikler ve Araçların Kullanımı

ComicEditör, en zorlu Manga / Çizgi Roman temizlik (cleaning) işlemlerini çocuk oyuncağına çeviren güçlü araç kitleriyle gelir. İşte programda bulunan tüm butonların ve fonksiyonların detaylı çalışma rehberi:

### Üst Menü İşlevleri

- **▶️ 📥 Proje Aç & 📤 Proje Kaydet:** Çalışmanızı (çeviriler, fırça çizimleri ve konumlar) anlık olarak `.comicproj` dosyası olarak kaydedip, yarım bıraktıktan sonra tek tıkla **pikseli pikseline aynı hizalamalarla** kaldığınız yerden devam etmenizi sağlayan tam otonom **Hafıza (Save/Load) Mekanizması!** _(Geri yükleme sırasında yazıların kayması/zıplaması %100 düzeltilmiştir.)_
- **📂 Resim/CBR Yükle:** Bilgisayarınızdaki resimleri (PNG, JPG), PDF dosyalarını ve webtoon formatındaki sıkıştırılmış `CBR` / `CBZ` çizgi roman arşivlerini programa aktarır. Sayfaları deşifre edip sol panele dizer.
- **🚀 Sayfayı Tam Otonom Çıkart:** **(Efsane Özellik)** Üzerinde çalıştığınız sayfanın yapay zeka tarafından taranmasını başlatır. Sayfadaki metinleri tespit eder ve **orijinal dokuya asla zarar vermeden, siyah balon çizgilerine taşmayan** özel bir Telea maskelemesiyle pürüzsüzce siler! Metni Türkçeye çevirerek yeni boşluğun tam ortasına mükemmel formatta ekler.
- **🔄 Sayfayı Sıfırla:** Fırçayla yanlış boyamalar yaptınız, balonlar karıştı ya da sayfa perişan mı oldu? Hiç dert değil. Buna tıkladığınız an sistem size "Emin misiniz?" diye sorar; evet derseniz o sayfadaki bütün işleri tarihe gömer ve sayfaya ilk yüklendiği o tertemiz, ham halini geri yükler.
- **➕ Yazı Kutusu Ekle:** Ekrana yapay zeka harici, sizin manuel büyütebileceğiniz bir metin kutusu fırlatır. Unutulmuş balonlar veya sayfa kenarı notları için idealdir.
- **👁️ Orijinali Gör:** Çevirinizin doğruluğunu teyit etmek için bu butona basılı tuttuğunuzda; o an çalıştığınız sayfanın tüm çevirilerini, yaptığınız tüm boyama ve sansür işlemlerini **gizler** ve size sadece 1 saniyeliğine _eski İngilizce sayfayı_ gösterir. Bıraktığınızda çevirili dünyaya geri dönersiniz.
- **💾 PDF Olarak Çıkar:** Sol sekmedeki tüm çalışma sayfalarınızı, dizdiğiniz onca balonu kalite kaybı yaşamadan tek bir `Hikaye_Full.pdf` dosyasına basıp teslimata hazır hale getirir.

### Fırça ve Tuval Araçları (Orta Kısım)

> _Not: Tuvalde yaptığınız her çizim veya boyama işlemi `Ctrl + Z` (Windows) veya `Cmd + Z` (Mac) kullanılarak son 20 adıma kadar **Geri Alınabilir (Undo)**!_

- **🖌️ Fırça:** Dilediğiniz sayfa üzerinde fare imleci ile serbestçe çizim yapıp yazıları silmenizi, istenmeyen kısımlara sansür atmanızı sağlar. Sağındaki "Boyut:" kutusundan fırça inceliği ayarlanır.
- **🔲 Kapla (Hızlı Dikdörtgen):** Sitenizdeki serilerde hızlı sansürler atmak veya bir balonun içini şipşak tek renkle doldurmak için kullanılılır. Fareyi basılı tutup ekranda bir dikdörtgen / kare çizersiniz, elinizi çektiğiniz an çizdiğiniz alanın tamamı saniyesinde seçili renk ile kusursuzca dolar!
- **💧 Damlalık (Color Picker):** Ekrandaki herhangi bir pikselin (örneğin arka plandaki mavi gökyüzünün veya balonun tam yanındaki duvarın) üzerine tıkladığınızda o rengi kopyalar. Sizi fiziksel RGB kodu almaktan kurtarıp **anında Fırça moduna geçirerek** aynı arka plan tonuyla çizim yapmanıza olanak tanır.
- **Kare Renk İkonu:** O an elinizdeki fırçanın beyazla mı yoksa kopyaladığınız renkle mi işlem yapacağını görsel olarak yansıtır.

### Sağ Panel (Manuel Müdahale ve Profesyonel Kontrol)

Ekranda otomatik çevrilen herhangi bir yazı kutusuna tıkladığınızda, panzehir sağ panel devreye girer.

- **Orijinal İbare & Çeviri İçeriği:** Kutudaki orijinal yabancı metni gösterir. Alttaki kutudan da tamanlı Türkçesini görüp istediğiniz gibi değiştirebilir, silebilir veya alt satıra geçirebilirsiniz. Değişiklik _anında_ ekranda güncellenir.
- **Yazı Rengi & Dış Çizgi (Stroke) Renkleri:** Metne ve şeffaf konturuna istediğiniz rengi verebilirsiniz.
- **💾 Ön Ayar Kaydet:** Bir çeviri balonunun rengini, büyüklüğünü, yazı stilini ve **artık o an ayarladığınız Kutu Ebatarını (Genişlik/Yükseklik)** kaydedebilen bu butona bastığınızda tasarımı şablon olarak kilitler! Bundan sonraki tüm yeni kutular (%100 aynı ebat ve tasarımda) yollanır.
- **Göster (Dış Çizgi Checkbox):** Seçtiğiniz beyaz/siyah dış çizgiyi balonun etrafından kapatıp açar. Beyaz balonlarda dış konturu kapatmak manga sitelerinde çok daha estetik bir görüntü yaratır.
- **Stil, Font Boyutu, Kutu Genişliği, Kutu Yüksekliği:** Balon çok mu taştı? Yazı çok mu küçük kaldı? Hemen bu kaydırıcılardan (slider) birini çekerek santimi santimine harika ayarlamalar yapabilirsiniz.
- **⭐ Sadece Metni Çevir (Seçili Kutu):** Orijinal metni elinizle yanlışları düzelterek yazdıktan sonra bu butona basarsanız, yalnızca o cümleyi yapay zeka ile çevirip o kutunun içine hapseder.
- **🔍 Seçerek Oku & Yeni Kutu Ekle (Lasso OCR):** Bazen yapay zeka arka plandaki sfx veya bozuk çizimli yazıları okuyamaz. Bu butonu seçin ve ekranda okunmayan yerin tam üzerine fareniz ile ince bir **kare çizin.** Çizimi bıraktığınız an sistem o alanı zorla tarar, çevirir ve tam o karenin olduğu yere bembeyaz tertemiz ve çevirili yeni bir kutu ekler!

---

## ⚙️ Akıllı Ayarlar ve API Desteği

Üst barda bulunan **⚙️ Ayarlar** tuşu ile ComicEditör'ün merkez beynini kontrol edebilirsiniz:

- Eklentilerden "Gemini" altyapısını kullanarak doğrudan kendi **Gemini API Anahtarınızı** girebilirsiniz (Ücretsizdir). Bunu yazdığınız an uygulama argoları, deyimleri ve kültürel esprileri kusursuz yansıtan devasa bir çevirmene dönüşür. Eğer boş bırakırsanız sistem kendi yerleşik çevirisini (Google) kullanır.
- Okuyucularınıza hitap edecek varsayılan klasik _"Comic Neue"_ veya _"Patrick Hand (Türkçe Uyumlu)"_ yazı tipini, balonlardaki hizalamayı kalıcı olarak Seçebilirsiniz.

## 🛠 Kurulum ve Terminal Başlatıcısı

### Gereksinimler

- Python 3.10 veya üzeri
- macOS (Intel & ARM) ve **Windows Destekli** _(CBR/CBZ okumak için Winrar yüklemenize gerek yoktur, uygulamanın içerisine Windows uyumlu gelişmiş UnRAR aracı yerleştirilmiştir)._
- Sorunsuz bir yapay zeka taraması için internet bağlantısı

### Kurulum Test Süreci

1. Repoyu bilgisayarınıza indirin veya terminal aracılığıyla klonlayın:
   ```bash
   git clone https://github.com/Sefflex/ComicEditor.git
   cd ComicEditör
   ```
2. Temiz çalışma alanı (virtual environment) kurun:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Araçları sisteme tanıtın:
   ```bash
   pip install -r requirements.txt
   ```
4. Programı çalıştırın! 🚀
   ```bash
   python3 main.py
   ```

## 👨‍💻 Geliştirici & Lisans

- **Geliştirici:** [Sefflex](https://github.com/Sefflex) [Yağız Efe Ağcahan](https://github.com/y4gizbey)
- **Sürüm:** v0.8

Uygulamanın OCR tarama hassasiyeti ve inpaint modülleri PyQt6 & C++ opencv kütüphaneleriyle optimize edilerek hazırlanmıştır. Sürüm yükseltmek, Pull Request atmak veya hataları (Issues) bildirmek için Github repomu kullanabilirsiniz. Çizgi roman okuyucularınızın şerefine...

NOT: UYGULAMA YENİ OLDUĞU İÇİN BAZI HATA VE EKSİKLİKLER OLABİLİR. BUNLARI BANA BİLDİRİRSENİZ SEVİNİRİM.
