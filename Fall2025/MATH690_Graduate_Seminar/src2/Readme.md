
# Dönem Projesi Raporu: StageAgent - Akıllı Tiyatro Etkinlik Tavsiye Sistemi

**Hazırlayan:** Makbule Özler
**Tarih:** 18.01.2026

## 1. Projeye Giriş ve Motivasyon

Bu proje, bir "dönem projesi" olarak, LLM (Büyük Dil Modelleri) ve "agentic" (fail) sistemler konusundaki yeteneklerimi geliştirmek amacıyla hayata geçirilmiştir. Temel motivasyonum, Andrew Ng'nin "Agentic Design Patterns" üzerine yaptığı çalışmaları ve tavsiyelerini uygulamalı olarak deneyimlemekti. Projenin ana hedefi, kullanıcıların doğal dil sorgularıyla belirli bir şehir ve tarihteki tiyatro etkinliklerini bulmalarını sağlayan, zamanla daha karmaşık ve yetenekli hale gelen bir tavsiye sistemi (recommender system) geliştirmektir.

Bu yola çıkarken amacım mükemmel bir ürün ortaya koymaktan ziyade, bir "agent" (fail) sisteminin nasıl evrildiğini, hangi zorluklarla karşılaşıldığını ve bu süreçte hangi öğrenimleri elde ettiğimi belgelemektir. Bu rapor, `recommender_llm_an1.py`'den `recommender_web_an7.py`'ye kadar olan tüm geliştirme adımlarını, karşılaştığım zorlukları ve bu zorlukları aşmak için kullandığım yöntemleri "acemi" bir geliştiricinin gözünden anlatmaktadır.

