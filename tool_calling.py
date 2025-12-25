import os
import re
from litellm import completion
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
import qrcode
from qrcode.image.styledpil import StyledPilImage

# Load environment variables from .env file
load_dotenv()

# --- Tool Definition ---
# In a real application, this could be a database or an external API call.
PLAY_SUMMARIES = {
        "Hamlet": "A young prince of Denmark who plots revenge against his uncle for murdering his father.",
        "A Midsummer Night's Dream": "A comedy involving four young Athenian lovers and a group of amateur actors who are manipulated by fairies in a forest.",
        "The Importance of Being Earnest": "A satirical comedy of manners in which two bachelors create alter egos to escape their tiresome lives.",
        "Death of a Salesman": "A tragedy about the failing American dream, following the last days of a washed-up salesman.",
        "A Streetcar Named Desire": "A drama about the fragile Blanche DuBois who moves in with her sister and brutish brother-in-law in New Orleans.",
        "L'Avare":  "A French comedy about a miserly man whose obsession with wealth leads to humorous situations.",
        "Othello": "A tragedy about jealousy and betrayal, focusing on the Moorish general Othello and his deceitful ensign Iago.",
        "The Cherry Orchard": "A play about an aristocratic Russian family that loses its estate, symbolizing the end of an era.",    
        "Waiting for Godot": "A tragicomedy about two    men waiting for someone named Godot, exploring themes of existentialism.",
        "The Glass Menagerie": "A memory play about a struggling family, focusing on the fragile relationship between a mother and her children.",
        "Romeo and Juliet": "A classic tragedy about two young star-crossed lovers whose deaths ultimately reconcile their feuding families.",
        "King Lear": "A tragedy about an aging king who divides his kingdom among his daughters, leading to betrayal and madness.",
        "The Crucible": "A dramatization of the Salem witch trials, exploring themes of hysteria, accusation, and integrity.",
        "Antigone": "A tragedy about the conflict between individual conscience and state law, focusing on Antigone's defiance of King Creon.",
        "The Tempest": "A play about magic, betrayal, and forgiveness, centered on the sorcerer Prospero and his daughter Miranda.",
        "A Doll's House": "A drama about a woman's struggle for independence within a constricting marriage.",
        "Tartuffe": "A comedy that satirizes religious hypocrisy through the character of Tartuffe, a conman posing as a pious man.",
        "The Seagull": "A play exploring unrequited love and the clash between artistic ambition and reality.",
        "The Taming of the Shrew": "A comedy about the courtship of the headstrong Katherina by Petruchio.",
        "Toz": "A Turkish play that delves into social issues and personal struggles.",
        "Arzu Tramvayi": "A Turkish comedy about love and misunderstandings on a tram.",
        "The New Tenant": "A Turkish play that explores themes of change and adaptation in a new living situation.",
       "War and Peace": "An epic novel adapted for the stage, exploring the lives of Russian aristocrats during the Napoleonic Wars.",
       "Yasamak mi Yoksa Olmek mi?": "They struggle to regain their independence, disregarding their lives.",
       "Gözlerimi Kaparım Vazifemi Yaparım": "A Turkish drama-comedy about a man who blindly follows orders without questioning them."
       }

"""Tool to get play summary."""
def get_play_summary(play_title: str) -> str:
    """
    Retrieves a brief summary of a given play.
    This is our 'tool' that the LLM can call.
    """
    return PLAY_SUMMARIES.get(play_title, "No summary available for this play.")

# --- Agent Logic ---

