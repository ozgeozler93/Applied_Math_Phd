import json

def load_plays(file_path):
    """
    Verilen dosya yolundan tiyatro oyunlarını yükler.
    Bu bizim veritabanımızı okuyan fonksiyonumuz.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Hata: '{file_path}' dosyası bulunamadı.")
        return []
    except json.JSONDecodeError:
        print(f"Hata: '{file_path}' dosyası düzgün bir JSON formatında değil.")
        return []

def find_matching_plays(plays, city, date):
    """
    Oyun listesi içinde şehir ve tarihe göre eşleşenleri bulur.
    """
    matches = []
    # Kullanıcıdan gelen girdiyi temizleyelim (büyük/küçük harf, boşluk vb.)
    search_city = city.strip().lower()
    search_date = date.strip().lower()

    for play in plays:
        play_city = play.get("city", "").lower()
        play_date = play.get("date", "").lower()

        # Şehir ve tarih eşleşiyorsa, oyunu 'matches' listesine ekle
        if search_city == play_city and search_date == play_date:
            matches.append(play)
    
    return matches

# --- Programın Başlangıç Noktası ---
if __name__ == "__main__":
    print("--- Tiyatro Öneri Agent'ına Hoş Geldiniz! ---")
    
    # 1. Veritabanımızdan oyunları yükle
    all_plays = load_plays("src2/data.json")
    
    if not all_plays:
        print("Sistemde hiç oyun bulunamadı. Program sonlandırılıyor.")
    else:
        # 2. Kullanıcıdan bilgi al
        user_city = input("Hangi şehirdeki oyunları arıyorsunuz? (örn: Istanbul): ")
        user_date = input("Hangi tarih için arama yapıyorsunuz? (örn: 23 Ocak 2026): ")
        
        # 3. Eşleşen oyunları bul
        found_plays = find_matching_plays(all_plays, user_city, user_date)
        
        # 4. Sonuçları kullanıcıya göster
        if found_plays:
            print(f"\n harika! '{user_city}' şehrinde '{user_date}' tarihinde şu oyunlar bulundu:")
            for play in found_plays:
                print(f"  - Başlık: {play['title']}, Mekan: {play['location']}")
        else:
            print(f"\n maalesef, '{user_city}' şehrinde '{user_date}' tarihinde hiç oyun bulunamadı.")
