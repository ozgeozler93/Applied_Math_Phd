# LLM Prompting ve Araç Kullanımı - Ders Notları

## 📚 Okuma Listem

### Must-Read
- **On the Biology of a Large Language Model** (2 hafta sonraya ertelendi)
  - Kaynak: https://transformer-circuits.pub/2025/attribution-graphs/biology.html

### Nice-to-Read
- **The Illusion of Thinking** - Apple'ın reasoning modeller üzerine makalesi
  - Kaynak: https://ml-site.cdn-apple.com/papers/the-illusion-of-thinking.pdf
  - *Not: 11. slayttaki reasoning modeller konusuyla bağlantılı*

---

## 📝 Ders İçeriği

### 5. Slayt: LLM'leri Kod İçinde Kullanma

**Konu:** Python ile LLM API'lerine nasıl istek gönderilir?

**Önemli Noktalar:**
- `litellm` kütüphanesi kullanılarak Gemini modeline örnek istek
- **Üç temel rol:**
  1. **System (Sistem):** Modelin genel davranış talimatları
  2. **User (Kullanıcı):** Son kullanıcıdan gelen sorgu/komut
  3. **Assistant (Asistan):** Modelin ürettiği yanıt

**Temperature Parametresi:**
- **Yüksek değer:** Daha yaratıcı, geniş bir seçenek yelpazesi
- **Düşük değer:** Daha deterministik, net ve kesin cevaplar
- *💡 İlginç not: Yeni nesil modeller o kadar güçlü ki, bu parametrenin önemi azalıyor*

---

### 6. Slayt: Zero-Shot Prompting

**Tanım:** Modele örnek vermeden, sadece talimatlara dayanarak cevap ürettirme

**Kullanım Alanları:**
- Örnek vermenin mümkün olmadığı durumlar
- Yeni konuların denenmesi
- Model tamamen eğitim sırasında öğrendiği bilgilere dayanır

---

### 7. Slayt: Few-Shot Prompting

**Tanım:** Modele birkaç somut örnek vererek beklenen çıktı formatını öğretme

**Avantajlar:**
- Model, verilen örneklerden bir pattern/desen çıkarır
- Çıktı kalitesi ve formatı örneklere göre şekillenir
- Özellikle spesifik format istenen durumlarda etkili

---

### 8. Slayt: Chain of Thought (CoT) - Düşünce Zinciri

**Tanım:** Modelden adım adım düşünme sürecini göstermesini isteme

**Ne Zaman Kullanılır:**
- Karmaşık problemler
- Basit örneklerle açıklanamayan durumlar
- Yüksek kaliteli ve doğru sonuç gerektiğinde

**Yapı:**
1. **Akıl Yürütme (Reasoning):** Modelin düşünce süreci
2. **Nihai Açıklama (Final Answer):** Son cevap

*💡 Model kendi kendine konuşarak en doğru sonuca ulaşır*

---

### 9. Slayt: Girdi Formatlama (Input Formatting)

**Amaç:** İstemleri yapılandırılmış ve işlenebilir hale getirmek

**Kullanılan Formatlar:**

1. **Markdown:**
   - Vurgu yapmak için
   - Yapılandırılmış talimatlar (kimlik, talimat, örnek)

2. **XML Etiketleri:**
   - `<user_query>`, `<assistant_response>` gibi
   - Bölümleri hiyerarşik olarak ayırma
   - Yazılım tarafından kolayca parse edilebilir çıktı

---

### 10. Slayt: Çıktı Formatlama (Output Formatting)

**Amaç:** Modelin çıktısını yapılandırarak işlenebilir hale getirmek

**Faydaları:**
- `<reasoning>` ve `<final_description>` gibi etiketlerle ayrıştırma
- Post-processing kolaylığı (örn: kullanıcıya sadece final cevap gösterme)
- CoT ile mükemmel uyum
- Sistemler tarafından çalıştırılabilir komutlar üretme

*💡 Bu yaklaşım özellikle Chain of Thought ile birleşince çok güçlü oluyor*

---

### 11. Slayt: Akıl Yürüten Modeller (Reasoning Models)

**Özellik:** Otomatik olarak düşünce süreci üreten modeller

**Nasıl Çalışır:**
- Nihai cevaptan önce `<thinking>` bloğunda kendi kendine düşünür
- Sistematik CoT kullanarak kendini şartlandırır
- Bu düşünme süreci genellikle kullanıcıya gösterilmez

*💡 Model kendi içinde bir hazırlık aşaması yapar, tıpkı bir öğrencinin taslak kağıdını kullanması gibi*

**İlgili Okuma:** Apple'ın "The Illusion of Thinking" makalesi bu modellerin gerçekten "düşünüp düşünmediğini" tartışıyor

---

### 12. Slayt: Araç Çağırma (Tool Calling)

