# 🎭 StageAgent - Multi-Agent AI Theater Recommendation System

> **MATH690 Agentic AI Graduate Seminar Project**  
> Galatasaray University, Applied Mathematics PhD Program  

---

## 📋 Project Overview

StageAgent is a **multi-agent conversational theater recommendation system** for Turkey. The system implements **Andrew Ng's Agentic AI Design Patterns** including reflection, tool use, planning, and multi-agent collaboration.

### 🎯 Key Features

| Feature | Description |
|---------|-------------|
| 🗣️ **Conversational Interface** | Natural language interaction in Turkish/English |
| 🏙️ **Multi-City Support** | Istanbul, Ankara, Adana, İzmir, Bursa, and more |
| 📅 **Smart Calendar Integration** | Google Calendar with conflict detection & reminders |
| 🔍 **Hybrid Search** | Database + Real-time web search via Tavily AI |
| 🤖 **AI Scoring** | Gemini LLM for intelligent play-preference matching |
| 👤 **Human-in-the-Loop** | User confirmation for conflicts, explicit web search |

---

## 🤖 Multi-Agent Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     StageAgent Multi-Agent System                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  User: "20 Ocak Istanbul'da oyun var mı? Takvime ekle"              │
│                              ↓                                       │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │         🎭 ConversationalAgent (ORCHESTRATOR)               │     │
│  │  • Intent Detection (search/calendar/info/preference)      │     │
│  │  • Context Management (city, date, preferences)            │     │
│  │  • Agent Coordination & Response Formatting                │     │
│  └────────────────────────────────────────────────────────────┘     │
│                              ↓                                       │
│      ┌───────────────────────┼───────────────────────┐              │
│      ↓                       ↓                       ↓               │
│ ┌──────────┐          ┌──────────┐           ┌──────────┐           │
│ │ 🗄️ DB    │          │ 🔍 Tavily │           │ 🧠 Memory │           │
│ │  Agent   │          │  Agent   │           │  Agent   │           │
│ │ (SQLite) │          │(Web+AI)  │           │(Context) │           │
│ └──────────┘          └──────────┘           └──────────┘           │
│      ↓                       ↓                                       │
│      └───────────┬───────────┘                                       │
│                  ↓                                                   │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │            ⭐ RecommenderAgent (Gemini LLM)                 │     │
│  │  • Play-Preference Matching (1-10 score)                   │     │
│  │  • Turkish Reasoning & Explanation                         │     │
│  └────────────────────────────────────────────────────────────┘     │
│                              ↓                                       │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │            📅 CalendarAgent (Google Calendar API)          │     │
│  │  • Conflict Detection (before adding!)                     │     │
│  │  • Event Creation with Reminders                           │     │
│  │  • Free Slot Finding                                       │     │
│  │  • Pending Play Memory (for "yine de ekle")               │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 🔗 Agent Communication Flow

```
1. User Input → ConversationalAgent
2. Intent Detection → Route to appropriate agent(s)
3. DatabaseAgent → Local plays (if available)
4. TavilyAgent → Web search (if DB empty or user requests)
5. RecommenderAgent → Score & rank results (stil need improvement)
6. CalendarAgent → Check conflicts → Add/Warn
7. ConversationalAgent → Format & return response
```

---

## 🔧 Andrew Ng's Agentic AI Patterns

### 1. 🔄 Reflection Pattern
| Implementation | Description |
|----------------|-------------|
| **AI Scoring** | Gemini LLM evaluates plays (1-10) with Turkish reasoning |
| **Validation** | Detects wrong city/date in web results |
| **Venue Filter** | Filters mismatched venues (e.g., Samsun play in Ankara) |
| **Conflict Check** | Validates calendar before adding events |

### 2. 🛠️ Tool Use Pattern
| Tool | Purpose |
|------|---------|
| **Tavily AI** | Web search with AI summarization |
| **Google Calendar API** | Event management, conflict detection |
| **SQLite Database** | Local play storage with fuzzy search |
| **Geopy/Nominatim** | Distance calculation |

### 3. 📋 Planning Pattern
| Strategy | Description |
|----------|-------------|
| **Intent Detection** | Classifies: search, calendar, info, preference |
| **Fallback Chain** | Database → Web Search → Direct Links |
| **Human-in-the-Loop** | User can request "web search", confirm conflicts |
| **Pending State** | Remembers play for "yine de ekle" confirmation |

