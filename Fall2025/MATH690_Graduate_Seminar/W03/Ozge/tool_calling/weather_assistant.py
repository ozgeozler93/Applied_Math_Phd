# Math690_GraduateSeminar/W03/Odev1/gsu_llm_odev/tool_calling/weather_assistant.py
from litellm import completion
from dotenv import load_dotenv
import os
import requests
import re
import json

load_dotenv()
print(f"API Key loaded: {os.getenv('OPENWEATHER_API_KEY')}")  # Debug


PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "gemini/gemini-1.5-flash")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "claude-3-5-haiku-20241022")

# def smart_completion(messages, temperature):
#     """
#     Önce Gemini dene, kota doluysa Claude kullan
#     """
#     try:
#         return completion(
#             model=PRIMARY_MODEL,
#             messages=messages,
#             temperature=temperature,
#             api_key=os.getenv("GEMINI_API_KEY")
#         )
#     except Exception as e:
#         if "429" in str(e) or "quota" in str(e).lower():
#             print("⚠️  Gemini kotası doldu, Claude'a geçiliyor...")
#             return completion(
#                 model=FALLBACK_MODEL,
#                 messages=messages,
#                 temperature=temperature,
#                 api_key=os.getenv("ANTHROPIC_API_KEY")
#             )
#         else:
#             raise e



# def get_weather_real(city):
#     """
#     Gerçek OpenWeatherMap API kullanarak hava durumu al
#     """
#     api_key = os.getenv("WEATHERAPI_KEY")
#     base_url = "http://api.weatherapi.com/v1/current.json"
    
#     params = {
#         "q": city,
#         "appid": api_key,
#         "units": "metric",  # Celsius için
#         "lang": "tr"        # Türkçe açıklama için
#     }
    
#     try:
#         response = requests.get(base_url, params=params)
#         response.raise_for_status()
#         data = response.json()
        
#         # API'den gelen verileri parse et
#         temp = data["main"]["temp"]
#         condition = data["weather"][0]["description"]
#         humidity = data["main"]["humidity"]
#         wind = data["wind"]["speed"]
        
#         return f"Şu anda {city}'da {temp}°C, {condition}, Nem: {humidity}%, Rüzgar: {wind} m/s"
    
#     except requests.exceptions.HTTPError as e:
#         if e.response.status_code == 404:
#             return f"{city} için hava durumu bilgisi bulunamadı."
#         else:
#             return f"API hatası: {str(e)}"
#     except Exception as e:
#         return f"Hata: {str(e)}"

# def get_forecast(city, days):
#     """Mock forecast API"""
#     forecasts = {
#         "Istanbul": "(Mockdata) Önümüzdeki günlerde sıcaklıklar 12-18°C arasında, parçalı bulutlu",
#         "Ankara": "(Mockdata) Hafta boyunca güneşli, gece sıcaklıkları 2-5°C civarında",
#         "İzmir": "(Mockdata) Yağışlı geçecek, 15-20°C arası sıcaklıklar bekleniyor",
#         "Antalya": "(Mockdata) Güneşli ve ılık, 20-25°C arası sıcaklıklar"
#     }
    
#     forecast = forecasts.get(city, "Tahmin bilgisi bulunamadı")
#     return f"{city} için {days} günlük tahmin: {forecast}"



def get_forecast_hybrid(city, days):
    """
    Önce gerçek API dene, başarısız olursa mock data kullan
    """
    # Önce real API dene
    real_result = get_forecast_weatherapi(city, days)
    
    # Eğer hata mesajı yoksa, real sonucu döndür
    if "alınamadı" not in real_result and "bulunamadı" not in real_result:
        return real_result
    
    # Real API başarısız olduysa, mock data'ya bak
    forecasts = {
        "Istanbul": "(Mockdata)günlerde sıcaklıklar 12-18°C arasında, parçalı bulutlu",
        "Ankara": "(Mockdata) Hafta boyunca güneşli, gece sıcaklıkları 2-5°C civarında",
        "İzmir": "(Mockdata) Yağışlı geçecek, 15-20°C arası sıcaklıklar bekleniyor",
        "Antalya": "(Mockdata) Güneşli ve ılık, 20-25°C arası sıcaklıklar",
        "Adana": "(Mockdata) Sıcak ve güneşli, sıcaklıklar 25-30°C arasında",
        "Mersin": "(Mockdata) Güneşli ve ılıman, 22-28°C arası sıcaklıklar",
        "Paris": "(Mockdata) Hafta boyunca yağmurlu, 10-15°C arası",
        "Bali": "(Mockdata) Tropik sıcak, 27-32°C arası, yüksek nem"
    }
    
    forecast = forecasts.get(city, "Tahmin bilgisi bulunamadı")
    return f"{city} için {days} günlük tahmin: (Mockdata) {forecast}"