**Tanım:** LLM'lerin dış kaynaklara ve araçlara erişimi

LLM'lerin hafizasi, internette olan her bilgiyi barindirir. Ama internetteki her bilgi guncel degildir hem de yanlis olabilir. Dogru ve guncel bilgiye ulasmak icin dis kaynaklara erismesi gerekebilir.

**Ne Yapabilir:**
- Arama motorlarından güncel bilgi alabilir
- API'lar ve veritabanlarıyla iletişim kurabilir
- Diğer programları çalıştırabilir
- Başka LLM'lerle iş birliği yapabilir

**Örnek Akış:**
1. Modele mevcut araçlar tanıtılır (`search_product_info`, `summarize_reviews`)
2. Model hangi aracı kullanacağına karar verir
3. `<tool_call>` etiketi içinde araç çağırma komutu üretir

*💡 Bu sayede LLM, kendi bilgi sınırlarının ötesine geçebiliyor*


Antropic, bu islemlerin nasil olmasi gerektigini dusunmus, standirze etmis. MCP server araci cikmis. Daha sonra diger sirketler de bu standizasyonu benimsemis.

---

### 13. Slayt: MCP - Model Context Protocol

**Tanım:** Yapay zekanın "USB-C"si - evrensel bir bağlantı standardı

**Neden Devrim Niteliğinde:**
- **Öncesi:** Her model x Her araç = N × M entegrasyon karmaşası
- **Sonrası:** Tek bir standart, herkes birbirine bağlanabilir
- Açık kaynak ve evrensel
- OpenAI, Google DeepMind gibi büyük oyuncular benimsedi

**İş Avantajları:**
- ⬇️ Entegrasyon maliyetleri düşer
- 🔄 Sistemler arası taşınabilirlik artar
- ✅ Denetim süreçleri basitleşir

*💡 Tıpkı USB-C'nin farklı cihazlar arasında evrensel bağlantı sağlaması gibi, MCP de AI ekosisteminde aynı rolü oynuyor*

---

### 14. Slayt: Genel Mimari (General Architecture)

**Sistem Bileşenleri:**

1. **👤 İnsan (Human)**
   - Sistemi kontrol eden nihai kullanıcı
   - *Örnek: Biz*

2. **🖥️ Arayüz (Interface)**
   - Kullanıcının sistemle etkileşime girdiği katman
   - *Örnek: Cline (web uygulaması)*

3. **🤖 LLM**
   - "Orkestra şefi" görevi
   - İstekleri işler, araçları çağırır, süreci yönetir
   - *Örnek: ChatGPT, Claude.ai*

4. **🔧 Ortam (Environment)**
   - Kod çalıştırma, dosya arama gibi işlemlerin yapıldığı alan
   - Sonuçların gözlemlendiği yer
   - *Örnek: VS Code, Cursor*

**İletişim Akışı:**
Sorgu → Netleştirme → Kod Yazma → Test Etme → Sonuçları Gösterme

*💡 Bu mimari, modern AI asistanlarının temelini oluşturuyor. Her bileşen kendi rolünü oynuyor ve birlikte akıllı bir sistem oluşturuyor*

---

## 🎯 Genel Değerlendirme

Bu ders, LLM'lerle etkili çalışmanın temel prensiplerini kapsıyor. Zero-shot'tan başlayıp reasoning modellere, oradan da tool calling ve MCP standardına kadar giden bir yolculuk. En önemli çıkarım: LLM'ler artık sadece metin üreten araçlar değil, dış dünyayla etkileşime girebilen, araçları kullanabilen ve sistemik düşünebilen platformlar haline geliyor.

---

## 📖 Gelecek Hafta İçin Yapılacaklar

- "litellm" kütüphanesi kulanan birkac tane deneme uygulama denenecek, github'a atılacak. 
- Proje konusu düşünmeye başlayacağız. Sonraki hafta da proje üzerinde çalışmaya başlayacağız. Ve takimlara ayrilacagiz.
Örnek proje konusu: Finansal advisor, seyahat planlayıcısı, hocanin derste bahsettigi gibi cesitli kaynaklardan urun tavsiyesi alip urun tavsiye eden uygulama... Matematikde proof checking yapma konusu biraz teorik kisimla bizi ugrastirabilecegi icin oncelikli olarak onerilmedi. Daha cok ugrasmamiz istenilen, uygulamada pratik kazanmamizdi.

> 🎯 *Chip Huyen praktik ML konularında çok iyi kaynaklar üretiyor. Bu yazıda muhtemelen agent'ların mimari tasarımı, kullanım senaryoları ve implementation challenges ele alınıyor.*


## 📖 Gelecek Hafta Islenecek Konular
 - Pratikte Agentic Ai nasil yapiliyor?



*Son güncelleme: 10 Ekim 2025*
*Son guncelleme: [@ozgeozler93]*

