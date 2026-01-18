# StageAgent: Akıllı Tiyatro Etkinlik Tavsiye Sistemi - Dönem Projesi Sunumu

## Giriş ve Motivasyon 
*   **Proje Adı:** StageAgent - Akıllı Tiyatro Etkinlik Tavsiye Sistemi
*   **Hedef:** Andrew Ng'nin Agentic Design Patterns'larını uygulamalı deneyimlemek
*   **Temel Amaç:** Kullanıcıların doğal dil sorgularıyla tiyatro etkinliklerini bulmasını sağlayan, gelişen bir sistem oluşturmak.
*   **Neden Tiyatro?** (Kişisel ilgi veya projenin gösterim potansiyeli)
*   **Odak Noktaları:**
    *   Multi-Agent Sistemler
    *   Tool (Araç) Kullanım Desenleri
    *   İteratif Geliştirme Yaklaşımı

## Gelişim Süreci: Versiyonlar ve Öğrenimler 

### Versiyon 1: En Basit Başlangıç (`recommender_llm_an1.py`) 
*   **Felsefe:** "Start Simple" (Basit Başla)
*   **Neler Yaptım?** Tek LLM (Gemini), doğrudan kullanıcı sorgusunu iletme.
*   **Karşılaşılan Zorluk:** LLM'in "halüsinasyon" görmesi (gerçek dışı öneriler).
*   **Öğrenim:** LLM'ler yaratıcıdır, ancak güncel ve doğrulanmış bilgi için harici araçlara ihtiyaç duyarlar. (Tool Use zorunluluğu doğdu.)

### Versiyon 2: Sorguyu Anlama ve Yapılandırma (`recommender_llm_an2.py`) 
*   **Felsefe:** "Parse Before Process" (İşlemeden Önce Ayrıştır)
*   **Neler Yaptım?** Sorgudan şehir ve tarihi elle (regex ile) çıkarma, LLM'e yapısal bilgi sağlama.
*   **Karşılaşılan Zorluk:** Halüsinasyonlar azalsa da tamamen bitmedi. LLM hala "nerede" arayacağını bilmiyordu.
*   **Öğrenim:** LLM'e net talimat vermek önemli ama bilgi eksikliğini gidermez. Gerçek veri kaynaklarına bağlantı şart.

### Versiyon 3: Multi-Agent Hibrit Sistem (`recommender_llm_an3.py`) 
*   **Felsefe:** "Combine the best of both approaches" (İki yaklaşımın en iyi yönlerini birleştir)
*   **Neler Yaptım?** Farklı bilgi kaynakları için uzmanlaşmış "ajanlar" oluşturma:
    *   **İBB Şehir Tiyatroları Ajanı:** Web Scraping (`requests`, `BeautifulSoup`)
    *   **Devlet Tiyatroları Ajanı:** Selenium ile otomasyon (Biletinial.com) ve yedek olarak Google Search.
    *   **Özel Tiyatrolar Ajanı:** Gemini'nin Google Search aracı ile arama.
*   **Karşılaşılan Zorluklar:**
    *   Web sitelerinin kırılgan HTML yapıları ve JavaScript bağımlılığı (Selenium öğrenimi).
    *   Selenium'un yavaşlığı ve bakım zorluğu.
    *   LLM'in arama sonuçlarını doğru yorumlaması için "Prompt Engineering" gereksinimi.
*   **Öğrenim:**
    *   Multi-Agent mimarinin gücü: Her işe özel doğru aracı kullanmak.
    *   Hibrit sistemler: Kural tabanlı (scraping) ve LLM tabanlı (arama) ajanların birleşimi.
    *   Sistem dayanıklılığı için "fallback" mekanizmaları.

### Versiyon 4: Harici Araç Entegrasyonu (Google Calendar) (`recommender_llm_an4.py`) 
*   **Felsefe:** "Tool Use" (Araç Kullanımı)
*   **Neler Yaptım?** Google Calendar API entegrasyonu, seçilen oyunu takvime ekleyebilme.
*   **Karşılaşılan Zorluk:** Google OAuth 2.0 yetkilendirme akışını anlama ve uygulama (`credentials.json`, `token.pickle`).
*   **Öğrenim:** Bir ajanın pasif bilgi sağlayıcıdan aktif bir asistana dönüşmesi. Eyleme geçme yeteneği.

### Versiyon 5: Kullanıcı Deneyimi ve Döngü (`recommender_llm_an5.py`) 
*   **Felsefe:** "Multi-Query Interaction" (Çoklu Sorgu Etkileşimi)
*   **Neler Yaptım?** Ana menü yapısı, `sorgu_gecmisi` ile oturum boyunca sorguları saklama.
*   **Karşılaşılan Zorluk:** Programın durumunu (state) yönetmek, modüler kod yazımı.
*   **Öğrenim:** Akıcı ve sürekli bir kullanıcı diyalogunun önemi. Uygulama hissi yaratma.

### Versiyon 6: Bağlam Zenginleştirme (YouTube API) (`recommender_llm_an6.py`) 
*   **Felsefe:** "Context Enrichment" (Bağlam Zenginleştirme)
*   **Neler Yaptım?** YouTube Data API entegrasyonu, oyunlarla ilgili fragman/tanıtım videoları önerme.
*   **Karşılaşılan Zorluk:** YouTube'da alakasız içerikler arasında doğru videoları bulmak için spesifik arama sorguları oluşturma.
*   **Öğrenim:** Bir ajanın sadece birincil görevi değil, kullanıcının karar sürecini destekleyecek ikincil bilgileri de sunmasının değeri.

### Versiyon 7: Arayüze Geçiş (Streamlit) (`recommender_web_an7.py`) 
*   **Felsefe:** "From CLI to GUI" (Komut Satırından Grafiksel Arayüze)
*   **Neler Yaptım?** Mevcut CLI mantığını Streamlit ile web arayüzüne taşıma. Arama formu, sonuç kartları, butonlar, video oynatıcılar.
*   **Karşılaşılan Zorluk:** Streamlit'in `session_state` mekanizmasını ve sayfa yeniden çizim (rerun) mantığını anlama.
*   **Öğrenim:** İyi bir arayüz, karmaşık agent sistemlerini son kullanıcı için basit ve erişilebilir kılar. Hızlı prototipleme araçlarının değeri.

## Genel Değerlendirme ve Gelecek Çalışmalar (10 dakika)

### Elde Edilen Ana Kazanımlar:
*   **Hibrit Sistemlerin Gücü:** Kural tabanlı ve LLM tabanlı yaklaşımların doğru kombinasyonu.
*   **Araçların Önemi:** LLM'lerin harici araçlarla güçlendirilerek asistan rolüne bürünmesi.
*   **İteratif Geliştirmenin Değeri:** Adım adım ilerlemenin faydaları.

### Gelecek Çalışmalar İçin Fikirler:
*   Kişiselleştirme (Kullanıcı tercihlerine göre öneriler)
*   Geribildirim Döngüsü (Kullanıcı beğenilerine göre öğrenme)
*   **Grup Planlaması:** Arkadaşların ortak takvimine göre otomatik etkinlik planlama.