### 4. 🤝 Multi-Agent Collaboration
| Agent | Role | Technology |
|-------|------|------------|
| **ConversationalAgent** | Orchestrator | Gemini LLM |
| **RecommenderAgent** | AI Scoring | Gemini LLM |
| **CalendarAgent** | Event Management | Google API |
| **TavilyAgent** | Web Search | Tavily AI |
| **DatabaseAgent** | Data Storage | SQLite |
| **MemoryAgent** | Context Persistence | In-memory |

---

## 📁 Project Structure

```
sonson2/
├── src/
│   ├── conversational_agent.py   # Main orchestrator (1900+ lines)
│   ├── tavily_agent.py           # Web search with AI summary
│   ├── calendar_agent.py         # Google Calendar + conflict detection
│   ├── recommender_agent.py      # Gemini LLM scoring
│   └── database.py               # SQLite operations
├── data/
│   └── theater_agent.db          # SQLite database
├── credentials/
│   └── credentials.json          # Google OAuth (not in repo)
├── .env                          # API keys (not in repo)
├── requirements.txt
└── README.md
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.9+
- Google Cloud Project with Calendar API enabled
- Tavily API key
- Google Gemini API key

### 1. Clone & Install
```bash
cd /path/to/sonson2
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment Variables (.env)
```env
GEMINI_API_KEY=your_gemini_api_key
TAVILY_API_KEY=your_tavily_api_key
```

### 3. Google Calendar Setup
1. Create project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable Calendar API
3. Create OAuth 2.0 credentials
4. Download as `credentials/credentials.json`
5. Add test user email in OAuth consent screen

### 4. Run
```bash
python3 src/conversational_agent.py
```

---

## 💬 Usage Examples

### 🔍 Theater Search (Database + Web)
```
You: 20 Ocak 2026 Istanbul'da hangi oyunlar var?

🎭 Agent: 🔍 **Istanbul** için **20 Ocak 2026** web araması sonuçları:

📋 **Web'den bulunan bilgi:**
The event "Başka Hayat" is scheduled for 20 Ocak 2026 in Istanbul.
The performance will take place at Fişekhane Ana Sahne.

🎭 **Bulunan Oyunlar:**
   1. **Başka Hayat** - 📍 Fişekhane Ana Sahne - [Bilet](...)
   2. **Horlamalar** - [Bilet](...)
   3. **Aydınlıkevler** - [Bilet](...)

📅 Yukarıdaki oyunlardan birini takvime eklemek ister misiniz?
```

### 📅 Calendar Add (No Conflict)
```
You: Başka Hayat oyununu takvimime ekler misin?

🎭 Agent: ✅ **Takvime eklendi!**

🎭 **Başka Hayat**
📍 Fişekhane Ana Sahne
📅 20 Ocak 2026 - 20:00

🔔 **Hatırlatıcılar ayarlandı:**
• 1 gün önce
• 1 saat önce
```

### ⚠️ Conflict Detection & Confirmation
```
You: Horlamalar isimli oyunu takvimime ekler misin?

🎭 Agent: ⚠️ **Çakışma Tespit Edildi!**

🎭 **Horlamalar**
📅 20 Ocak 2026 - 20:00

❌ **Bu saatte zaten planınız var:**
   • 🎭 Başka Hayat

**Ne yapmak istersiniz?**
• "**Yine de ekle**" → Çakışmaya rağmen **Horlamalar** ekler
• "**İptal**" → Eklemez

You: yine de ekle

🎭 Agent: ✅ **Takvime eklendi!** (Çakışmaya rağmen)

🎭 **Horlamalar**  ← Doğru oyun eklendi!
📍 Istanbul
📅 20 Ocak 2026 - 20:00
```

### 📊 Conflict Check
```
You: takvimde çakışma var mı?

🎭 Agent: ⚠️ **5 tarihte çakışma bulundu!**

**1. 17 Ocak Cumartesi**
   🕐 **20:00** - 3 etkinlik çakışıyor:
      • Ben Medea Değilim
      • Bir Gece Masalı
      • Fabrikada Cinayet

**2. 20 Ocak Salı**
   🕐 **20:00** - 3 etkinlik çakışıyor:
      • Horlamalar
      • Başka Hayat

💡 **Öneriler:**
   • Çakışan etkinliklerden birini iptal edin
   • Farklı seanslara bilet alın
```