Projenin temel odak noktaları şunlardır:
- **Multi-Agent Sistemler:** Farklı bilgi kaynaklarını (web scraping, Selenium, API'lar) ayrı birer "uzman" gibi kullanarak daha güvenilir ve kapsamlı sonuçlar elde etme.
- **Tool (Araç) Kullanım Desenleri:** LLM'lerin yeteneklerini harici araçlarla (Google Search, Google Calendar, YouTube API) zenginleştirerek daha işlevsel bir sistem kurma.
- **İteratif Geliştirme:** "Önce basit bir başlangıç yap, sonra sürekli iyileştir" prensibini takip ederek karmaşık bir sistemi adım adım inşa etme.

Bu rapor, kodun kendisi kadar, bu kodu yazarken geçtiğim düşünce süreçlerini de yansıtmayı amaçlamaktadır.

---

## 2. Geliştirme Süreci ve Versiyonlar

### Versiyon 1: `recommender_llm_an1.py` - En Basit Başlangıç (Andrew Ng Prensibi 1)

**Felsefe:** "Start Simple" (Basit Başla)

Her büyük yolculuğun ilk adımı gibi, bu projeye de olabilecek en basit şekilde başladım. Amacım, sadece temel bir fikrin çalışıp çalışmadığını görmekti: Bir LLM, tiyatro tavsiyesi yapabilir mi?

**Mimari:**
- **Tek Ajan:** Sadece Gemini API'sini kullanan bir "LLM ajanı".
- **Tek Araç:** `google.genai` kütüphanesi.
- **Tek Fonksiyon:** `tiyatro_ara_basit(sorgu)`

**İşleyiş:**
1. Kullanıcıdan basit bir metin girdisi alınır (örn: "İstanbul'da 23 ocak tiyatro").
2. Bu girdi, olduğu gibi bir "prompt" (istek metni) içine yerleştirilir.
3. Prompt, Gemini API'sine gönderilir.
4. Gelen yanıt, ham metin olarak ekrana basılır.

**Kod Örneği (`recommender_llm_an1.py`):**
```python
import os
import google.genai as genai

# ... API anahtarı kurulumu ...

def tiyatro_ara_basit(sorgu):
    """En basit tiyatro arama"""
    prompt = f"""
    Kullanıcı tiyatro arıyor: "{sorgu}"
    Bu kişiye tiyatro önerileri yap.
    5-6 öneri yeterli.
    """
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=prompt
    )
    return response.text

sorgu = input("Ne arıyorsunuz? (örn: İstanbul'da 23 ocak tiyatro): ")
sonuc = tiyatro_ara_basit(sorgu)
print(sonuc)
```

**Karşılaşılan Zorluklar ve Öğrenimler:**
- **Zorluk:** LLM'in verdiği cevaplar tamamen "halüsinasyon" idi. Yani, gerçekte var olmayan oyunları ve mekanları uyduruyordu. Çünkü LLM'in o anki bilgi tabanında güncel ve doğrulanmış bir etkinlik takvimi yoktu.
- **Öğrenim:** LLM'ler, doğaları gereği yaratıcı metin üretirler. Onlara güncel ve gerçek dünya verisi sağlamadan, onlardan "gerçek" bilgi beklemek hataydı. Bu, "Tool Use" (Araç Kullanımı) ve harici bilgi kaynaklarına bağlanmanın neden bu kadar kritik olduğunu ilk elden deneyimlememi sağladı.

---

### Versiyon 2: `recommender_llm_an2.py` - Sorguyu Anlama ve Yapılandırma

**Felsefe:** "Parse Before Process" (İşlemeden Önce Ayrıştır)

İlk versiyonda LLM'in uydurma cevaplar verdiğini gördükten sonra, sorunun bir kısmının da LLM'e çok belirsiz bir görev vermek olduğunu fark ettim. "İstanbul'da 23 ocak tiyatro" sorgusunu doğrudan LLM'e vermek yerine, bu sorgudan kritik bilgileri (şehir, tarih) kendim çıkarıp LLM'e daha yapısal bir görev verirsem ne olurdu?

**Mimari:**
- **Tek Ajan:** Hala sadece Gemini API'si.
- **Yeni Yetenek:** Sorgu ayrıştırma (`sorguyu_ayristir` fonksiyonu).
- **Gelişmiş Prompt:** LLM'e artık "Şehir: İstanbul, Tarih: 2026-01-23" gibi yapısal bilgi veriliyordu.

**İşleyiş:**
1. Kullanıcıdan sorgu alınır.
2. `sorguyu_ayristir` fonksiyonu, basit `regex` ve sözlükler kullanarak sorgudan **şehir** ve **tarih** bilgilerini çıkarır.
3. Bu yapısal bilgiler, LLM'e gönderilen prompt'a eklenir. Bu, LLM'in daha odaklı ve "rolüne uygun" cevaplar vermesini teşvik eder.

**Kod Örneği (`recommender_llm_an2.py`):**
```python
def sorguyu_ayristir(sorgu):
    """Sorgudan şehir ve tarih çıkar"""
    # ... sehirler ve aylar için sözlükler ...
    # ... regex ile tarih arama ...
    return sehir, tarih

def tiyatro_ara_akilli(sehir, tarih, sorgu):
    prompt = f"""
    Kullanıcı: "{sorgu}"
    Şehir: {sehir}
    Tarih: {tarih_formatli}
    
    Bu şehir ve tarih için tiyatro önerileri yap.
    Lütfen gerçekçi öneriler yap (uydurma).
    """
    # ... API çağrısı ...
```

**Karşılaşılan Zorluklar ve Öğrenimler:**
- **Zorluk:** Sonuçlar bir miktar iyileşse de, LLM hala büyük ölçüde halüsinasyon görmeye devam ediyordu. Çünkü hala güncel veri kaynaklarına erişimi yoktu. Ona sadece ne araması gerektiğini daha iyi söylüyordum, ama "nerede" arayacağını söylemiyordum.
- **Öğrenim:** Yapısal veri ve net talimatlar, LLM'in çıktısını iyileştirmek için güçlü bir yöntemdir. Ancak bu, temel "bilgi eksikliği" sorununu çözmez. Gerçek dünyadan veri alacak araçlara (tools) olan ihtiyaç artık kaçınılmazdı.

---

### Versiyon 3: `recommender_llm_an3.py` - Multi-Agent Hibrit Sistem

**Felsefe:** "Combine the best of both approaches" (İki yaklaşımın da en iyi yönlerini birleştir)

Bu versiyon, projenin en büyük sıçramalarından birini temsil ediyor. Artık tek bir LLM ajanına güvenmek yerine, her biri kendi alanında uzmanlaşmış farklı "veri toplama ajanları" oluşturmaya karar verdim. Bu, gerçek bir "Multi-Agent" sistemine attığım ilk adımdı.

**Mimari - Bir "Agent" Orkestrası:**
1.  **İBB Şehir Tiyatroları Ajanı:**
    -   **Araç:** `requests` ve `BeautifulSoup` kütüphaneleri.
    -   **Görev:** İBB Şehir Tiyatroları'nın web sitesindeki takvimi "scrape" ederek (kazıyarak) yapısal veri (oyun adı, sahne, saat, bilet durumu) elde etmek. Bu, en güvenilir ve kesin veri kaynağımdı.

2.  **Devlet Tiyatroları Ajanı:**
    -   **Araç:** `Selenium` ve `webdriver-manager`.
    -   **Görev:** Biletinial.com'un Devlet Tiyatroları sayfasını otomasyon ile kontrol etmek. JavaScript ile yüklenen dinamik içeriği alabilmek için Selenium kullanmak zorunda kaldım. Bu ajan, web sitesiyle bir "kullanıcı gibi" etkileşime giriyordu (şehir seç, takvime bak).
    -   **Yedek Plan:** Selenium başarısız olursa, bu ajan "fallback" olarak Gemini'nin **Google Search** aracını kullanan bir alt ajana devrediyordu. Bu, sistemin dayanıklılığını (resilience) artırdı.

3.  **Özel Tiyatrolar Ajanı:**
    -   **Araç:** Gemini API'sinin dahili **Google Search** aracı.
    -   **Görev:** Özel tiyatrolar (DasDas, Zorlu PSM vb.) için tek bir merkezi veri kaynağı olmadığından, bu ajanın görevi internette arama yapmaktı. Prompt'u, belirli siteleri (Biletix, Passo) hedef alacak şekilde özel olarak tasarlandı.

**İşleyiş:**
1.  Ana program (orkestra şefi), kullanıcının sorgusunu ayrıştırır.
2.  Her bir "uzman ajanı" (İBB, Devlet, Özel) paralel olarak göreve çağırır.
3.  İBB ajanı web scraping yapar.
4.  Devlet Tiyatroları ajanı Selenium ile veri çekmeye çalışır, olmazsa Google Search'e başvurur.
5.  Özel Tiyatrolar ajanı doğrudan Google Search yapar.
6.  Tüm ajanlardan gelen veriler toplanır ve kullanıcıya sunulur.

**Karşılaşılan Zorluklar ve Öğrenimler:**
-   **Zorluk (Web Scraping):** Web sitelerinin HTML yapıları inanılmaz derecede kırılgandır. İBB'nin sitesindeki `<table>` yapısı beklediğim gibi değildi (örn: `<th>` yerine `<td>` kullanılması). Biletinial'ın sitesi ise JavaScript'e o kadar bağımlıydı ki, `requests` ile veri almak imkansızdı. Bu, Selenium'u öğrenmemi zorunlu kıldı.
-   **Zorluk (Selenium):** Selenium yavaş ve kaynak tüketen bir araç. Headless modda bile çalışması zaman alıyor. Ayrıca, web sitesindeki en ufak bir CSS class değişikliği tüm otomasyonu kırabiliyor. Bu yüzden "fallback" (yedek) mekanizması çok önemli.
-   **Zorluk (Google Search):** Gemini'nin Google Search aracı çok güçlü olsa da, LLM'in arama sonuçlarını "yorumlayıp" istediğim formatta sunmasını sağlamak ciddi bir "prompt engineering" (istek metni mühendisliği) gerektirdi. Bazen alakasız sonuçlar veya yanlış formatta çıktılar verebiliyordu.
-   **Öğrenim (Multi-Agent Gücü):** Her iş için doğru aracı kullanmak inanılmaz sonuçlar veriyor. Web scraping gibi kesin sonuç gereken yerlerde kural tabanlı bir ajan, belirsiz ve dağınık veri kaynakları için ise LLM tabanlı bir arama ajanı kullanmak, sistemin hem güvenilirliğini hem de esnekliğini artırdı. Bu, "hibrit" sistemlerin gücünü gösterdi.

---

### Versiyon 4: `recommender_llm_an4.py` - Harici Araç Entegrasyonu (Google Calendar)

**Felsefe:** "Tool Use" (Araç Kullanımı)

Sistem artık güvenilir veri bulabiliyordu. Peki bu veriyi sadece göstermekle mi yetinmeliydik? Bir "agent", kullanıcının hayatını kolaylaştırmak için bir adım daha atmalıydı. Bu versiyonda, kullanıcının bulduğu bir etkinliği doğrudan kendi takvimine eklemesini sağlayan bir araç entegre ettim.

**Mimari:**
- **Yeni Araç:** Google Calendar API.
- **Yeni Yetenek:** `add_to_google_calendar` fonksiyonu.
- **Etkileşimli Akış:** Arama sonuçları listelendikten sonra, kullanıcıya hangi oyunu takvimine eklemek istediği sorulur.

**İşleyiş:**
1. Kullanıcı oyunları arar ve sonuçlar listelenir.
2. Program, "Takvime eklemek istediğiniz oyunun numarasını girin" diye sorar.
3. Kullanıcı bir numara seçtiğinde:
    a. `get_calendar_service` fonksiyonu, `credentials.json` ve `token.pickle` dosyalarını kullanarak Google Calendar API'sine bağlanır (OAuth 2.0 akışı).
    b. `add_to_google_calendar` fonksiyonu, oyunun bilgilerini (ad, mekan, saat) ve tarihi kullanarak bir takvim etkinliği (event) oluşturur.
    c. Etkinlik, kullanıcının birincil takvimine gönderilir.

**Kod Örneği (`recommender_llm_an4.py`):**
```python
# ... Google Calendar kütüphaneleri import edilir ...

def get_calendar_service():
    # ... OAuth 2.0 ile yetkilendirme ve token yönetimi ...
    return build('calendar', 'v3', credentials=creds)

def add_to_google_calendar(oyun, tarih_str, sehir):
    service = get_calendar_service()
    event = {
        'summary': f"🎭 {oyun['oyun']}",
        'location': f"{oyun.get('sahne', 'Bilinmiyor')}, {sehir}",
        # ... başlangıç ve bitiş zamanları ...
    }
    service.events().insert(calendarId='primary', body=event).execute()
```

**Karşılaşılan Zorluklar ve Öğrenimler:**
- **Zorluk:** Google API'lerinin yetkilendirme süreci (OAuth 2.0) ilk başta karmaşık geldi. `credentials.json` dosyasını oluşturmak, doğru "scope"ları (izinleri) belirlemek ve token'ların nasıl yönetildiğini anlamak zaman aldı.
- **Öğrenim:** Bir "agent" sisteminin gücü, sadece bilgi bulmak değil, aynı zamanda bu bilgiyle "eyleme geçmektir". Takvime etkinlik eklemek gibi basit bir "tool", uygulamanın değerini ve kullanışlılığını kat kat artırdı. Bu, bir agent'ın pasif bir bilgi sağlayıcıdan, aktif bir "asistan"a nasıl dönüşebileceğinin en güzel örneğiydi.

---

### Versiyon 5: `recommender_llm_an5.py` - Kullanıcı Deneyimi ve Döngü

**Felsefe:** "Multi-Query Interaction" (Çoklu Sorgu Etkileşimi)

Önceki versiyonlarda program her arama sonrası kapanıyordu. Kullanıcı yeni bir arama yapmak için programı yeniden başlatmak zorundaydı. Bu, "agentic" bir deneyimden çok, basit bir "script" deneyimiydi. Bu versiyonda, kullanıcıya bir ana menü sunarak ve sorgu geçmişini tutarak daha akıcı ve sürekli bir diyalog ortamı yarattım.

**Mimari:**
- **Ana Döngü:** `while True` döngüsü içinde çalışan bir ana menü.
- **Durum Yönetimi (State Management):** `sorgu_gecmisi` adında bir liste, kullanıcının yaptığı tüm aramaları oturum boyunca saklar.
- **Modüler Fonksiyonlar:** Arama (`sorgu_yap`) ve takvim işlemleri (`takvim_islemleri`) ana döngüden çağrılan ayrı fonksiyonlara bölündü.

**İşleyiş:**
1. Program ana menüyü gösterir: "1. Yeni Arama", "2. Geçmiş Sorgular", "3. Çıkış".
2. Kullanıcı "1"i seçerse, arama süreci başlar. Arama bittikten sonra takvim ekleme adımı gelir. Bu adım bitince program tekrar ana menüye döner.
3. Kullanıcı "2"yi seçerse, `sorgu_gecmisi` listesindeki tüm geçmiş aramalar gösterilir.
4. Kullanıcı "3"ü seçerse, ana döngü kırılır ve program sonlanır.

**Karşılaşılan Zorluklar ve Öğrenimler:**
- **Zorluk:** Programın state'ini (durumunu) yönetmek, özellikle birden fazla sorgu ve sonuç arasında geçiş yaparken, değişkenlerin doğru şekilde aktarılmasını gerektirdi. Kodun daha modüler ve organize olması kritik hale geldi.
- **Öğrenim:** İyi bir "agent", tek seferlik görevler yapan bir araç değil, kullanıcıyla sürekli bir diyalog halinde olan bir yardımcıdır. Bir ana menü ve sorgu geçmişi gibi basit kullanıcı deneyimi (UX) iyileştirmeleri, programı bir "araç" olmaktan çıkarıp bir "uygulama" hissiyatına yaklaştırdı.

---

### Versiyon 6: `recommender_llm_an6.py` - Bağlam Zenginleştirme (YouTube API)

**Felsefe:** "Context Enrichment" (Bağlam Zenginleştirme)

Kullanıcı artık bir oyun bulup takvimine ekleyebiliyordu. Ama o oyuna bilet almadan önce daha fazla bilgi edinmek isterse ne olacaktı? Oyunun fragmanını, oyuncularla yapılmış bir röportajı veya oyundan kısa bir sahneyi izlemek, karar verme sürecini çok daha zenginleştirirdi.

**Mimari:**
- **Yeni Araç:** YouTube Data API v3.
- **Yeni Yetenek:** `search_youtube_videos` fonksiyonu.
- **Gelişmiş Etkileşim:** Kullanıcı bir oyunu takvime eklemeden önce, o oyunla ilgili YouTube videolarını arama ve izleme seçeneği sunulur.

**İşleyiş:**
1. Arama sonuçları listelenir.
2. Kullanıcıya "Takvime ekle" veya "Video ara" gibi seçenekler sunulur (bu versiyonda takvim akışına entegre edildi).
3. Kullanıcı bir oyun için video istediğinde:
    a. `search_youtube_videos` fonksiyonu, oyun adını kullanarak (`"{oyun_adi} tiyatro fragman"`, `"{oyun_adi} sahnesi"` gibi birden fazla potansiyel sorgu ile) YouTube API'sine bir arama isteği gönderir.
    b. API'den dönen en alakalı videolar (başlık, link, kanal adı) parse edilir.
    c. Sonuçlar kullanıcıya listelenir ve isteğe bağlı olarak tarayıcıda açılır.

**Karşılaşılan Zorluklar ve Öğrenimler:**
- **Zorluk:** YouTube'da doğru videoyu bulmak, Google'da arama yapmaktan daha zordu. Çok fazla alakasız içerik (vloglar, eleştiriler) çıkabiliyordu. Bu yüzden arama sorgularını `"tiyatro oyunu fragman"`, `"sahnesi"` gibi anahtar kelimelerle daha spesifik hale getirmek gerekti.
- **Öğrenim:** Bir "agent" sadece birincil görevi (etkinlik bulmak) yapmakla kalmamalı, aynı zamanda kullanıcının karar verme sürecini destekleyecek "ikincil" ve "bağlamsal" bilgiler de sunmalıdır. Bu, kullanıcıya daha bütünsel ve zengin bir deneyim sunar ve agent'ın "akıllı" olduğu algısını güçlendirir.

---

### Versiyon 7: `recommender_web_an7.py` - Arayüze Geçiş (Streamlit)

**Felsefe:** "From CLI to GUI" (Komut Satırından Grafiksel Arayüze)

Proje artık o kadar çok yeteneğe sahipti ki, komut satırı (CLI) arayüzü yetersiz kalmaya başladı. Kullanıcıların sonuçları daha rahat görmesi, butonlarla etkileşime girmesi ve videoları doğrudan arayüzde izlemesi gerekiyordu. Bu yüzden, tüm bu `agentic` mantığı alıp bir web arayüzüne taşıdım.

**Mimari:**
- **Arayüz Kütüphanesi:** `Streamlit`.
- **Durum Yönetimi (State Management):** Streamlit'in `st.session_state` mekanizması, CLI versiyonundaki `sorgu_gecmisi`, `tum_oyunlar` gibi değişkenleri yönetmek için kullanıldı.
- **Bileşen Tabanlı Tasarım:** Arama formu, sonuç kartları, butonlar ve video oynatıcılar gibi UI bileşenleri kullanıldı.

**İşleyiş:**
1. `recommender_llm_an6.py`'deki tüm "backend" mantığı (arama, scraping, API çağrıları) fonksiyonlar olarak korundu.
2. Streamlit kullanılarak bir yan menü (sidebar), ana içerik alanı ve sekmeler (tabs) oluşturuldu.
3. Kullanıcı arama formuna bilgileri girip butona tıkladığında, `sorgu_yap` fonksiyonu tetiklenir.
4. Dönen sonuçlar, `st.session_state`'e kaydedilir.
5. Streamlit, `st.session_state`'deki değişiklikleri algılar ve arayüzü yeniden çizer (rerun), sonuçları dinamik olarak oluşturulmuş kartlar halinde gösterir.
6. Her kartın üzerindeki "Takvime Ekle" veya "Videoları Göster" butonları, ilgili backend fonksiyonlarını çağırır.

**Karşılaşılan Zorluklar ve Öğrenimler:**
- **Zorluk:** Streamlit'in "stateful" (durum bilgisi olan) yapısını anlamak ve yönetmek, CLI'daki basit döngüden daha farklı bir düşünme biçimi gerektirdi. Bir butona tıklandığında sayfanın yeniden çizilmesi (rerun) ve `session_state`'in bu döngüde nasıl korunacağı, başlangıçta kafa karıştırıcıydı.
- **Öğrenim:** İyi bir arayüz, en karmaşık "agent" sistemini bile son kullanıcı için basit ve anlaşılır hale getirebilir. Streamlit gibi araçlar, backend mantığına odaklanmış geliştiricilerin bile hızla prototip ve demo'lar oluşturabilmesi için inanılmaz bir güç sunuyor.

---

## 3. Agent Mimarisi ve Çalışma Prensibi

Bu projenin kalbinde, tek bir monolitik yapı yerine, her biri belirli bir görevde uzmanlaşmış "ajanların" ve "araçların" işbirliği yaptığı bir sistem yatmaktadır. Bu mimari, sistemin hem esnekliğini hem de güvenilirliğini artırmaktadır.

### Çalışma Akışı Şeması

Aşağıdaki şema, kullanıcı sorgusundan nihai eyleme kadar olan tüm süreci özetlemektedir:

```
+-------------------------------------------------------------------------+
|                                KULLANICI                                |
|                  (Doğal Dil Sorgusu: "22 ocak istanbul")                 |
+----------------------------------+--------------------------------------+
                                   |
                                   v
+-------------------------------------------------------------------------+
|                      STAGEAGENT (ORKESTRATÖR/ANA PROGRAM)                 |
|            (Görevi alır, doğru ajanlara delege eder, sonuçları birleştirir) |
+----------------------------------+--------------------------------------+
                                   |
                                   v
+-------------------------------------------------------------------------+
|                         Sorgu Ayrıştırıcı (Parser)                        |
|                     (Şehir: İstanbul, Tarih: 2026-01-22)                  |
+----------------------------------+--------------------------------------+
                                   |
+----------------------------------+----------------------------------------------------------+
| Delege Edilen Veri Toplama Görevleri (Paralel Çalışır)                                      |
|                                                                                             |
|    +--------------------------+      +-------------------------------+      +--------------------------+
|    |   İBB Tiyatroları Ajanı  |      |  Devlet Tiyatroları Ajanı     |      |  Özel Tiyatrolar Ajanı   |
|    +--------------------------+      +-------------------------------+      +--------------------------+
|              |                                 |                                 |
|              v                                 v                                 v
|    +--------------------------+      +-------------------------------+      +--------------------------+
|    | Aracı: Web Scraping      |      | Aracı 1: Selenium             |      | Aracı: Google Search     |
|    | (requests, BeautifulSoup)|      | (JS-yoğun site için)          |      | (LLM ile arama)          |
|    +--------------------------+      +-------------+-----------------+      +--------------------------+
|              |                                 | (Başarısız olursa)              |
|              v                                 v                                 v
|    [ İBB Web Sitesi ]                +-------------------------------+      [     Google.com       ]
|                                      | Aracı 2: Google Search        |
|                                      +-------------------------------+
|                                                |
|                                                v
|                                      [    Biletinial.com     ]
|
+----------------------------------+----------------------------------------------------------+
                                   |
                                   v
+-------------------------------------------------------------------------+
|                  STAGEAGENT (Gelen verileri birleştirir)                  |
+----------------------------------+--------------------------------------+
                                   |
                                   v
+-------------------------------------------------------------------------+
|                        [ Birleştirilmiş Sonuç Listesi ]                     |
|                              (Kullanıcıya Sunulur)                        |
+----------------------------------+--------------------------------------+
                                   ^
                                   |
+----------------------------------+--------------------------------------+
|                                KULLANICI                                |
|           (Seçim: '3 Numaralı Oyunu Takvime Ekle' veya '5 için Video Göster') |
+----------------------------------+--------------------------------------+
                                   |
                                   v
+-------------------------------------------------------------------------+
|                      STAGEAGENT (Yeni görevi alır)                      |
+----------------------------------+--------------------------------------+
                                   |
                +------------------+-------------------+
                |                                      |
                v                                      v
+----------------------------------+   +-----------------------------------+
|     Eylem Aracı: Google Calendar     |   Bağlam Aracı: YouTube API         |
+----------------------------------+   +-----------------------------------+
                |                                      |
                v                                      v
      [ Takvime Yeni Etkinlik Ekle ]         [ Video Önerileri Sun ]


```

### Mimarinin Açıklaması

1.  **Orkestratör (Orchestrator):** Ana `main()` fonksiyonu gibi çalışan merkezi beyindir. Kullanıcıdan gelen ilk sorguyu alır ve hangi adımların atılması gerektiğine karar verir.
2.  **Sorgu Ayrıştırıcı (Parser):** "22 ocak istanbul" gibi anlamsız bir metni, makinenin anlayabileceği yapısal verilere (`şehir=İstanbul`, `tarih=2026-01-22`) dönüştüren ilk basit ajandır.
3.  **Veri Toplama Ajanları (Data Gathering Agents):** Projenin "multi-agent" yapısının temelini oluştururlar. Her biri, farklı bir veri kaynağı ve farklı bir yöntem konusunda uzmanlaşmıştır:
    *   **İBB Ajanı:** Güvenilir ve yapısı belli bir web sitesi için en verimli yöntem olan **Web Scraping**'i kullanır.
    *   **Devlet Tiyatroları Ajanı:** JavaScript ile çalışan dinamik bir site için daha güçlü bir araç olan **Selenium**'u kullanır. Bu ajanın zekası, Selenium başarısız olduğunda pes etmeyip bir **yedek plana (Google Search)** başvurmasıdır.
    *   **Özel Tiyatrolar Ajanı:** Merkezi bir veri kaynağı olmadığı için en esnek araç olan **LLM destekli Google Search**'ü kullanır. Bu ajan, internetin dağınık yapısıyla başa çıkmak için tasarlanmıştır.
4.  **Eylem ve Bağlam Araçları (Action & Context Tools):** Veri toplandıktan sonra devreye girerler:
    *   **Google Calendar Aracı:** Sadece bilgi bulmakla kalmaz, kullanıcının dünyasında gerçek bir **eylem** gerçekleştirir (takvime etkinlik ekler).
    *   **YouTube Aracı:** Mevcut bilgiyi (oyun adı), kullanıcıya daha zengin bir **bağlam** sunmak için yeni bilgilerle (videolar) zenginleştirir.

Bu mimari, her iş için en uygun aracın seçilmesini sağlayarak hem daha doğru sonuçlar elde edilmesine olanak tanır hem de sistemin bir bütün olarak daha yetenekli ve "akıllı" davranmasını sağlar.

---

## 4. Genel Değerlendirme ve Gelecek Çalışmalar

Bu proje, basit bir LLM çağrısından başlayarak, birden fazla "uzman" ajanın işbirliği yaptığı, harici araçlarla (Google, YouTube, Calendar) zenginleştirilmiş ve sonunda kullanıcı dostu bir web arayüzüne sahip hibrit bir sisteme dönüştü. Bu süreç, "agentic design patterns" konusundaki teorik bilgileri pratiğe dökmemi sağladı.

**Elde Edilen Ana Kazanımlar:**
- **Hibrit Sistemlerin Gücü:** Ne zaman kural tabanlı (web scraping) ne zaman LLM tabanlı (Google Search) bir yaklaşım kullanılacağını öğrenmek, sistemin hem doğruluğunu hem de esnekliğini artırdı.
- **Araçların Önemi:** Bir LLM'in tek başına ne kadar "yetersiz" kaldığını ve doğru araçlarla donatıldığında nasıl güçlü bir "asistan" haline gelebildiğini gördüm.
- **İteratif Geliştirmenin Değeri:** Her adımda küçük ama işlevsel bir prototip ortaya çıkarmak, motivasyonu yüksek tuttu ve bir sonraki adımın ne olması gerektiğini netleştirdi.

**Gelecek Çalışmalar İçin Fikirler:**
- **Kişiselleştirme:** Kullanıcının geçmiş tercihlerine (sevdiği türler, sık gittiği mekanlar) göre kişisel tavsiyeler sunan bir "hafıza" mekanizması eklenebilir.
- **Geribildirim Döngüsü:** Kullanıcıların tavsiyeleri beğenip beğenmediğini (thumbs up/down) sorarak, gelecekteki tavsiyelerin kalitesini artıracak bir "reinforcement learning" (pekiştirmeli öğrenme) döngüsü kurulabilir.
- **Grup Planlaması:** Birden fazla arkadaşın Google Takvim yetkisi vermesiyle, herkesin ortak olarak müsait olduğu bir zaman dilimini otomatik olarak bulan ve buna göre tiyatro önerileri sunan bir özellik eklenebilir. Bu, sosyal etkinlik planlamasını büyük ölçüde otomatize edebilir.

