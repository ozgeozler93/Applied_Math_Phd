# 🎭 StageAgent - AI Theater Recommendation System

**An intelligent conversational agent that recommends theater plays in Istanbul using advanced LLM prompting techniques, web scraping, and location-based filtering.**

*GSU Math Graduate Seminar - Fall 2025*  
*MATH690 - Applied Mathematics PhD Program*

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [LLM Prompting Techniques](#-llm-prompting-techniques)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Usage](#-usage)
- [Examples](#-examples)
- [Technical Details](#-technical-details)
- [Results](#-results)
- [Future Work](#-future-work)

---

## 🎯 Overview

StageAgent is an end-to-end AI system that demonstrates practical applications of:
- **Large Language Models (LLMs)** for natural language understanding
- **Well-known prompting techniques** (zero-shot, few-shot, chain-of-thought)
- **Multi-modal data integration** (web scraping, APIs, databases)
- **Conversational AI** with context memory and tool calling

**Problem Statement:** Theater-goers in Istanbul face difficulty finding plays that match their preferences, considering factors like genre, location, schedule, and personal taste.

**Solution:** An AI agent that understands natural language queries, filters plays by location and availability, and provides personalized recommendations using LLM-based scoring.

---

## 🌟 Features

### Core Capabilities
- **🤖 Agent 1: Conversational AI** - Multi-turn dialogue with context memory and orchestration
- **🧠 Agent 2: Intent Detection** - Classifies user queries (recommend/info/search/preference/calendar)
- **📝 Agent 3: Preference Extraction** - Understands implicit preferences and semantic matching
- **🗄️ Agent 4: Data Retrieval** - SQLite database with structured plays, showtimes, venues, cities
- **🎯 Agent 5: Smart Recommendations** - LLM evaluates user-play compatibility (0-10 scale)
- **🗓️ Agent 7: Calendar Integration** - Google Calendar connection with smart event detection

### Planned Extensions

- **Agent 6: YouTube Search** - Automated trailer/review integration
- **Agent 8: Personalization** - Learn from user ratings (few-shot learning)
- **Agent 9: Multi-Language** - English ↔ Turkish translation support


### Data & Tools

- **🕷️ Automated Web Scraping** - Real-time data from biletinial.com
- **📍 Location-Based Filtering** - Google Maps Distance Matrix API integration
- **🏙️ Multi-City Support** - Istanbul and Ankara with smart city detection
- **🎬 YouTube Integration** - Trailer/review search (implemented, ready to use)

---

# 🧠 LLM Prompting Techniques - UPDATED WITH REAL CODE

## Overview

This project implements three advanced prompting strategies, tested with real Turkish theater data and actual terminal outputs shown below.

---

## 1️⃣ Zero-Shot Prompting

### Definition
Asking the LLM to perform a task **without** providing examples - only direct instructions.

### Implementation

**File:** `src/prompting/zero_shot.py`

```python
def recommend_play(user_preference):
    """
    Zero-shot recommendation - no examples, just direct task
    """
    prompt = f"""
    I want to watch a play and I'm in the mood for something {user_preference}.
    Based on my preference, which one play from the list should I watch?
    Respond with only the title of the play.
    """
    
    response = completion(
        model="gemini/gemini-2.5-flash",
        messages=[
            {
                "role": "system",
                "content": "You are an expert in theater and literature."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    return response.choices[0].message.content.strip()
```

### Real Terminal Outputs

```bash
$ cd src/prompting
$ python zero_shot.py

# Test 1: English query, lighthearted comedy
What kind of play are you in the mood for? I want something light-hearted and funny
Based on your preference, I recommend: The Importance of Being Earnest

# Test 2: Turkish actor - single name
What kind of play are you in the mood for? I want something with Nezaket Erden
Based on your preference, I recommend: Sen İstanbul'dan Daha Güzelsin

# Test 3: Multiple constraints - actor + author
What kind of play are you in the mood for? I want something with Nezaket Erden and Latife Tekin
Based on your preference, I recommend: Sürükleyici

# Test 4: Same query, different run (shows stochasticity)
What kind of play are you in the mood for? I want something with Nezaket Erden and Latife Tekin
Based on your preference, I recommend: Sevgili Arsız Ölüm - Dirmit
```

### Key Observations

✅ **Strengths:**
- Understands Turkish theater context (Nezaket Erden, Latife Tekin)
- Works across languages (English query → Turkish play)
- Fast response (~1-2 seconds)
- No training data needed

⚠️ **Limitations:**
- Stochastic - same query can give different answers
- No memory of previous interactions
- Cannot learn from feedback

---
## 1️⃣. 1️⃣. Zero-Shot with Examples (Hybrid)


### Definition
Providing **examples** to guide LLM behavior, but **NO constrained list** of plays.

### Implementation

**File:** `src/prompting/zero_shot_with_examples.py`

```python
def recommend_play_few_shot(user_preference):
    """
    Hybrid approach: Examples guide style, but no play list constraint
    """
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
    
    response = completion(
        model="gemini/gemini-2.5-flash",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    
    return response.choices[0].message.content.strip()
```

### Real Terminal Output

```bash
$ python zero_shot_with_examples.py

What kind of play are you in the mood for? (e.g., 'a serious tragedy', 'a light-hearted comedy', 'something dramatic') turkish and romantic
Based on your preference, I recommend: Recommendation: Legend of Love (Ferhat ile Şirin)


What kind of play are you in the mood for? (e.g., 'a serious tragedy', 'a light-hearted comedy', 'something dramatic') turkish and dark-comedy
Based on your preference, I recommend: Recommendation: Yaşar Ne Yaşar Ne Yaşamaz (Yaşar Neither Lives Nor Dies) by Aziz Nesin

```

### Characteristics
- ✅ Examples guide output format
- ✅ More consistent than pure zero-shot
- ⚠️ Still no constraint on available plays
- 🎯 Best for: Open-ended recommendations from all plays

### Why "Zero-Shot with Examples"?
This is technically **not pure few-shot** because:
- ❌ No "available plays" list to choose from
- ✅ Examples only show the FORMAT, not the selection logic
- 📚 Some researchers call this "few-shot prompting"
- 🎓 Others call it "zero-shot with demonstrations"



---

## 2️⃣ Few-Shot Prompting

### Definition
Providing 2-5 **examples** to guide the LLM's behavior and output format.

### Implementation

**File:** `src/prompting/few_shot.py`

```python
def recommend_play_few_shot(user_preference):
    """
    Few-shot with examples to guide LLM behavior
    """
    plays = [
        "Hamlet", "A Midsummer Night's Dream", 
        "Death of a Salesman", "Toz", "Arzu Tramvayi",
        # ... more plays
    ]
    
    prompt = f"""
    You are an expert in theater. Recommend a play based on examples:
    
    --- EXAMPLES ---
    User: "I want to see a classic tragedy."
    Plays: Hamlet, A Midsummer Night's Dream, The Importance of Being Earnest
    Recommendation: Hamlet
    
    User: "I'm in the mood for a light-hearted comedy."
    Plays: Death of a Salesman, A Streetcar Named Desire, A Midsummer Night's Dream  
    Recommendation: A Midsummer Night's Dream
    --- END EXAMPLES ---
    
    Now recommend:
    User: "{user_preference}"
    Available plays: {', '.join(plays)}
    Recommendation:
    """
    
    response = completion(
        model="gemini/gemini-2.5-flash",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2  # Lower temp for consistency
    )
    
    return response.choices[0].message.content.strip()
```

### Real Terminal Outputs

```bash
$ python few_shot.py

# Test 1: Single actor constraint
What kind of play are you in the mood for? I want something with Nezaket Erden
Based on your preference, I recommend: Toz

# Test 2: Two constraints (repeated 3 times - same answer!)
What kind of play are you in the mood for? I want something with Nezaket Erden and Latife Tekin
Based on your preference, I recommend: Toz

What kind of play are you in the mood for? I want something with Nezaket Erden and Latife Tekin
Based on your preference, I recommend: Toz

What kind of play are you in the mood for? I want something with Nezaket Erden and Latife Tekin  
Based on your preference, I recommend: Toz
```

### Key Observations

✅ **Strengths:**
- **Consistent outputs** - same query → same answer (temperature=0.2)
- Learns from examples (format, reasoning style)
- Better pattern matching than zero-shot
- Combines actor knowledge with available plays

⚠️ **Limitations:**
- Needs carefully chosen examples
- Examples take up context window
- May overfit to example patterns

### Comparison: Zero-Shot vs Few-Shot

| Query | Zero-Shot | Few-Shot |
|-------|-----------|----------|
| "Nezaket Erden + Latife Tekin" | Sürükleyici (run 1) | **Toz (consistent)** |
| "Nezaket Erden + Latife Tekin" | Sevgili Arsız Ölüm (run 2) | **Toz (consistent)** |
| "Nezaket Erden + Latife Tekin" | ? (run 3) | **Toz (consistent)** |

**Winner:** Few-shot for **consistency**



---

## 3️⃣ Chain-of-Thought (CoT) Prompting

### Definition
Asking the LLM to **"think step by step"** before providing the final answer - explicit reasoning.

### Implementation

**File:** `src/prompting/chain_of_thought.py`

```python
def recommend_play_cot(user_preference):
    """
    Chain-of-Thought: Show reasoning process
    """
    plays = ["Hamlet", "Toz", "Arzu Tramvayi", ...]  # List of plays
    
    prompt = f"""
    You are a theater expert. Think step-by-step:
    
    1. Analyze the user's preference: themes, genres, emotions?
    2. Consider the themes of available plays
    3. Determine the best fit
    
    After reasoning, provide:
    Final Recommendation: [Play Title]
    
    User preference: "{user_preference}"
    """
    
    response = completion(
        model="gemini/gemini-2.5-flash",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    
    # Returns BOTH reasoning AND final answer
    return response.choices[0].message.content.strip()
```

### Real Terminal Outputs

**Test 1: Single actor query**

```bash
$ python chain_of_thought.py
What kind of play are you in the mood for? I want something with Nezaket Erden

Here is the recommendation process:

1. **Analyze the user's preference:** 
   The user's preference is highly specific: "I want something with Nezaket Erden." 
   This is not a mood or genre, but a direct request for a play featuring this 
   particular actress.

2. **Briefly consider the themes of the available plays:** 
   No list was provided. I will select a notable work Nezaket Erden has been 
   involved in. She is known for powerful performances in critically acclaimed 
   productions. One significant play is "Tırnak İçinde Hizmetçiler" (Maids in 
   Quotation Marks), an adaptation of Jean Genet's "The Maids."

3. **Determine the best fit:** 
   "Tırnak İçinde Hizmetçiler" directly addresses the user's preference for the 
   actress.

Final Recommendation: Tırnak İçinde Hizmetçiler
```

**Test 2: Multi-constraint query**

```bash
What kind of play are you in the mood for? I want something with Nezaket Erden and Latife Tekin

Here is the recommendation process:

1. **Analyze the user's preference:** 
   The user wants a play involving BOTH Nezaket Erden and Latife Tekin. This 
   indicates a play where Nezaket Erden performed, and which is either written by 
   Latife Tekin or is an adaptation of her work.

2. **Consider the themes:** 
   The most famous theatrical work bringing these two together is the adaptation 
   of Latife Tekin's novel "Sevgili Arsız Ölüm" (Dear Shameless Death). Nezaket 
   Erden is recognized for her powerful one-woman performance as Dirmit. The play 
   explores magical realism, rural life, migration, family struggles, and a young 
   woman's journey against societal pressures.

3. **Determine the best fit:** 
   "Sevgili Arsız Ölüm - Dirmit" directly involves both: it's an adaptation of 
   Latife Tekin's novel, and Nezaket Erden is the lead actress.

Final Recommendation: Sevgili Arsız Ölüm - Dirmit
```

**Test 3: Complex interpretive query**

```bash
What kind of play are you in the mood for? I want a play with a Turkish woman having Cannes Award

Here is the recommendation process:

1. **Analyze the user's preference:**
   - "Turkish woman": Desire for Turkish female character/playwright/setting
   - "Cannes Award": CHALLENGING - Cannes Awards are for FILM, not theater!
   - Must interpret as: desire for a character with significant international 
     artistic recognition

2. **Consider available plays:**
   No specific list provided. I must find a play featuring a strong, recognized 
   Turkish female figure in the arts. The challenge is bridging "theater" and 
   "Cannes Award" (film).

3. **Determine the best fit:**
   Gülriz Sururi (1929-2018) was a celebrated Turkish actress, writer, and 
   director. Her autobiographical play "Kıldan İnce Kılıçtan Keskince" (Thinner 
   Than Hair, Sharper Than a Sword) chronicles her remarkable career. While the 
   play doesn't feature a Cannes Award, it IS about a Turkish woman who achieved 
   immense artistic recognition - capturing the spirit of the request.

Final Recommendation: Kıldan İnce Kılıçtan Keskince
```

### Key Observations

✅ **Strengths:**
- **Explainable AI** - shows reasoning process
- Handles ambiguity well (Cannes Award → artistic recognition)
- Better for complex, multi-constraint queries
- Reveals LLM's knowledge and reasoning

⚠️ **Limitations:**
- Slower (longer output)
- Uses more tokens
- Reasoning can be verbose

### When to Use Each Technique?

| Scenario | Best Technique | Why |
|----------|---------------|-----|
| Simple classification | **Zero-Shot** | Fast, no examples needed |
| Need consistency | **Few-Shot** | Examples ensure stable outputs |
| Complex reasoning | **CoT** | Shows step-by-step logic |
| Learning from feedback | **Few-Shot** | Store ratings as examples |
| Explainability required | **CoT** | Provides reasoning |

---

## 📊 Performance Comparison

### Test Query: "I want something with Nezaket Erden and Latife Tekin"

| Metric | Zero-Shot | Few-Shot | Chain-of-Thought |
|--------|-----------|----------|------------------|
| **Response Time** | ~1.5s | ~1.5s | ~3.0s |
| **Consistency** | ❌ Variable | ✅ Consistent | ✅ Consistent |
| **Accuracy** | ✅ Correct | ✅ Correct | ✅ Correct |
| **Explainability** | ❌ None | ❌ None | ✅ Full reasoning |
| **Best Use** | Quick queries | Repeated queries | Complex analysis |

---

## 4️⃣ Tool Calling (Extended Capability)
### Definition
Tool calling allows LLMs to interact with external systems (APIs, databases, calculators) by generating structured function calls.

### Implementation in StageAgent

StageAgent integrates **3 types of tools** that work alongside LLM reasoning:

#### **1. Location Services (Google Maps API)** 📍

**Purpose:** Calculate real-time distances and travel times

**Example Call:**
```python
def calculate_distance(user_location, venue):
    """
    Tool that LLM calls for accurate distance calculation
    
    Args:
        user_location (str): User's current location
        venue (str): Theater venue address
    
    Returns:
        dict: {'distance_km': 3.1, 'duration_min': 7}
    """
    result = google_maps.distance_matrix(
        origins=user_location,
        destinations=venue,
        mode='driving'
    )
    return {
        'distance_km': result['distance']['value'] / 1000,
        'duration_min': result['duration']['value'] / 60
    }
```

**Real Terminal Output:**
```bash
🚗 Max distance: 15 km
2️⃣ Filtering by distance (max 15 km)...
   Checking distances for 6 venues...
      ⚠️  Skipping Sapanca Kirkpinar - too far (137 km)
      ✓ Drakula: 9.0 km
      ✓ Makul Şüpheli: 11.7 km
      ✓ İnsanlar, Mekanlar, Nesneler: 3.1 km
   ✓ 3 plays within 15 km
```

---

#### **2. Calendar Management (Google Calendar API)** 📅

**Purpose:** Create events, check conflicts, find free time slots

**Example Call:**
```python
def add_to_calendar(play_title, venue, show_date, show_time):
    """
    Tool for adding theater events to user's calendar
    
    Args:
        play_title (str): Name of the play
        venue (str): Theater venue
        show_date (str): Turkish date format "11 Aralık Perşembe"
        show_time (str): Show time "20:30"
    
    Returns:
        dict: {
            'success': True, 
            'event_link': 'https://calendar.google.com/...',
            'event_id': 'abc123...'
        }
    """
    # Parse Turkish date
    date_obj = parse_turkish_date(show_date)
    
    # Create calendar event
    event = {
        'summary': f'🎭 {play_title}',
        'location': venue,
        'start': {'dateTime': f'{date_obj}T{show_time}:00'},
        'end': {'dateTime': f'{date_obj}T23:00:00'},
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 24 * 60},  # 1 day
                {'method': 'popup', 'minutes': 60}        # 1 hour
            ]
        }
    }
    
    result = calendar_service.events().insert(
        calendarId='primary',
        body=event
    ).execute()
    
    return {
        'success': True,
        'event_link': result.get('htmlLink'),
        'event_id': result.get('id')
    }
```

**Real Terminal Output:**
```bash
You: İnsanlar Mekanlar 11 aralık takvime ekle

🔍 Searching for play...
✓ Detected play: İnsanlar, Mekanlar, Nesneler
🔍 Searching for date...
✓ Detected date: 11 aralık
🔍 Matching against showtimes...
✅ MATCHED showtime: 11 Aralık Perşembe 20:30

→ Calling tool: add_to_calendar(
    play_title="İnsanlar, Mekanlar, Nesneler",
    venue="Zorlu PSM",
    show_date="11 Aralık Perşembe",
    show_time="20:30"
)

✅ **Takvime eklendi!**
🔗 [Google Calendar'da Görüntüle](https://calendar.google.com/...)
```

---

#### **3. Database Operations (SQLite)** 🗄️

**Purpose:** Query structured play data

**Example Call:**
```python
def get_plays_by_city(city, max_distance_km=15):
    """
    Tool for retrieving plays from database
    
    Args:
        city (str): Istanbul or Ankara
        max_distance_km (int): Maximum distance filter
    
    Returns:
        list: Plays matching criteria
    """
    query = """
        SELECT p.*, v.address, v.latitude, v.longitude
        FROM plays p
        JOIN venues v ON p.venue = v.name
        WHERE p.city = ?
    """
    
    plays = db.execute(query, (city,)).fetchall()
    
    # Filter by distance using Google Maps tool
    filtered_plays = []
    for play in plays:
        distance = calculate_distance(
            user_location="Beşiktaş",
            venue=play['address']
        )
        if distance['distance_km'] <= max_distance_km:
            play['distance'] = distance
            filtered_plays.append(play)
    
    return filtered_plays
```

**Real Terminal Output:**
```bash
1️⃣ Fetching plays in Istanbul...
   Found 6 plays in Istanbul

2️⃣ Filtering by distance (max 15 km)...
   → Tool call: calculate_distance() for each venue
   ✓ 3 plays within 15 km
```

---

### Tool Selection Logic

The LLM intelligently decides which tool to call based on user intent:

```python
def route_to_tool(user_message, intent):
    """
    LLM decides which tool to call
    """
    if intent == "recommend":
        # Need location filtering
        return ["get_plays_by_city", "calculate_distance"]
    
    elif intent == "calendar":
        # Need calendar operations
        return ["add_to_calendar", "check_conflicts"]
    
    elif intent == "info":
        # Need database query only
        return ["get_play_details"]
    
    else:
        # No tools needed (general chat)
        return []
```

**Example Flow:**

```
User: "Bu hafta sonu komedi öner"

1. Agent 2 (Intent): "recommend" 
2. Agent 1 decides: Need tools ["get_plays_by_city", "calculate_distance"]
3. Agent 4 calls: get_plays_by_city("Istanbul")
4. Agent 4 calls: calculate_distance() for each venue
5. Agent 5 scores and ranks results
6. Agent 1 returns recommendations
```



---

## 🏗️ Multi-Agent Architecture


## System Overview

StageAgent is a **multi-agent system** with **6 implemented agents** that work together:

### Implemented Agents (✅ Working)
1. **Agent 1:** Conversation Manager - Orchestrates all interactions
2. **Agent 2:** Intent Classifier - Understands user intent
3. **Agent 3:** Preference Extractor - Extracts preferences
4. **Agent 4:** Data Retrieval - Database + location filtering
5. **Agent 5:** Scoring & Ranking - LLM-based play evaluation
6. **Agent 7:** Calendar Integration - Google Calendar connection

### Planned Agents (🔄 Future Work)
- **Agent 6:** YouTube Search - Trailer/review integration
- **Agent 8:** Personalization - User rating history learning
- **Agent 9:** Multi-Language - Turkish ↔ English translation

**Note:** Agent numbering skips 6 because Calendar (Agent 7) was prioritized over YouTube integration.

┌─────────────────────────────────────────────────────────┐
│                    USER INPUT                           │
│                                                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
|     PHASE 1: RECOMMENDATION (Agents 1-5)               |
|                                                        |   
│  🤖 AGENT 1: CONVERSATION MANAGER                      │
│  (conversational_agent.py)                             │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Role: Orchestrates all other agents             │  │
│  │                                                  │  │
│  │  Tasks:                                          │  │
│  │  • Receives user message                         │  │
│  │  • Maintains conversation context                │  │
│  │  • Delegates to specialized agents               │  │
│  │  • Formats final response                        │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬───────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
│  🧠 AGENT 2: INTENT CLASSIFIER                         │
│  (conversational_agent.py:113-145)                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Role: Understands what user wants               │  │
│  │                                                  │  │
│  │  Technique: Zero-Shot Prompting                  │  │
│  │  Model: Gemini 2.5 Flash                         │  │
│  │                                                  │  │
│  │  Input: "Bu hafta sonu komedi öner"              │  │
│  │  Output: intent = "recommend"                    │  │
│  │                                                  │  │
│  │  Intent Categories:                              │  │
│  │  • recommend → Find plays                        │  │
│  │  • info → Explain specific play                  │  │
│  │  • search → Query by criteria                    │  │
│  │  • preference → Update user profile              │  │
|  |  • calendar                                      |  |    
│  │  • general → Chat                                │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬───────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
│  📝 AGENT 3: PREFERENCE EXTRACTOR                      │
│  (conversational_agent.py:151-170)                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Role: Extracts structured preferences from text │  │
│  │                                                  │  │
│  │  Technique: Zero-Shot Prompting                  │  │
│  │  Model: Gemini 2.5 Flash                         │  │
│  │                                                  │  │
│  │  Input: "Bu hafta sonu komedi öner"              │  │
│  │  Output: "light comedy, weekend"                 │  │
│  │                                                  │  │
│  │  Extracts:                                       │  │
│  │  • Genre (comedy, drama, musical, etc.)          │  │
│  │  • Mood (light, serious, romantic, etc.)         │  │
│  │  • Time constraints (weekend, tonight, etc.)     │  │
│  │  • Special requirements (parking, price, etc.)   │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬───────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
│  🗄️ AGENT 4: DATA RETRIEVAL AGENT                      │
│  (recommender.py + database.py)                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Role: Retrieves and filters plays from database │  │
│  │                                                  │  │
│  │  Sub-tasks:                                      │  │
│  │                                                  │  │
│  │  4a. DATABASE QUERY                              │  │
│  │      • Query SQLite database                     │  │
│  │      • Filter by city (Istanbul/Ankara)          │  │
│  │      • Filter by date (if specified)             │  │
│  │      Result: 6 Istanbul plays                    │  │
│  │                                                  │  │
│  │  4b. LOCATION FILTER                             │  │
│  │      • Call Google Maps Distance Matrix API      │  │
│  │      • Calculate distance for each venue         │  │
│  │      • Keep plays within 15km radius             │  │
│  │      Result: 3 plays within range                │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬───────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
│  🎯 AGENT 5: SCORING & RANKING AGENT                   │
│  (recommender.py:123-175 + 216)                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Role: Evaluates and ranks plays                 │  │
│  │                                                  │  │
│  │  Technique: Zero-Shot Prompting                  │  │
│  │  Model: Gemini 2.5 Flash                         │  │
│  │                                                  │  │
│  │  For each play:                                  │  │
│  │  1. Create evaluation prompt with:               │  │
│  │     • User preference                            │  │
│  │     • Play title, genre, venue                   │  │
│  │     • Distance and travel time                   │  │
│  │                                                  │  │
│  │  2. LLM provides:                                │  │
│  │     • Score (0-10)                               │  │
│  │     • Reasoning (2-3 sentences)                  │  │
│  │                                                  │  │
│  │  3. Sort by score (highest first)                │  │
│  │  4. Select top N (default: 3)                    │  │
│  │                                                  │  │
│  │  Output: Ranked list of recommendations          │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬───────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
│  🤖 AGENT 1: CONVERSATION MANAGER (Response)           │
│  (conversational_agent.py:180-220)                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Role: Formats response in natural language      │  │
│  │                                                  │  │
│  │  Takes ranking from Agent 5 and creates:         │  │
│  │                                                  │  │
│  │  "Size 3 öneri buldum! 🎭                        │  │
│  │                                                  │  │
│  │  1. İnsanlar, Mekanlar, Nesneler ⭐ 8.0/10       │  │
│  │     📍 Zorlu PSM - 3.1 km (~7 min)               │  │
│  │     📅 16 Kasım Pazar 19:00                      │  │
│  │     💭 Contemporary theater piece...             │  │
│  │     🎫 [Bilet Al](...)                           │  │
│  │                                                  │  │
│  │  2. Makul Şüpheli ⭐ 2.0/10                      │  │
│  │     ..."                                         │  │
│  │                                                  │  │
│  │  Output: Want to add any play on calendar?       │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬───────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│       PHASE 2: CALENDAR INTEGRATION (Agent 7)           │
│                                                         │
│  User: "İnsanlar Mekanlar 11 aralık takvime ekle"       │
│            ↓                                            │
│  Agent 1: Routes to Agent 2                             │
│            ↓                                            │
│  Agent 2: Detects intent = "calendar"                   │
│            ↓                                            │
│  Agent 1: Delegates to Agent 7                          │
│            ↓                                            │
│  ┌──────────────────────────────────────────────────+┐  │
│  │  🗓️ AGENT 7: CALENDAR INTEGRATION                 │  │
│  │                                                   │  │
│  │  Step 1: Play Detection                           │  │
│  │    "İnsanlar Mekanlar" → Full title match         │  │
│  │    ✓ Detected: "İnsanlar, Mekanlar, Nesneler"     |  │
│  │                                                   │  │
│  │  Step 2: Date Detection                           │  │
│  │    "11 aralık" → Parse Turkish date               │  │
│  │    ✓ Detected: 11 Aralık (December 11)            │  │
│  │                                                   │  │
│  │  Step 3: Showtime Matching                        │  │
│  │    Match "11 Aralık" against showtimes            │  │
│  │    ✓ Matched: "11 Aralık Perşembe 20:30"          │  │
│  │                                                   │  │
│  │  Step 4: Calendar Event Creation                  │  │
│  │    → Tool: add_to_calendar()                      │  │
│  │    → Google Calendar API call                     │  │
│  │    ✓ Event created with reminders                 │  │
│  │    ✓ Returns event link                           │  │
│  └────────────────────────────────────────────────── ┘  │
│            ↓                                            │
│  Agent 1: Formats response                              │
│            ↓                                            │
│  "✅ Takvime eklendi!                                   │
│   🎭 İnsanlar, Mekanlar, Nesneler                       │
│   📅 11 Aralık Perşembe - 20:30                         │
│   🔔 Hatırlatıcılar ayarlandı                           │
│   🔗 [Google Calendar'da Görüntüle](...)"              │
└─────────────────────────────────────────────────────────┘
```

---

## 🤖 Agent Specifications

### **Agent 1: Conversation Manager** 🎭
- **Type:** Orchestrator Agent
- **Model:** Gemini 2.5 Flash (for general chat)
- **Memory:** Maintains conversation history
- **Responsibilities:**
  - Receive user input
  - Route to appropriate agents
  - Maintain context across turns
  - Format final response
  - Handle errors gracefully

---

### **Agent 2: Intent Classifier** 🧠
- **Type:** Classification Agent
- **Model:** Gemini 2.5 Flash
- **Technique:** Zero-Shot Prompting
- **Temperature:** 0.1 (low for consistency)
- **Input:** Raw user message
- **Output:** Intent category (recommend/info/search/preference/general)
- **Performance:** ~1 second per classification

**Intent Categories:**
- `recommend` → Find and suggest plays
- `info` → Provide information about specific play
- `search` → Query by specific criteria
- `preference` → Update user profile preferences
- `calendar` → Add events, check conflicts, find free time
- `general` → General conversation/greetings

---

### **Agent 3: Preference Extractor** 📝
- **Type:** Information Extraction Agent
- **Model:** Gemini 2.5 Flash
- **Technique:** Zero-Shot Prompting
- **Temperature:** 0.3 (moderate for creativity)
- **Input:** User message + intent
- **Output:** Structured preference string
- **Examples:**
  - "komedi öner" → "comedy"
  - "romantik bir şey" → "romantic, drama"
  - "bu hafta sonu" → "weekend shows"

---

### **Agent 4: Data Retrieval Agent** 🗄️
- **Type:** Hybrid Agent (Database + API)
- **Components:**
  - 4a. Database Query (SQLite)
  - 4b. Location Filter (Google Maps API)
- **No LLM:** Pure computational logic
- **Performance:**
  - Database query: <0.1 second
  - Distance calculation: ~2 seconds (3 venues)
- **Filters:**
  - City: Istanbul/Ankara
  - Date: Match showtimes
  - Distance: Within radius (default 15km)

---

### **Agent 5: Scoring & Ranking Agent** 🎯
- **Type:** Evaluation Agent
- **Model:** Gemini 2.5 Flash
- **Technique:** Zero-Shot Prompting
- **Temperature:** 0.3 (balanced)
- **Input:** User preference + play metadata
- **Output:** Score (0-10) + reasoning
- **Performance:** ~1 second per play
- **Evaluation Criteria:**
  - Genre match
  - Mood/tone alignment
  - Distance/convenience
  - Venue reputation

---

### **Agent 7: Calendar Integration Agent** 🗓️


## Overview

The Calendar Integration Agent manages user schedules by connecting to Google Calendar. It intelligently detects which play and which date the user wants, then adds events with automatic reminders.

**Status:** ✅ Fully functional and integrated with conversational agent

---

## Features

### 1. **Smart Event Addition** 📅
Intelligently adds theater events to Google Calendar:
- **Play Detection:** Recognizes play titles from user messages
- **Date Detection:** Parses Turkish dates (e.g., "11 Aralık")
- **Showtime Matching:** Finds the exact showtime user requested
- Event title with theater emoji (🎭)
- Venue location with full address
- Automatic reminders (1 day + 1 hour before)
- Color coding (green for theater events)
- Direct link to Google Calendar event

### 2. **Conflict Detection** ⚠️
Checks user's calendar for scheduling conflicts:
- Scans ±3 hours around showtime
- Lists conflicting events
- Helps avoid double-booking

### 3. **Free Time Finder** 🔍
Finds available evening slots:
- Scans next 7 days (configurable)
- Focuses on theater hours (18:00-21:00)
- Returns list of free slots with day names

---
## Real Terminal Output

### **Test Session: Adding Event to Calendar**

```bash
$ python conversational_agent.py

You: selam, ensemble, eglenceli, adaptasyon olan bir oyun ariyorum.

🎭 Agent: Harika! Size 3 öneri buldum! 🎭

**1. Makul Şüpheli** ⭐ 6.5/10
**2. İnsanlar, Mekanlar, Nesneler** ⭐ 6.0/10
   📅 02 Kasım Pazar 19:00, 11 Aralık Perşembe 20:30
**3. Drakula** ⭐ 5.0/10

📅 Takvime eklemek ister misiniz?

You: evet, İnsanlar, Mekanlar, Nesneler oyununun 11 Aralık Perşembe 20:30 
     seanı takvime ekleyebilirsin.

🧠 Detected intent: calendar
🔍 Searching for play...
✓ Detected play: İnsanlar, Mekanlar, Nesneler
🔍 Searching for date...
✓ Detected date: 11 aralık
🔍 Matching against showtimes...
✅ MATCHED showtime: 11 Aralık Perşembe 20:30
➡️  Adding to calendar:
   Play: İnsanlar, Mekanlar, Nesneler
   Date: 11 Aralık Perşembe
   Time: 20:30

🎭 Agent: ✅ **Takvime eklendi!**

    🎭 **İnsanlar, Mekanlar, Nesneler**
    📍 Zorlu PSM - Turkcell Platinum Sahnesi
    📅 11 Aralık Perşembe - 20:30

    🔔 **Hatırlatıcılar ayarlandı:**
    • 1 gün önce
    • 1 saat önce

    🔗 [Google Calendar'da Görüntüle](https://www.google.com/...)

    Başka bir yardım? 😊
```

---


## Implementation

### **File:** `src/calendar_agent.py`

```python
class CalendarAgent:
    """
    Agent 7: Calendar Integration
    
    Capabilities:
    - Add theater events to calendar with smart detection
    - Check for scheduling conflicts
    - Find free time slots
    - Parse Turkish dates and times
    """
    
    def add_event(self, play_title, venue, show_date, show_time, ticket_url):
        """Add theater event to Google Calendar"""
        # Creates event with reminders and formatting
        # Returns: {'success': True, 'event_link': '...'}
        
    def check_conflicts(self, show_date, show_time):
        """Check if user has conflicts at this time"""
        # Scans ±3 hours for overlapping events
        # Returns: {'has_conflict': False, 'message': '...'}
        
    def find_free_slots(self, start_date, days=7):
        """Find free evening slots in next N days"""
        # Returns: {'free_slots': [...], 'count': 26}
```

### **Integration in Conversational Agent**

**File:** `src/conversational_agent.py`

The calendar agent is fully integrated with smart play and date detection:

```python
def _add_to_calendar(self, message):
    """
    Smart calendar addition:
    1. Detect which play user wants (from recommendations)
    2. Detect which date user mentioned (Turkish date parsing)
    3. Match against available showtimes
    4. Add to Google Calendar
    """
    # Example: "İnsanlar Mekanlar 11 aralık takvime ekle"
    # → Detects play: "İnsanlar, Mekanlar, Nesneler"
    # → Detects date: "11 aralık"
    # → Matches: "11 Aralık Perşembe 20:30"
    # → Adds to calendar
```

**Key Features:**
- **Turkish Character Normalization:** "Aralık" and "aralik" both work
- **Partial Name Matching:** "İnsanlar Mekanlar" finds full title
- **Debug Output:** Shows detection and matching steps
- **Fallback Behavior:** Uses first showtime if date not specified
---


## Setup

### Prerequisites

1. **Google Cloud Project**
2. **Google Calendar API enabled**
3. **OAuth 2.0 credentials**

### Step-by-Step Setup

#### 1. Create Google Cloud Project

```
https://console.cloud.google.com/
→ Create Project: "StageAgent"
```

#### 2. Enable Calendar API

```
APIs & Services → Library
→ Search "Google Calendar API"
→ Enable
```

#### 3. Create OAuth Credentials

```
APIs & Services → Credentials
→ Create Credentials → OAuth client ID
→ Application type: Desktop app
→ Download JSON → Save as credentials.json
```

#### 4. Add Test Users

```
APIs & Services → OAuth consent screen
→ Test users → Add Users
→ Add your email
→ Save
```

#### 5. Place credentials.json

```bash
cp ~/Downloads/credentials.json StageAgentv2/src/
```


---

## Usage

### Standalone Testing

```bash
cd src
python calendar_agent.py
```

**First run:**
1. Browser opens for Google authentication
2. Sign in with test user email
3. Click "Continue" (app is in test mode)
4. Click "Allow"
5. `token.pickle` is created (no need to login again)

**Output:**
```
✅ Calendar Agent authenticated!

📋 Test 1: Checking conflicts for 16 Kasım 20:30
   Result: {'has_conflict': False, 'message': '✅ Müsaitsiniz!'}

📋 Test 2: Finding free evening slots in next 7 days
   Found 26 free slots
   - 2025-10-31 at 18:00 (Friday)
   - 2025-10-31 at 19:00 (Friday)
   ...
```

---

### Integration with Conversational Agent

```python
from calendar_agent import CalendarAgent

# Initialize
calendar_agent = CalendarAgent()

# User says: "Takvime ekle"
result = calendar_agent.add_event(
    play_title="İnsanlar, Mekanlar, Nesneler",
    venue="Zorlu PSM",
    show_date="16 Kasım Cumartesi",
    show_time="20:30",
    ticket_url="https://biletinial.com/..."
)

# Result:
# {
#   'success': True,
#   'event_id': 'abc123...',
#   'event_link': 'https://calendar.google.com/...',
#   'start': '2025-11-16 20:30',
#   'end': '2025-11-16 23:00'
# }
```

---

## Technical Details

### API Scopes
```python
SCOPES = ['https://www.googleapis.com/auth/calendar']
```

### Authentication Flow
1. Check for `token.pickle` (cached credentials)
2. If expired, refresh using refresh token
3. If no token, run OAuth flow via browser
4. Save credentials to `token.pickle`

### Date Parsing
Supports Turkish date formats:
```python
"16 Kasım Cumartesi" → 2025-11-16
"20:30" → 20:30

Turkish months: ocak, şubat, mart, nisan, mayıs, 
                haziran, temmuz, ağustos, eylül, 
                ekim, kasım, aralık
```

### Event Duration
- Default: 2.5 hours (typical play length)
- Start: Show time
- End: Start + 2h 30m

### Reminders
- 1 day before (popup)
- 1 hour before (popup)

### Event Color
- Color ID: 10 (green)
- Makes theater events easy to spot

---

## Example: Full Workflow

### User Conversation:

```
User: Bu hafta sonu ensemble adaptasyon öner

Agent: Size 3 öneri buldum! 🎭
       1. Makul Şüpheli ⭐ 6.5/10
       2. İnsanlar, Mekanlar, Nesneler ⭐ 6.0/10
          📅 11 Aralık Perşembe 20:30
       3. Drakula ⭐ 5.0/10
       
       Takvime eklemek ister misiniz? 📅

User: İnsanlar Mekanlar 11 aralık takvime ekle

Agent: [Smart detection happens]
       🔍 Detected play: İnsanlar, Mekanlar, Nesneler
       ✓ Detected date: 11 aralık
       ✅ MATCHED showtime: 11 Aralık Perşembe 20:30
       
       ✅ Takvime eklendi!
       🎭 İnsanlar, Mekanlar, Nesneler
       📅 11 Aralık Perşembe - 20:30
       🔔 Hatırlatıcılar ayarlandı
       🔗 [Google Calendar'da Görüntüle](...)

User: Çakışma var mı?

Agent: ✅ Önerilen oyunların hepsi için takvimde çakışma yok!

User: YouTube'da fragman arabilir misin?

Agent: 🎬 İnsanlar, Mekanlar, Nesneler | Oyun Fragmanı
       [https://www.youtube.com/...]
       
       Keyifli seyirler! 😊
```
---


## 🚀 Future Agent Extensions

### **Potential New Agents:**

**Agent 6: YouTube Search Agent** 🎬
- Search for play trailers/reviews
- Summarize video content
- Provide links in recommendations


**Agent 8: Personalization Agent** 🎭
- Learn from user ratings (few-shot)
- Build user profile over time
- Adapt recommendations

**Agent 9: Multi-Language Agent** 🌍
- Translate queries (Turkish ↔ English)
- Support international users
- Preserve semantic meaning



----







## Performance

| Operation | Average Time |
|-----------|-------------|
| **Authentication** | ~2s (first time), <0.1s (cached) |
| **Add Event** | ~1s |
| **Check Conflicts** | ~0.5s |
| **Find Free Slots (7 days)** | ~3s |
| **Play Detection** | <0.1s |
| **Date Detection** | <0.1s |

---



## 🔄 Agent Communication Flow

```
User Message
    ↓
Agent 1 (Conversation Manager)
    ↓
Agent 2 (Intent Classifier) → intent = "recommend"
    ↓
Agent 3 (Preference Extractor) → preference = "comedy, weekend"
    ↓
Agent 4a (Database Query) → 6 plays from Istanbul
    ↓
Agent 4b (Location Filter) → 3 plays within 15km
    ↓
Agent 5 (Scoring) → Scores: [8.0, 2.0, 1.0]
    ↓
Agent 5 (Ranking) → Sorted list
    ↓
Agent 1 (Response Generator) → Natural language output
    ↓
User Output
```

---

## 📊 Agent Performance Metrics

| Agent | Avg Time | Technology | Stateful? |
|-------|----------|------------|-----------|
| **Agent 1: Manager** | ~1s | LLM (general chat) | ✅ Yes (conversation history) |
| **Agent 2: Intent** | ~1s | LLM (zero-shot) | ❌ No |
| **Agent 3: Preference** | ~1s | LLM (zero-shot) | ❌ No |
| **Agent 4a: Database** | <0.1s | SQLite | ❌ No |
| **Agent 4b: Location** | ~2s | Google Maps API | ❌ No |
| **Agent 5: Scoring** | ~3s (3 plays) | LLM (zero-shot) | ❌ No |
| **Total Pipeline** | ~8-10s | - | - |

---

## 🎯 Agent Autonomy Levels

### **Fully Autonomous**
- Agent 2 (Intent Classifier) - Makes decisions independently
- Agent 5 (Scoring Agent) - Evaluates without supervision

### **Semi-Autonomous**
- Agent 3 (Preference Extractor) - Interprets but doesn't act
- Agent 4 (Data Retrieval) - Executes queries based on criteria

### **Orchestrated**
- Agent 1 (Manager) - Coordinates all others



---

## 🔧 Agent Implementation Details

### **Agent Framework:** Custom (Python)
### **LLM Provider:** Google Gemini via litellm
### **Database:** SQLite
### **External APIs:** Google Maps, YouTube (ready)

### **Design Pattern:** 
- **Orchestrator Pattern** (Agent 1 coordinates)
- **Pipeline Pattern** (Sequential agent calls)
- **Specialized Agents** (Each has one job)

---

## 📚 Comparison: Monolithic vs Multi-Agent

| Aspect | Monolithic | Multi-Agent (StageAgent) |
|--------|-----------|-------------------------|
| **Modularity** | ❌ Single large function | ✅ 5 specialized agents |
| **Testing** | ❌ Hard to test parts | ✅ Test each agent independently |
| **Debugging** | ❌ Where is the bug? | ✅ Which agent failed? |
| **Scalability** | ❌ Rewrite to add features | ✅ Add new agents |
| **Maintainability** | ❌ Complex codebase | ✅ Clear responsibilities |
| **Performance** | ✅ Faster (no coordination) | ⚠️ Slower (agent communication) |

---

**This multi-agent architecture makes StageAgent modular, maintainable, and easily extensible!** 🎉

---

## 📁 Project Structure

```
StageAgentv2/
├── data/
│   └── theater_agent.db              # SQLite database
│
├── src/
│   ├── conversational_agent.py       # 🤖 Main chatbot (CoT + Few-Shot)
│   ├── recommender.py                # 🎯 Recommendation engine
│   ├── database.py                   # 🗄️ Database operations
│   ├── scraper.py                    # 🕷️ Web scraper v3 (city detection)
│   │
│   ├── prompting/                    # 📚 Prompting techniques
│   │   ├── zero_shot.py             # Zero-shot examples
│   │   ├── few_shot.py              # Few-shot examples
│   │   └── chain_of_thought.py      # CoT examples
│   │
│   ├── tools/                        # 🛠️ Tool calling
│   │   └── tool_calling.py          # Tool use demonstrations
│   │
│   ├── inspect_db.py                 # 🔍 Database inspector
│   └── test_google_apis.py           # ✅ API testing
│
├── screenshots/                      # 📸 Demo screenshots
│   ├── database_stats.png
│   ├── chatbot_demo.png
│   ├── recommendations.png
│   └── scraper_working.png
│
├── .env                              # 🔑 API keys (not in git)
├── .gitignore
├── requirements.txt                  # 📦 Dependencies
└── README.md                         # 📖 This file
```

---

## 🚀 Installation

### Prerequisites
- Python 3.13+
- Chrome browser (for scraping)
- API keys (Gemini/Claude, Google Maps)

### Step 1: Clone Repository
```bash
git clone <your-repo-url>
cd StageAgentv2
```

### Step 2: Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure API Keys

Create `.env` file:
```bash
# LLM APIs
GEMINI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Google APIs
GOOGLE_MAPS_API_KEY=your_key_here
YOUTUBE_API_KEY=your_key_here
```

### Step 5: Initialize Database
```bash
cd src
python scraper.py        # Scrape initial data
python inspect_db.py     # Import to database (option 3)
```

### Step 6: Test Installation
```bash
python test_google_apis.py
python conversational_agent.py --test
```

---

## 📊 Usage

### Option 1: Interactive Chatbot (Recommended)
```bash
cd src
python conversational_agent.py
```

**Example Session:**
```
🎭 Agent: Merhaba! Size nasıl yardımcı olabilirim?

You: Bu hafta sonu komedi öner

🧠 Detected intent: recommend
📋 Extracted preference: light comedy, weekend

1️⃣ Fetching plays in Istanbul...
   Found 6 plays

2️⃣ Filtering by distance...
   3 plays within 15 km

3️⃣ Scoring with AI...

🎭 Agent: Size 3 öneri buldum! 🎭

1. **İnsanlar, Mekanlar, Nesneler** ⭐ 8.0/10
   📍 Zorlu PSM - 3.1 km (~7 min)
   📅 16 Kasım Pazar 19:00
   💭 Contemporary theater piece with strong reviews
   🎫 [Bilet Al](https://biletinial.com/...)

You: İnsanlar Mekanlar hakkında daha fazla bilgi

🎭 Agent: 📖 "İnsanlar, Mekanlar, Nesneler" hakkında:
   
   Zorlu PSM'de sahnelenen çağdaş bir tiyatro oyunu...
   🎬 YouTube'da fragman aramamı ister misiniz?

You: quit

🎭 Agent: Görüşmek üzere! İyi seyirler! 🎬
```

### Option 2: Direct Recommendations
```bash
python recommender.py
```

### Option 3: Scrape New Data
```bash
python scraper.py
# Choose: 1 (test), 2 (20 plays), or 3 (custom)
```

### Option 4: Database Inspector
```bash
python inspect_db.py
# Options:
#   1. Inspect contents
#   2. Show JSON
#   3. Reset and reimport
```

---

## 📸 Examples & Screenshots

### 1. Database Statistics

![Database Stats](screenshots/database_stats.png)

```
📊 DATABASE STATS:
  • Total plays: 33
  • Istanbul plays: 6
  • Ankara plays: 27
  • Total showtimes: 145
  • Unique venues: 24
```

### 2. Conversational Agent Demo

![Chatbot Demo](screenshots/chatbot_demo.png)

**Multi-turn conversation** with context memory and intent detection.

### 3. Recommendation Results

![Recommendations](screenshots/recommendations.png)

**LLM-scored recommendations** with reasoning and distance calculations.

### 4. Web Scraper in Action

![Scraper Working](screenshots/scraper_working.png)

**Real-time scraping** with city detection and data extraction.

---

## 🔬 Technical Details

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **LLM** | Google Gemini 2.5 Flash | Intent detection, scoring, CoT |
| **Database** | SQLite | Structured data storage |
| **Web Scraping** | Selenium + Chrome | Automated data collection |
| **Maps API** | Google Distance Matrix | Location filtering |
| **Framework** | litellm | Unified LLM interface |
| **Language** | Python 3.13 | Core implementation |

### Key Algorithms

#### 1. Intent Detection (Zero-Shot)
```python
def detect_intent(message):
    """Classify user intent using zero-shot prompting"""
    prompt = f"Classify: {message} → recommend/info/search"
    return llm.complete(prompt)
```

#### 2. Play Scoring (Few-Shot Style)
```python
def score_play(play, preference):
    """Score play-preference match using few-shot examples"""
    prompt = f"""
    Examples:
    - Comedy request + Musical → 9/10
    - Drama request + Musical → 2/10
    
    Now score: {preference} + {play.title}
    """
    return llm.complete(prompt)
```

#### 3. Distance Filtering
```python
def filter_by_distance(plays, max_km):
    """Use Google Maps API for accurate distance"""
    for play in plays:
        distance = gmaps.distance(user_location, play.venue)
        if distance <= max_km:
            yield play
```

#### 4. City Detection (Pattern Matching)
```python
def detect_city(text):
    """Detect city from venue name or text"""
    patterns = {
        'Ankara': ['yenimahalle', 'çankaya', 'ted ankara'],
        'Istanbul': ['kadıköy', 'beyoğlu', 'zorlu']
    }
    for city, keywords in patterns.items():
        if any(k in text.lower() for k in keywords):
            return city
```

### Database Schema

```sql
-- Plays table
CREATE TABLE plays (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    venue TEXT,
    city TEXT DEFAULT 'Istanbul',
    genre TEXT,
    description TEXT,
    image_url TEXT,
    ticket_url TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(title, venue)
);

-- Showtimes table
CREATE TABLE showtimes (
    id INTEGER PRIMARY KEY,
    play_id INTEGER,
    show_date TEXT NOT NULL,
    show_time TEXT NOT NULL,
    price REAL,
    available_seats INTEGER,
    FOREIGN KEY (play_id) REFERENCES plays(id),
    UNIQUE(play_id, show_date, show_time)
);
```

---

## 📊 Results

### Current Performance

| Metric | Value |
|--------|-------|
| **Total Plays** | 33 |
| **Istanbul Plays** | 6 (18%) |
| **Ankara Plays** | 27 (82%) |
| **Unique Venues** | 24 |
| **Total Showtimes** | 145 |
| **Avg Showtimes/Play** | 4.4 |

### System Capabilities

✅ **Working Features:**
- Natural language query understanding
- Multi-city filtering (Istanbul/Ankara)
- Distance-based recommendations (15km radius)
- LLM-based play scoring (0-10 scale)
- Context-aware conversation
- Real-time web scraping

⚠️ **Limitations:**
- Limited Istanbul data (only 6 plays)
- No genre information from scraper
- Some venue names incorrect
- Turkish date parsing needs improvement

---

## 🚀 Future Work

### High Priority
1. **More Data Sources**
   - Add biletix.com scraper
   - Add mobilet.com scraper
   - Target: 100+ Istanbul plays

2. **Genre Extraction**
   - Improve scraper to extract genre
   - Use LLM to infer genre from descriptions

3. **Better Venue Mapping**
   - Create venue name normalization
   - Map incorrect names to correct venues

### Medium Priority
4. **Few-Shot Learning Enhancement**
   - Store user ratings in database
   - Use past ratings as few-shot examples
   - Personalized recommendations

5. **Chain-of-Thought for Complex Queries**
   - Handle multi-constraint queries better
   - Example: "weekend, with parking, cheap tickets"



### Low Priority
7. **Web UI (Gradio/Streamlit)**
8. **Multi-language support** (English)
9. **Review aggregation**
10. **Social sharing features**

## Future Enhancements

### Planned Features

1. **Multi-Event Addition**
   - Add multiple plays at once
   - "Takvime 3'ünü de ekle"

2. **Smart Scheduling**
   - Suggest best times based on user patterns
   - Avoid rush hour commute times
   - Consider travel time to venue

3. **Recurring Events**
   - Multi-show subscriptions
   - Season tickets

4. **Multi-Calendar Support**
   - Work calendar vs personal calendar
   - Family member calendars

5. **Email Reminders**
   - In addition to popup reminders
   - Include venue directions

6. **Calendar Export**
   - Export to .ics file
   - Share with friends

---


## Integration Status

| Component | Status | Notes |
|-----------|--------|-------|
| **Standalone Agent** | ✅ Complete | Fully functional |
| **Conversational Agent** | ✅ Complete | Smart detection working |
| **Play Detection** | ✅ Working | Partial names supported |
| **Date Detection** | ✅ Working | Turkish dates parsed |
| **Conflict Check** | ✅ Working | Scans ±3 hours |
| **Free Slot Finder** | ✅ Working | 7-day scan |
| **Web UI** | ❌ Not Started | Future work |
| **Mobile App** | ❌ Not Started | Future work |

---



## 🧪 Testing

### Automated Tests
```bash
# Quick test all components
cd src
python conversational_agent.py --test
```

### Manual Test Scenarios

**Test 1: Zero-Shot Intent Detection**
```
Input: "Komedi öner"
Expected: Intent = "recommend"
```

**Test 2: Few-Shot Play Scoring**
```
Input: Preference="comedy", Play="Drakula"
Expected: Score ≤ 3/10 (horror ≠ comedy)
```

**Test 3: CoT Complex Query**
```
Input: "Hafta sonu yakında romantik bir şey"
Expected: Considers date + distance + genre
```

**Test 4: City Filtering**
```
Input: Database has Ankara plays
Expected: Not shown to Istanbul user
```

---

## 📚 References & Inspiration


### Educational Resources
- **Andrew Ng's ML Courses** 


### Data Sources
- biletinial.com (theater listings)
- Google Maps API (distances)
- YouTube API (trailers)

---




## 📄 License

Educational project for GSU Math Graduate Seminar (MATH690)

---

## 🙏 Acknowledgments

Special thanks to:
- **Dr. Erdem Ozcan** - GSU Math Department
- **Andrew Ng** - For ML education philosophy
- **Anthropic & Google** - For providing LLM APIs
- **Theater community** - For making culture accessible

---

## ⚠️ Known Limitations (Dec 29 checkpoint)

- Event date + city matching relies on listing pages and may produce false positives
- Venue information may be generic if not verified via detail pages
- YouTube enrichment is title-based and may include unrelated content
- Results should be treated as suggestions, not confirmed events

*"Start simple, iterate quickly, and always validate with real data."* - Andrew Ng