"""Tool to recommend a play using LLM with tool calling capability."""
def recommend_play_with_tools(user_preference):
    """
    Recommends a play by allowing the LLM to call tools for more information.
    """
    plays = list(PLAY_SUMMARIES.keys())
    
    # 1. Initial prompt with tool definition
    prompt = f"""
    You are an expert in theater and literature. Your task is to recommend a single play from a list.

    # Tools
    You have access to the following tool:
    - get_play_summary(play_title): Retrieves a brief summary of a play.

    # Instructions
    1. Analyze the user's preference.
    2. If you are unsure which play fits best, use the `get_play_summary` tool to learn more about a play.
    3. To use a tool, respond with a <tool_call> block, like this:
       <tool_call>get_play_summary("Hamlet")</tool_call>
    4. After receiving the tool's output, provide a final recommendation.
    5. If you are confident enough to make a recommendation without using a tool, just provide the play's title.

    # User Query
    User preference: "{user_preference}"
    Available plays: {', '.join(plays)}
    """

    try:
        # 2. First call to the LLM
        response = completion(
            # model="anthropic/claude-3-5-sonnet-20241022",
            model="gemini/gemini-2.5-flash",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        first_response_text = response.choices[0].message.content.strip()

        # 3. Check if the LLM wants to call a tool
        tool_call_match = re.search(r"<tool_call>(.*)</tool_call>", first_response_text)

        if tool_call_match:
            tool_call_str = tool_call_match.group(1).strip()
            print(f"--- LLM decided to call a tool: {tool_call_str} ---")
            
            # Execute the tool (with basic parsing)
            try:
                play_title_match = re.search(r'"(.*?)"', tool_call_str)
                if "get_play_summary" in tool_call_str and play_title_match:
                    play_title = play_title_match.group(1)
                    summary = get_play_summary(play_title)
                    tool_result = f"Summary for {play_title}: {summary}"
                else:
                    tool_result = "Could not parse the tool call."
            except Exception as e:
                tool_result = f"Error executing tool: {e}"

            print(f"--- Tool Result: {tool_result} ---\n")

            # 4. Second call to the LLM with the tool's result
            second_prompt = f"""
            {prompt}

            I have used the tool as you requested. Here is the result:
            {tool_result}

            Based on this new information, please provide your final recommendation. Respond with only the title of the play.
            """
            
            second_response = completion(
                # model="anthropic/claude-3-haiku-20240307",
                model="gemini/gemini-2.5-flash",
                messages=[{"role": "user", "content": second_prompt}],
                temperature=0.2
            )
            final_recommendation = second_response.choices[0].message.content.strip()
            return f"After getting more information, the final recommendation is: {final_recommendation}"
        else:
            # The LLM made a recommendation without using a tool
            return f"The agent made a direct recommendation: {first_response_text}"

    except Exception as e:
        return f"An error occurred: {e}"
    

"""Tool to get current time in a specified timezone."""
def get_current_time(timezone):
    """
     Returns the current time in the specified timezone.
    """
    timezone=ZoneInfo(timezone)
    return datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")





def get_weather_from_ip():
    """
    Gets the current, high, and low temperature in Fahrenheit for the user's
    location and returns it to the user.
    """
    # Get location coordinates from the IP address
    lat, lon = requests.get('https://ipinfo.io/json').json()['loc'].split(',')

    # Set parameters for the weather API call
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m",
        "daily": "temperature_2m_max,temperature_2m_min",
        "temperature_unit": "fahrenheit",
        "timezone": "auto"
    }

    # Get weather data
    weather_data = requests.get("https://api.open-meteo.com/v1/forecast", params=params).json()

    # Format and return the simplified string
    return (
        f"Current: {weather_data['current']['temperature_2m']}°F, "
        f"High: {weather_data['daily']['temperature_2m_max'][0]}°F, "
        f"Low: {weather_data['daily']['temperature_2m_min'][0]}°F"
    )

# Write a text file
def write_txt_file(file_path: str, content: str):
    """
    Write a string into a .txt file (overwrites if exists).
    Args:
        file_path (str): Destination path.
        content (str): Text to write.
    Returns:
        str: Path to the written file.
    """
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return file_path


# Create a QR code
def generate_qr_code(data: str, filename: str, image_path: str):
    """Generate a QR code image given data and an image path.

    Args:
        data: Text or URL to encode
        filename: Name for the output PNG file (without extension)
        image_path: Path to the image to be used in the QR code
    """
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(data)

    img = qr.make_image(image_factory=StyledPilImage, embedded_image_path=image_path)
    output_file = f"{filename}.png"
    img.save(output_file)

    return f"QR code saved as {output_file} containing: {data[:50]}..."




if __name__ == "__main__":
    user_input = input("What kind of play are you in the mood for? ")
    
    if not user_input.strip():
        print("\nNo preference entered.")
    else:
        recommendation = recommend_play_with_tools(user_input)
        summary = get_play_summary(recommendation.split(":")[-1].strip())
        print(f"\n{recommendation}")
        print(f"\n and its summary is: {summary}")
        print(f"\nCurrent time in UTC: {get_current_time('Pacific/Auckland')}")
        print(f"\nCurrent weather based on your IP: {get_weather_from_ip()}")
        print(write_txt_file("play_recommendation.txt", f"{recommendation}\n\nSummary: {summary}")) 
        print(generate_qr_code(f"{recommendation}\n\nSummary: {summary}", "play_recommendation_qr", "screenshots/theater_mask.png"))    
