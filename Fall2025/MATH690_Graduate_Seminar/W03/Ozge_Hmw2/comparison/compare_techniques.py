from litellm import completion
from dotenv import load_dotenv
import os
import time

load_dotenv()

def test_technique(technique_name, system_prompt, user_prompt, problem):
    """Bir prompting tekniğini test et"""
    start_time = time.time()
    
    try:
        resp = completion(
            model="anthropic/claude-3-5-haiku-latest",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt.format(problem=problem)}
            ],
            temperature=0.1,
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        
        elapsed_time = time.time() - start_time
        answer = resp["choices"][0]["message"]["content"]
        
        return {
            "success": True,
            "answer": answer,
            "time": elapsed_time,
            "tokens_approx": len(answer.split())
        }
    
    except Exception as e:
        return {
            "success": False,
            "answer": f"Hata: {str(e)}",
            "time": 0,
            "tokens_approx": 0
        }

def compare_all_techniques():
    """Tüm teknikleri karşılaştır"""
    
    problem = "Bir bakkalda 3 kg elma 60 TL. 8 kg elma alırsam toplam ne kadar öderim?"
    
    techniques = {
        "Zero-Shot": {
            "system": "You are a helpful math assistant.",
            "user": "Solve this problem: {problem}"
        },
        "Few-Shot": {
            "system": """You are a math assistant.

            Example 1:
            Problem: 15 kalem 3 öğrenciye eşit dağıtılıyor. Her öğrenciye kaç kalem düşer?
            Solution: 15 ÷ 3 = 5 kalem

            Example 2:
            Problem: 2 kg domates 24 TL. 5 kg domates kaç TL?
            Solution: 24 ÷ 2 = 12 TL/kg, 12 × 5 = 60 TL

            Now solve:""",
                        "user": "{problem}"
                    },
        "Chain-of-Thought": {
            "system": """You are a math tutor. Think step by step:
                                    1. Understand the problem
                                    1.1 List given data
                                    2. Identify needed operations
                                    3. Calculate
                                    4. Verify answer
                                    5. Conclude""",
            "user": "Think step by step and solve: {problem}"
        },
        "Tool-Calling": {
            "system": """You are a math assistant. Use the calculator tool when needed.""",
            "user": """Solve the problem: {problem}
                                    If you need to do calculations, use the tool like this:
                                    [CALCULATE: expression]
                                    Then continue with your solution."""    
                         }
        }
    
    print("=" * 80)
    print("TEKNİK KARŞILAŞTIRMA - MATH PROBLEM")
    print("=" * 80)
    print(f"\nProblem: {problem}\n")
    
    results = {}
    
    for technique, prompts in techniques.items():
        print(f"\n{'='*80}")
        print(f"Testing: {technique}")
        print('='*80)
        
        result = test_technique(
            technique,
            prompts["system"],
            prompts["user"],
            problem
        )
        
        results[technique] = result
        
        if result["success"]:
            print(f"\n📝 Answer:\n{result['answer']}")
            print(f"\n⏱️  Time: {result['time']:.2f} seconds")
            print(f"📊 Approximate tokens: {result['tokens_approx']}")
        else:
            print(f"\n❌ {result['answer']}")
    
    # Summary Table
    print("\n" + "=" * 80)
    print("SUMMARY TABLE")
    print("=" * 80)
    print(f"{'Technique':<20} {'Time (s)':<12} {'Tokens':<10} {'Status':<10}")
    print("-" * 80)
    
    for technique, result in results.items():
        status = "✅ Success" if result["success"] else "❌ Failed"
        print(f"{technique:<20} {result['time']:<12.2f} {result['tokens_approx']:<10} {status:<10}")
    
    # Analysis
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    
    if all(r["success"] for r in results.values()):
        fastest = min(results.items(), key=lambda x: x[1]["time"])
        most_detailed = max(results.items(), key=lambda x: x[1]["tokens_approx"])
        
        print(f"\n🏆 En Hızlı: {fastest[0]} ({fastest[1]['time']:.2f}s)")
        print(f"📚 En Detaylı: {most_detailed[0]} ({most_detailed[1]['tokens_approx']} tokens)")
        
        print("\n💡 Observations:")
        print("   - Zero-Shot: En basit, hızlı ama bazen yeterince detaylı değil")
        print("   - Few-Shot: Örneklerle öğrenme, daha tutarlı sonuçlar")
        print("   - Chain-of-Thought: En detaylı, adım adım açıklama, ama daha yavaş")
        print("   - Tool-Calling: Hesaplama gerektiren problemler için ideal, doğru sonuçlar")

if __name__ == "__main__":
    compare_all_techniques()