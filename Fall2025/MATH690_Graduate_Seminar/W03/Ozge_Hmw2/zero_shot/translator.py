from litellm import completion
from dotenv import load_dotenv
from pathlib import Path
import os

# .env dosyasından API key'i yükle
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"  # -> Ozge/.env
load_dotenv(ENV_PATH)

load_dotenv()

# API key'in yüklendiğini kontrol et
if not os.getenv("ANTHROPIC_API_KEY"):
    print("HATA: .env dosyasında ANTHROPIC_API_KEY bulunamadı!")
    exit()

def translate_text(text, target_language):
    """
    Zero-Shot Translation: Hiç örnek vermeden direkt çeviri yap
    """
    try:
        resp = completion(
            # model="gemini/gemini-2.0-flash-exp",
            model="anthropic/claude-3-5-haiku-latest",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a professional translator. Translate text to {target_language} accurately. And do not change the meaning."
                },
                {
                    "role": "user",
                    "content": f"Translate: {text}"
                }
            ],
            temperature=0.3,  # Düşük temperature = daha tutarlı sonuç
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        
        return resp["choices"][0]["message"]["content"]
    
    except Exception as e:
        return f"Hata oluştu: {str(e)}"

# Test et
if __name__ == "__main__":
    print("=" * 60)
    print("ZERO-SHOT TRANSLATION TEST")
    print("=" * 60)
    
    test_cases = [
        ("Hello, how are you?", "Turkish"),
        ("Bugün hava çok güzel", "English"),
        ("I love programming", "Spanish"),
        ("I love Theatre", "Italian"),
        ("Je suis très heureux aujourd'hui", "English"),
        ("Das Wetter ist heute schön", "English"),
        ("今日はとても良い天気です", "English"),
        ("El clima es agradable hoy", "English"),
        ("El clima es agradable hoy", "Chinese"),
        ("Genelde Fransız ve kıta Avrupa ekolünden etkilenmesi beni şaşırtmamıştı ama. Merleau-Ponty çok temkinli de olsa dönüp dolaşıp Hegel ve Heidegger tarzı coşku felsefesine meylediyor.","English")
    ]
    
    for text, lang in test_cases:
        print(f"\nOriginal : {text}")
        translation = translate_text(text, lang)
        print(f"Translation({lang}) : {translation}")
        print("-" * 60)


