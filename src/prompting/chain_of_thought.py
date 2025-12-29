#  src/prompting/chain_of_thought.py
import os
from litellm import completion
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def recommend_play_cot(user_preference):
    """
    Recommends a play based on user preference using a Chain of Thought prompt.
    """
    plays = [
        "Hamlet", 
        "A Midsummer Night's Dream",
        "The Importance of Being Earnest",
        "Death of a Salesman", 
        "A Streetcar Named Desire", 
        "L'Avare", 
        "Othello",
        "The Cherry Orchard", 
        "Waiting for Godot", 
        "The Glass Menagerie",
        "Romeo and Juliet", 
        "King Lear", 
        "The Crucible", 
        "Antigone", 
        "The Tempest",
        "A Doll's House", 
        "Tartuffe",
        "The Seagull", 
        "The Taming of the Shrew",
        "Toz", 
        "Arzu Tramvayi", 
        "The New Tenant",
        "Yasamak mi Yoksa Olmek mi?"
    ]
    
    # This is the Chain of Thought prompt.
    prompt = f"""
    You are an expert in theater and literature. Your task is to recommend a single play from a given list based on a user's mood.

    First, show your reasoning by thinking step-by-step:
    1.  Analyze the user's preference: what themes, genres, or emotions are they looking for?
    2.  Briefly consider the themes of the available plays.
    3.  Based on your analysis, determine which play is the best fit.

    After your reasoning, provide the final answer on a new line in the format:
    Final Recommendation: [Play Title]

    User preference: "{user_preference}"
    """
    
    try:
        response = completion(
            # model="claude-3-5-sonnet-20241022",
            model="gemini/gemini-2.5-flash",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2
        )
        
        # The full response now contains both reasoning and the final answer.
        full_response = response.choices[0].message.content.strip()
        return full_response

    except Exception as e:
        return f"An error occurred: {e}. Please ensure your API key is set correctly."

if __name__ == "__main__":
    if not os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY") == "your_api_key":
        print("---")
        print("WARNING: The GEMINI_API_KEY is not set in your .env file.")
        print("---\n")

    user_input = input("What kind of play are you in the mood for? ")
    
    if not user_input.strip():
        print("\nNo preference entered. Please run the script again.")
    else:
        recommendation = recommend_play_cot(user_input)
        print(f"\nHere is the recommendation process:\n\n{recommendation}")
