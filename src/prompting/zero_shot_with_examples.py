# src/prompting/zero_shot_with_examples.py
import os
from litellm import completion
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def recommend_play_few_shot(user_preference):
    """
    Recommends a play based on user preference using a few-shot prompt with litellm.
    """
    
    # This is the few-shot prompt. We provide examples to guide the model.
    prompt = f"""
        You are an expert in theater and literature.
        
        Here are a few examples:
        ---
        User preference: "I want to see a classic tragedy."
        Recommendation: Hamlet
        ---
        User preference: "I'm in the mood for a light-hearted comedy."
        Recommendation: A Midsummer Night's Dream
        ---
        
        Now recommend a play for:
        User preference: "{user_preference}"
        Recommendation:
    """
    
    try:
        # We use the same model as before.
        response = completion(
            # model="anthropic/claude-3-haiku-20240307",
            model="gemini/gemini-2.5-flash",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2
        )
        
        # Extract the content from the response
        recommendation = response.choices[0].message.content.strip()
        return recommendation

    except Exception as e:
        # Handle potential errors
        return f"An error occurred: {e}. Please ensure your API key is set correctly."

if __name__ == "__main__":
    # Check if the API key is set.
    if not os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY") == "your_api_key":
        print("---")
        print("WARNING: The GEMINI_API_KEY is not set in your .env file.")
        print("Please add your API key to the .env file before running the script.")
        print("---\n")

    user_input = input("What kind of play are you in the mood for? (e.g., 'a serious tragedy', 'a light-hearted comedy', 'something dramatic') ")
    
    # Add input validation to handle empty input
    if not user_input.strip():
        print("\nNo preference entered. Please run the script again and tell me what you're in the mood for.")
    else:
        recommendation = recommend_play_few_shot(user_input)
        print(f"\nBased on your preference, I recommend: {recommendation}")