def get_forecast_weatherapi(city, days):
    """
    WeatherAPI.com kullanarak gerçek hava tahmini
    """
    api_key = os.getenv("WEATHERAPI_KEY")
    
    if not api_key:
        return f"HATA: WEATHERAPI_KEY bulunamadı"
    
    base_url = "http://api.weatherapi.com/v1/forecast.json"
    
    params = {
        "key": api_key,
        "q": city,
        "days": min(days, 10),  # WeatherAPI free tier: max 10 gün
        "lang": "tr"
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # Tahmin verilerini analiz et
        forecast_days = data["forecast"]["forecastday"]
        min_temp = min([day["day"]["mintemp_c"] for day in forecast_days])
        max_temp = max([day["day"]["maxtemp_c"] for day in forecast_days])
        
        # En yaygın hava durumu
        conditions = [day["day"]["condition"]["text"] for day in forecast_days]
        most_common = max(set(conditions), key=conditions.count)
        
        return f"{city} için {days} günlük tahmin: {most_common}, sıcaklıklar {min_temp:.1f}-{max_temp:.1f}°C arasında"
    
    except Exception as e:
        return f"{city} için tahmin alınamadı: {str(e)}"



# execute_tool'da kullan:
def execute_tool(tool_name, **kwargs):
    if tool_name == "get_weather":
        return get_weather_weatherapi(kwargs.get("city", ""))
    elif tool_name == "get_forecast":
        return get_forecast_hybrid(kwargs.get("city", ""), kwargs.get("days", 3))
    else:
        return f"Bilinmeyen tool: {tool_name}"

def get_weather_weatherapi(city):
    """
    WeatherAPI.com - Daha hızlı aktivasyon
    """
    api_key = os.getenv("WEATHERAPI_KEY")
    base_url = "http://api.weatherapi.com/v1/current.json"
    
    params = {
        "key": api_key,
        "q": city,
        "lang": "tr"
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        temp = data["current"]["temp_c"]
        condition = data["current"]["condition"]["text"]
        humidity = data["current"]["humidity"]
        wind = data["current"]["wind_kph"]
        
        return f"Şu anda {city}'da {temp}°C, {condition}, Nem: {humidity}%, Rüzgar: {wind} km/h"
    
    except Exception as e:
        return f"{city} için bilgi alınamadı: {str(e)}"

# def get_forecast_real(city, days):
#     """
#     Gerçek OpenWeatherMap Forecast API
#     """
#     api_key = os.getenv("OPENWEATHER_API_KEY")
#     base_url = "http://api.openweathermap.org/data/2.5/forecast"
    
#     params = {
#         "q": city,
#         "appid": api_key,
#         "units": "metric",
#         "lang": "tr",
#         "cnt": days * 8  # Her 3 saatte bir veri, günde 8 veri
#     }
    
#     try:
#         response = requests.get(base_url, params=params)
#         response.raise_for_status()
#         data = response.json()
        
#         # İlk ve son günün sıcaklıklarını al
#         temps = [item["main"]["temp"] for item in data["list"]]
#         min_temp = min(temps)
#         max_temp = max(temps)
        
#         # En yaygın hava durumu
#         conditions = [item["weather"][0]["description"] for item in data["list"]]
#         most_common = max(set(conditions), key=conditions.count)
        
#         return f"{city} için {days} günlük tahmin: {most_common}, sıcaklıklar {min_temp:.1f}-{max_temp:.1f}°C arasında"
    
#     except Exception as e:
#         return f"Tahmin bilgisi alınamadı: {str(e)}"



def weather_assistant(user_query):
    """
    Tool Calling: LLM hangi tool'u kullanacağına karar versin
    """
    try:
        resp = completion(
            model="gemini-1.5-flash",
            messages=[
                {
                    "role": "system",
                    "content": """You are a weather assistant with access to tools.

                    # Available Tools:
                    1. get_weather(city): Get current weather for a city
                    - Returns: temperature, condition, humidity, wind
                    
                    2. get_forecast(city, days): Get weather forecast for N days
                    - Parameters: city (string), days (integer)
                    - Returns: forecast information

                    # Instructions:
                    1. Analyze user's question
                    1.1 List given data
                    2. Decide which tool(s) to use
                    3. Output tool calls in <tool_call> tags with JSON format
                    4. Provide reasoning in <reasoning> tags
                    5. Give final answer in <answer> tags

                    # Format:
                    <tool_call>
                    {
                    "tool": "tool_name",
                    "parameters": {"param1": "value1", "param2": "value2"}
                    }
                    </tool_call>

                    <reasoning>
                    [Your thinking process]
                    </reasoning>

                    <answer>
                    [Final answer to user]
                    </answer>

                    # Example:
                    User: "Istanbul'da hava nasıl?"

                    <tool_call>
                    {
                    "tool": "get_weather",
                    "parameters": {"city": "Istanbul"}
                    }
                    </tool_call>

                    <reasoning>
                    Kullanıcı Istanbul'un şu anki hava durumunu sordu, bu yüzden get_weather tool'unu kullanmalıyım.
                    </reasoning>

                    <answer>
                    İstanbul'da şu anda 15°C, hava bulutlu. Nem oranı %70, rüzgar 15 km/h hızında esiyor.
                    </answer>"""
                },
                {
                    "role": "user",
                    "content": user_query
                }
            ],
            temperature=0.2,
            api_key=os.getenv("GEMINI_API_KEY")

        )
        
        response = resp["choices"][0]["message"]["content"]
        
        # Parse tool calls
        tool_call_matches = re.findall(r'<tool_call>(.*?)</tool_call>', response, re.DOTALL)
        
        tool_results = []
        for tool_call_str in tool_call_matches:
            try:
                # JSON parse et
                tool_call = json.loads(tool_call_str.strip())
                tool_name = tool_call.get("tool")
                parameters = tool_call.get("parameters", {})
                
                # Tool'u çalıştır
                result = execute_tool(tool_name, **parameters)
                tool_results.append({
                    "tool": tool_name,
                    "parameters": parameters,
                    "result": result
                })
            except json.JSONDecodeError:
                tool_results.append({"error": "Tool call parse edilemedi"})
        
        # Parse reasoning ve answer
        reasoning = re.search(r'<reasoning>(.*?)</reasoning>', response, re.DOTALL)
        answer = re.search(r'<answer>(.*?)</answer>', response, re.DOTALL)
        
        return {
            "tool_calls": tool_results,
            "reasoning": reasoning.group(1).strip() if reasoning else "",
            "answer": answer.group(1).strip() if answer else "",
            "full_response": response
        }
    
    except Exception as e:
        if "429" in str(e) or "quota" in str(e).lower():
            print("❌ Kota doldu!")
        else:
             print(f"❌ Başka hata: {str(e)}")
        return {
            "tool_calls": [],
            "reasoning": f"Hata: {str(e)}",
            "answer": "",
            "full_response": ""
        }




def weather_assistant2(user_query):
    """
    YENİ VERSİYON: İki aşamalı (tool sonucunu görüyor)
    """
    try:
        # ===== AŞAMA 1: Tool Call Generation =====
        resp1 = completion(
            model="claude-3-5-haiku-20241022",
            messages=[
                {
                    "role": "system",
                    "content": """You are a weather assistant with access to tools.

                    # Available Tools:
                    1. get_weather(city): Get current weather for a city
                    2. get_forecast(city, days): Get weather forecast for N days

                    # Instructions:
                    Output tool calls in JSON format inside <tool_call> tags.
                    If you need multiple cities, use multiple <tool_call> blocks.

                    Example:
                    <tool_call>
                    {"tool": "get_weather", "parameters": {"city": "Istanbul"}}
                    </tool_call>"""
                },
                {
                    "role": "user",
                    "content": user_query
                }
            ],
            temperature=0.2,
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        
        response1 = resp1["choices"][0]["message"]["content"]
        
        # Parse tool calls
        tool_call_matches = re.findall(r'<tool_call>(.*?)</tool_call>', response1, re.DOTALL)
        
        tool_results = []
        tool_outputs_text = ""
        
        for tool_call_str in tool_call_matches:
            try:
                tool_call = json.loads(tool_call_str.strip())
                tool_name = tool_call.get("tool")
                parameters = tool_call.get("parameters", {})
                
                # Tool'u çalıştır
                result = execute_tool(tool_name, **parameters)
                tool_results.append({
                    "tool": tool_name,
                    "parameters": parameters,
                    "result": result
                })
                
                # Sonuçları text olarak birleştir
                tool_outputs_text += f"\n• {tool_name}({parameters}): {result}\n"
                
            except json.JSONDecodeError:
                tool_results.append({"error": "Tool call parse edilemedi"})
        
        # ===== AŞAMA 2: Final Answer (Tool sonuçlarını kullanarak) =====
        resp2 = completion(
            model="claude-3-5-haiku-20241022",
            messages=[
                {
                    "role": "user",
                    "content": f"""Kullanıcı şunu sordu: "{user_query}"

                    Hava durumu araçlarını kullanarak şu sonuçları aldım:
                    {tool_outputs_text}

                    Şimdi bu sonuçlara dayanarak kullanıcıya Türkçe, detaylı ve doğal bir cevap ver.
                    Eğer birden fazla şehir karşılaştırılıyorsa, karşılaştırmalı bilgi ver."""
                }
            ],
            temperature=0.3,
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        
        final_answer = resp2["choices"][0]["message"]["content"]
        
        return {
            "tool_calls": tool_results,
            "reasoning": f"İki aşamalı işlem: {len(tool_results)} tool çağrıldı, sonuçlar final answer'a dahil edildi",
            "answer": final_answer,
            "full_response": response1
        }
    
    except Exception as e:
        return {
            "tool_calls": [],
            "reasoning": f"Hata: {str(e)}",
            "answer": "",
            "full_response": ""
        }


# Main kısmında ikisini de test et
if __name__ == "__main__":
    print("=" * 80)
    print("TOOL CALLING - WEATHER ASSISTANT TEST")
    print("=" * 80)
    
    queries = [
        "Istanbul'da hava nasıl?",
        "Paris'de hava nasıl?",
        "Bali'de hava durumu nedir?",
        "Adana ve Mersin'in onumuzdeki 5 gunluk hava durumunu karşılaştırir misin?",
        "Ankara'da önümüzdeki 5 gün hava durumu nasıl olacak?",
        "Izmir ve Antalya'nın şu anki hava durumunu karşılaştırir misin?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*80}")
        print(f"Query {i}: {query}")
        print('='*80)
        
        # # ESKİ VERSİYON
        # print("\n[OLD VERSION - Tek Aşamalı]")
        # result_old = weather_assistant(query)
        # print(f"Answer: {result_old['answer'][:100]}...")
        
        # YENİ VERSİYON
        print("\n[NEW VERSION - İki Aşamalı]")
        result_new = weather_assistant2(query)
        
        print("\n🔧 TOOL CALLS:")
        for tool_call in result_new["tool_calls"]:
            if "error" in tool_call:
                print(f"  ❌ {tool_call['error']}")
            else:
                print(f"  📞 {tool_call['tool']}({tool_call['parameters']})")
                print(f"     → {tool_call['result']}")
        
        print(f"\n✅ ANSWER:\n{result_new['answer']}")
        print("\n" + "-"*80)