---

## 🎓 Lessons Learned

### 1. Web Scraping → AI Summary
| Problem | Solution |
|---------|----------|
| Complex HTML structure | Use Tavily AI summary instead |  ****
| Wrong play-URL mappings | Show source links for verification | (still need improvement)
| Inconsistent data | Add validation warnings |   ***

### 2. Pending Play Memory
| Problem | Solution |
|---------|----------|
| "Yine de ekle" added wrong play | Store pending play in `_pending_calendar_play` |
| Lost context after warning | Retrieve from memory on confirmation |

### 3. Conflict Detection Timing
| Problem | Solution |
|---------|----------|
| Events added despite conflicts | Check conflicts BEFORE adding |
| User not informed | Show clear warning with options |

### 4. Turkish Language Handling
| Problem | Solution |
|---------|----------|
| Character mismatches (ı/i, ş/s) | Normalize all text for comparison |
| Date parsing (Ocak, Şubat) | Comprehensive month mapping |

---

## 📊 Test Results Summary

| Test Case | Status | Notes |
|-----------|--------|-------|
| 20 Ocak 2026 Istanbul web search | ✅ Pass | Found Başka Hayat, Horlamalar, Aydınlıkevler |
| Add Başka Hayat (no conflict) | ✅ Pass | Added successfully |
| Add Horlamalar (with conflict) | ✅ Pass | Warning shown |
| "Yine de ekle" confirmation | ✅ Pass | **Horlamalar** added (not Başka Hayat!) |
| Conflict check | ✅ Pass | Shows 5 conflicts with Turkish dates |
| Explicit "web search" request | ✅ Pass | Bypasses database |
| Typo handling ("oacak" → "ocak") | ⚠️ Partial | Sometimes works | (still need improvement)

---

## ⚠️ Known Limitations

| Limitation | Impact | Potential Solution |
|------------|--------|-------------------|
| Tavily AI summary quality varies | Generic responses sometimes | Use `search_depth="advanced"` |
| Default 20:00 showtime | May not match actual | Extract from web content |
| Limited to biletinial/biletix | Misses independent theaters | Add more domains |
| No ticket purchase integration | User must visit site | Future: Add payment flow |

---

## 🔮 Future Improvements

### Short-term
- [ ] Better showtime extraction from web
- [ ] Genre-based filtering
- [ ] Price range filtering
- [ ] Multiple showtime selection

### Medium-term
- [ ] Direct biletinial API (if available)
- [ ] User preference learning
- [ ] Group booking suggestions
- [ ] Review/rating integration

### Long-term
- [ ] Mobile app (iOS/Android)
- [ ] Voice interface
- [ ] Social features (share with friends)
- [ ] Dynamic pricing alerts

---

## 🔑 API Keys & Services

| Service | Purpose | Rate Limits |
|---------|---------|-------------|
| Tavily | Web search + AI | 1000/month (free) |
| Gemini | LLM scoring | 60 req/min |
| Google Calendar | Events | 1M queries/day |
| Geopy | Distance | 1 req/sec |

---

## 📚 References

1. Andrew Ng - [Agentic Design Patterns](https://www.deeplearning.ai/the-batch/how-agents-can-improve-llm-performance/) (2024)
2. [Tavily API Documentation](https://docs.tavily.com/)
3. [Google Calendar API](https://developers.google.com/calendar)


---

## 🏆 Key Achievements

| Achievement | Description |
|-------------|-------------|
| ✅ Multi-Agent System | 6 specialized agents working together |
| ✅ All 4 Agentic Patterns | Reflection, Tool Use, Planning, Multi-Agent |
| ✅ Human-in-the-Loop | Conflict confirmation, explicit web search |
| ✅ Real-time Data | Web search for current theater info | (still need improvement)
| ✅ Calendar Intelligence | Conflict detection BEFORE adding |
| ✅ Turkish NLP | Date parsing, text normalization |

---

*Last Updated: December 30, 2025*