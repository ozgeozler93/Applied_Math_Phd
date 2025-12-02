import os
from dotenv import load_dotenv  # Bu satırı ekleyin
# .env dosyasını yükle (Bu işlem, sanki terminale yazmışsınız gibi anahtarı yükler)
load_dotenv()

from litellm import completion
from googleapiclient.discovery import build
import json

# Model adını ve diğer ayarları başa alalım
MODEL_NAME = "gemini/gemini-2.5-flash"

from datetime import datetime, timedelta

def search_google(query: str):
    """
    Verilen sorgu için Google'da arama yapar ve sonuçları döndürür.
    """
    try:
        print(f"\n[Tool Execution]: Google'da '{query}' aranıyor...")
        api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        cse_id = os.getenv("GOOGLE_SEARCH_CX_ID")
        
        if not api_key or not cse_id:
            return json.dumps({"error": "Google API anahtarı veya CX ID bulunamadı."})

        service = build("customsearch", "v1", developerKey=api_key)
        res = service.cse().list(q=query, cx=cse_id, num=5).execute()
        
        search_results = [item['link'] for item in res.get('items', [])]
        return json.dumps(search_results)
    except Exception as e:
        print(f"Google API ile arama sırasında bir hata oluştu: {e}")
        return json.dumps({"error": f"Google API ile arama sırasında bir hata oluştu: {e}"})

def search_plays_real_data(city: str, date_query: str):
    """
    Belirtilen şehir ve tarih sorgusu için tiyatro oyunlarını biletinial.com'da arar.
    'today' ve 'this week' sorgularını destekler.
    """
    print(f"\n[Tool Execution]: '{city}' için '{date_query}' sorgusuyla oyunlar biletinial.com'da aranıyor...")
    
    query = f"site:biletinial.com {city} tiyatro {date_query}"
    return search_google(query)

def run_theater_agent(messages: list):
    """Tiyatro agent'ını çalıştırır, araçları kullanır ve sonucu kullanıcıya sunar."""
    
    try:
        print(f"--- Sorgu Gönderiliyor... ---")
        response = completion(
            model=MODEL_NAME,
            messages=messages,
            tools=[{
                "type": "function",
                "function": {
                    "name": "search_plays_real_data",
                    "description": "Belirtilen şehir ve tarih için güncel tiyatro oyunlarını web'den kazıyarak bulur.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string", "description": "Oyunların aranacağı şehir, ör. 'Istanbul'"},
                            "date_query": {"type": "string", "description": "Tarih sorgusu, ör. 'today' veya 'this week'"}
                        },
                        "required": ["city", "date_query"]
                    }
                }
            }],
            temperature=0.5
        )

        tool_calls = response.choices[0].message.tool_calls
        if tool_calls:
            print("\n--- Karar: TOOL CALL ---")
            tool_call = tool_calls[0]
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)
            
            print(f"Model, aracı çağırmaya karar verdi: {func_name} (Argümanlar: {func_args})")

            if func_name == "search_plays_real_data":
                tool_result = search_plays_real_data(
                    city=func_args.get("city"), 
                    date_query=func_args.get("date_query")
                )
                print(f"[Tool Execution Result]: {tool_result}")
                
                # Aracı çalıştırdıktan sonra, sonucu LLM'ye geri besleyerek kullanıcı dostu bir özet oluşturmasını sağlıyoruz.
                print("\n--- Sonuç LLM'e Geri Besleniyor ---")
                
                # Hata burada: LLM'in kendi tool_call mesajını da geçmişe eklemeliyiz.
                # Önceki 'messages' listesi + LLM'in cevabı + bizim tool sonucumuz.
                assistant_message = response.choices[0].message
                
                final_messages = messages + [
                    assistant_message, # Modelin tool call içeren cevabı
                    {"role": "tool", "tool_call_id": tool_call.id, "content": tool_result}
                ]
                
                final_response = completion(
                    model=MODEL_NAME,
                    messages=final_messages
                )
                
                print("\n--- Nihai Kullanıcı Cevabı ---")
                final_content = final_response.choices[0].message.content
                print(final_content)
                messages.append({"role": "assistant", "content": final_content})

        else:
            #print("\n--- Karar: Direkt Cevap ---")
            final_content = response.choices[0].message.content
            print(final_content)
            messages.append({"role": "assistant", "content": final_content})

    except Exception as e:
        print(f"\nBir hata oluştu: {e}")
    
    return messages

# --- Ana Çalıştırma Bloğu (İnteraktif Mod) ---
if __name__ == "__main__":
    print("Tiyatro Asistanına hoş geldiniz! Sormak istediğiniz soruyu yazın.")
    print("Çıkmak için 'quit' veya 'exit' yazabilirsiniz.")
    
    # Konuşma geçmişini tutmak için mesaj listesini döngünün dışında başlat
    conversation_history = [
        {"role": "system", "content": "Sen bir Tiyatro Veri Toplama Ajanısın. Kullanıcıdan şehir ve tarih bilgisi alana kadar soru sor. Her iki bilgiyi de aldıktan sonra 'search_plays_real_data' aracını kullan. Bu araç, biletinial.com'da Google araması yaparak sonuçları döndürür."},
    ]

    while True:
        user_query = input("\nSiz: ")
        if user_query.lower() in ["quit", "exit"]:
            print("Görüşmek üzere!")
            break
        
        if not user_query:
            continue
        
        # Kullanıcının yeni mesajını geçmişe ekle
        conversation_history.append({"role": "user", "content": user_query})
        
        # Güncellenmiş konuşma geçmişi ile agent'ı çalıştır
        conversation_history = run_theater_agent(conversation_history)
