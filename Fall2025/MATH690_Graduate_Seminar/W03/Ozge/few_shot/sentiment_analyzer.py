from litellm import completion
from dotenv import load_dotenv
import os

load_dotenv()

def analyze_sentiment(text):
    """
    Few-Shot Sentiment Analysis: Örneklerle model'i eğit
    """
    try:
        resp = completion(
            model="anthropic/claude-3-5-haiku-latest",
            messages=[
                {
                    "role": "system",
                    "content": """You are a sentiment analyzer. Classify Turkish text as Positive, Negative, or Neutral.

                    **Examples:**

                    Input: "Bu ürün harika! Çok memnun kaldım, herkese tavsiye ederim."
                    Output: Positive

                    Input: "Korkunç bir deneyimdi. Para kaybı. Asla tekrar almam."
                    Output: Negative

                    Input: "Normal bir ürün. Fiyatına göre idare eder."
                    Output: Neutral

                    Input: "Kargo hızlıydı ama ürün beklediğim gibi değildi."
                    Output: Negative

                    Now classify the following text:"""
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            temperature=0.2,
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        
        result = resp["choices"][0]["message"]["content"]
        
        # Sadece sentiment kelimesini al (Positive/Negative/Neutral)
        for sentiment in ["Positive", "Negative", "Neutral"]:
            if sentiment in result:
                return sentiment
        
        return result
    
    except Exception as e:
        return f"Hata: {str(e)}"

# Test et
if __name__ == "__main__":
    print("=" * 60)
    print("FEW-SHOT SENTIMENT ANALYSIS TEST")
    print("=" * 60)
    
    test_texts = [
        "Ürün çok kaliteli, fiyatına göre harika bir alışveriş oldu!",
        "Hiç beğenmedim, paramı boşa harcadım.",
        "İdare eder, çok iyi değil ama kötü de değil.",
        "Müşteri hizmeti berbattı, asla tekrar sipariş vermem!",
        "Kargo çok geç geldi ama ürün güzelmiş.",
        "Gayet başarılı bir ürün, teşekkürler."
    ]
    
    for i, text in enumerate(test_texts, 1):
        sentiment = analyze_sentiment(text)
        print(f"\n{i}. Text: {text}")
        print(f"   Sentiment: {sentiment}")
        print("-" * 60)