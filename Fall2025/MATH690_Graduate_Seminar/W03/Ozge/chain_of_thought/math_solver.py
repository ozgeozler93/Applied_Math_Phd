from litellm import completion
from dotenv import load_dotenv
import os
import re

load_dotenv()

def solve_math_problem(problem):
    """
    Chain of Thought: Model adım adım düşünsün
    """
    try:
        resp = completion(
            # model="gemini/gemini-2.0-flash-exp",  # Kota doldu
            # model="gemini/gemini-1.5-flash",
            model="anthropic/claude-3-5-haiku-latest",  # ✅ DOĞRU MODEL
            # Alternatifler:
            # model="claude-3-5-sonnet-20241022"  # Daha güçlü ama pahalı
            # model="claude-3-haiku-20240307"     # Eski versiyon
            messages=[
                {
                    "role": "system",
                    "content": """You are a math tutor. Solve problems step by step using this format:

                    <reasoning>
                    Adım 1: [Problemi anla]
                    Adim 1.1: [Verilenleri listele]
                    Adım 2: [Hangi işlem gerekli?]
                    Adım 3: [Hesapla]
                    Adım 4: [Doğrula]
                    Adim 5: [Tebrikler! Sonuç bulundu.]
                    </reasoning>

                    <answer>
                    [Nihai cevap]
                    </answer>

                    Be detailed in your reasoning."""
                },
                {
                    "role": "user",
                    "content": f"Bu problemi adım adım çöz: {problem}"
                }
            ],
            temperature=0.1,
            api_key=os.getenv("ANTHROPIC_API_KEY")  # ✅ ANTHROPIC_API_KEY
        )
        
        response = resp["choices"][0]["message"]["content"]
        
        # Parse XML tags
        reasoning_match = re.search(r'<reasoning>(.*?)</reasoning>', response, re.DOTALL)
        answer_match = re.search(r'<answer>(.*?)</answer>', response, re.DOTALL)
        
        reasoning = reasoning_match.group(1).strip() if reasoning_match else "Reasoning bulunamadı"
        answer = answer_match.group(1).strip() if answer_match else "Answer bulunamadı"
        
        return {
            "reasoning": reasoning,
            "answer": answer,
            "full_response": response
        }
    
    except Exception as e:
        return {
            "reasoning": f"Hata: {str(e)}",
            "answer": "",
            "full_response": ""
        }

if __name__ == "__main__":
    print("=" * 60)
    print("CHAIN OF THOUGHT - MATH SOLVER TEST (Claude)")
    print("=" * 60)
    
    problems = [
        "Bir mağazada 3 tişört 240 TL. 7 tişört alırsam toplam ne kadar öderim?",
        "Ali'nin 150 TL'si var. Bir kitap 45 TL, bir defter 12 TL. 3 kitap ve 5 defter alırsa kaç TL kalır?",
        "Bir pastanede 48 kurabiye var. Bunlar 6 kutuya eşit dağıtılacak. Her kutuya kaç kurabiye konur?"
    ]
    
    for i, problem in enumerate(problems, 1):
        print(f"\n{'='*60}")
        print(f"Problem {i}: {problem}")
        print('='*60)
        
        result = solve_math_problem(problem)
        
        print("\n📝 REASONING (Model'in düşünme süreci):")
        print(result["reasoning"])
        
        print("\n✅ ANSWER (Nihai cevap):")
        print(result["answer"])
        
        print("\n" + "-"*60)