import os
from dotenv import load_dotenv  # Bu satırı ekleyin
# .env dosyasını yükle (Bu işlem, sanki terminale yazmışsınız gibi anahtarı yükler)
load_dotenv()

from litellm import completion
from tavily import TavilyClient
import json

# Model adını ve diğer ayarları başa alalım
MODEL_NAME = "gemini/gemini-2.5-flash"

from datetime import datetime, timedelta

def search_tavily(query: str):
    """
    Uses Tavily API to search for the given query and returns the results.
    """
    try:
        print(f"\n[Tool Execution]: Searching Tavily for '{query}'...")
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return json.dumps({"error": "Tavily API key not found."})

        client = TavilyClient(api_key=api_key)
        # Use 'advanced' search to get the content of the pages directly.
        response = client.search(query=query, search_depth="advanced", max_results=3)
        
        # The 'content' will now contain the scraped text from the web pages.
        search_results = [{"title": item['title'], "url": item['url'], "content": item['content']} for item in response.get('results', [])]
    
        return json.dumps(search_results, ensure_ascii=False)
    except Exception as e:
        print(f"An error occurred during Tavily search: {e}")
        return json.dumps({"error": f"An error occurred during Tavily search: {e}"})

def search_plays_real_data(city: str, date_query: str):
    """
    Finds theater plays for a given city and date query by searching the web.
    Supports queries like 'today' and 'this week'.
    """
    print(f"\n[Tool Execution]: Searching for plays in '{city}' for '{date_query}'...")
    
    # A more specific query that is not restricted to a single site to find the best sources.
    query = f"tiyatro oyunları listesi {city} {date_query}"
    return search_tavily(query)

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
                
                # Programmatically extract the content from the search results.
                try:
                    search_results = json.loads(tool_result)
                    all_content = "\n\n".join([item.get('content', '') for item in search_results])
                    if not all_content.strip():
                        all_content = "No content found in search results."
                except json.JSONDecodeError:
                    all_content = tool_result # Pass raw result if not JSON

                final_messages = messages + [
                    assistant_message,
                    {"role": "tool", "tool_call_id": tool_call.id, "content": tool_result},
                    # Force the model to process the extracted content with a very direct and simple prompt.
                    {
                        "role": "user", 
                        #"content": f"From the following text, list the theater play names, venues, and times. Text: ###{all_content}###"
                        "content": f"""
Use the following text and the above tool result to output the theater play names, venues, times and the URL where the user can purchase the ticket. Make sure to list all the theater plays in your result. 
Here is the format you can use to present your result:
**Oyun adi**: <title>
  - Tarih ve saat: <date and time>
  - Mekan: <venue>
  - URL: <url>

Here it the text you should extract results from:
{all_content}"""
                    }
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
        {"role": "system", "content": "You are a helpful assistant who finds theater plays. Your goal is to provide a list of plays, including their names, venues, and times for a specific city and date. You will be given content from web search results. Your task is to carefully analyze this content, synthesize the information, and present a clean, formatted list of the plays to the user. Focus on extracting concrete details and ignore irrelevant information. If the content is messy, do your best to find the relevant information."},
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
