# 🎭 StageAgent - AI Theater Planning Assistant

An intelligent theater recommendation system using Agentic AI patterns.

## 📌 Project Status: STAGE 1 (MVP)

**Current Features:**
- ✅ Zero-shot play recommendations
- ✅ Mock theater database
- ✅ Basic LLM integration

**Coming Soon:**
- 🔄 Few-shot preference learning
- 🔄 Calendar integration
- 🔄 Location-based filtering
- 🔄 Chain-of-thought reasoning
- 🔄 Tool calling pattern
- 🔄 Planner architecture
- 🔄 Streamlit UI

## 🚀 Quick Start

### 1. Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys
```bash
# Edit .env and add your Anthropic API key
# Get key from: https://console.anthropic.com/
```

### 3. Run
```bash
python main.py
```

## 🎓 Course Information

**Course:** MATH690 - Agentic AI  
**Instructor:** Dr. Erdem Özcan  
**Students:** Ayşegül Yavuz & Makbul Özge Özler  
**Institution:** Galatasaray University  
**Semester:** Fall 2025  

## 📝 Development Stages

- **STAGE 1:** MVP ✅ (Current)
- **STAGE 2:** Few-Shot Learning 🔄
- **STAGE 3:** Tool Calling 🔄
- **STAGE 4:** Advanced Patterns 🔄
- **STAGE 5:** UI & Polish 🔄

## 🛠️ Tech Stack

- **LLM:** Claude 3.5 Haiku (Anthropic)
- **Integration:** LiteLLM
- **Language:** Python 3.11+

---

**Version:** 0.1.0 (STAGE 1)

---
## ✅ COMPLETED FEATURES

### STAGE 1: Zero-Shot MVP (Completed)
- ✅ Mock theater database (8 plays)
- ✅ LLM integration (Claude 3.5 Haiku)
- ✅ Zero-shot recommendations
- ✅ Basic CLI interface
- ✅ Basic theater recommendations



**Demo Screenshot:**

![Demo Screenshot](./screenshots/zero-shot-mvp.png)

**Example Queries:**
- "I want to see a Shakespearean tragedy" → Recommends Hamlet
- "Something funny for tonight" → Recommends Comedy Club Night



### STAGE 2: Few-Shot Learning + Rating System ✅
- ✅ User rating system (1-5 stars + review)
- ✅ SQLite database for preference storage
- ✅ Few-shot prompting using rating history
- ✅ Rating statistics (favorites, disliked plays)
- ✅ Menu-driven interface
- ✅ Both zero-shot and few-shot available

![Demo Screenshot](./screenshots/few-shot-mvp-1.png)
![Demo Screenshot](./screenshots/few-shot-mvp-2.png)
![Demo Screenshot](./screenshots/few-shot-mvp-3.png)


**Example Queries:**
# Menuden:
- 3 → Hamlet'e 5⭐ ver ("Amazing tragedy!")
- 3 → Comedy Club Night'a 2⭐ ver ("Not funny")
- 3 → Macbeth'e 4⭐ ver ("Dark and intense")

# Sonra:
- 2 → Few-Shot recommendation

# Query: "something dramatic and dark"
# → AI geçmişinize göre önerecek!