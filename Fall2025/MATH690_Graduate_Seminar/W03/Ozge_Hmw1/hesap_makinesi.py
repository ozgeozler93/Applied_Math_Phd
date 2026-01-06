#!/usr/bin/env python3
"""
LLM Tabanlı Hesap Makinesi
Bu uygulama Anthropic Claude API kullanarak matematiksel hesaplamalar yapar.
"""

import os
from dotenv import load_dotenv
from anthropic import Anthropic

# .env dosyasından API anahtarını yükle
load_dotenv()

# Anthropic client oluştur
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def hesapla(matematik_ifadesi: str) -> str:
    """
    LLM kullanarak matematiksel ifadeyi hesaplar.
    
    Args:
        matematik_ifadesi: Hesaplanacak matematiksel ifade
        
    Returns:
        Hesaplama sonucu
    """
    # Claude'a gönderilecek prompt
    prompt = f"""Sen bir hesap makinesisin. Sadece matematiksel sonucu sayı olarak ver, başka açıklama yapma.

Hesapla: {matematik_ifadesi}

Sadece sonucu yaz (örn: 42)"""

    try:
        # Anthropic Claude API çağrısı
        message = client.messages.create(
            model="claude-3-haiku-20240307",  # En ucuz ve hızlı model
            max_tokens=100,
            temperature=0,  # Tutarlı sonuçlar için
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Sonucu al
        sonuc = message.content[0].text.strip()
        return sonuc
        
    except Exception as e:
        return f"Hata oluştu: {str(e)}"

def main():
    """Ana program döngüsü"""
    print("=" * 60)
    print("LLM TABANLI HESAP MAKİNESİ")
    print("=" * 60)
    print("Claude 3 Haiku modeli kullanılıyor")
    print("Çıkmak için 'q' veya 'çık' yazın\n")
    
    while True:
        # Kullanıcıdan ifade al
        ifade = input("Hesaplamak istediğiniz ifadeyi girin: ").strip()
        
        # Çıkış kontrolü
        if ifade.lower() in ['q', 'çık', 'cik', 'exit', 'quit']:
            print("\nProgram sonlandırılıyor...")
            break
        
        # Boş girdi kontrolü
        if not ifade:
            print("Lütfen bir ifade girin!\n")
            continue
        
        # Hesaplama yap
        print(f"\nHesaplanıyor: {ifade}")
        sonuc = hesapla(ifade)
        print(f"Sonuç: {sonuc}\n")
        print("-" * 60 + "\n")

if __name__ == "__main__":
    main()
