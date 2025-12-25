# src/prompting/zero_shot.py
import os
from litellm import completion
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def recommend_play(user_preference):
    """
    Recommends a play based on user preference using a zero-shot prompt with litellm.
    """

    
    # This is the zero-shot prompt. We provide the context and the task directly.
    prompt = f"""
    I want to watch a play and I'm in the mood for something {user_preference}.

    Based on my preference, which one play from the list should I watch?
    Respond with only the title of the play.
    """
    
    try:
        # As per the document, we use litellm to call the model.
        # Note: The model "gemini/gemini-2.5-flash" (from your list of available models) is used here.
        # You might need to change it based on your API key and provider.
        response = completion(
            # model="anthropic/claude-3-haiku-20240307",
            # model="gemini/gemini-2.5-flash",
            model="anthropic/claude-3-haiku-20240307",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert in theater and literature. Your task is to recommend a single play from a given list based on a user's mood."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Extract the content from the response
        recommendation = response.choices[0].message.content.strip()
        return recommendation

    except Exception as e:
        # Handle potential errors, like missing API keys
        return f"An error occurred: {e}. Please ensure your API key is set correctly."

if __name__ == "__main__":
    # Check if the API key is set.
    if not os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY") == "your_api_key":
        print("---")
        print("WARNING: The ANTHROPIC_API_KEY is not set in your .env file.")
        print("Please add your API key to the .env file before running the script.")
        print("---\n")

    user_input = input("What kind of play are you in the mood for? (e.g., 'a serious tragedy', 'a light-hearted comedy', 'something dramatic') ")
    
    # Add input validation to handle empty input
    if not user_input.strip():
        print("\nNo preference entered. Please run the script again and tell me what you're in the mood for.")
    else:
        recommendation = recommend_play(user_input)
        print(f"\nBased on your preference, I recommend: {recommendation}")
