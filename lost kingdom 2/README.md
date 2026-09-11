# 👑 Lost Kingdom II: The Adaptive Chronicles
### Autonomous Multi-Agent Educational Game Prototype

An interactive RPG-style educational game where **5 autonomous AI agents** collaboratively monitor the player's interactions, calculate topic mastery, estimate affective gameplay engagement, adjust challenge difficulty, generate dynamic storyline branches, and synthesize adaptive NPC dialogue in real time.

---

## 🌟 Key Architecture & Multi-Agent System

```text
                 PLAYER INTERACTION (Answers, Timing, Movement, Voice)
                                           │
                                           ▼
                            ┌─────────────────────────────┐
                            │ Agent 1: Player Analysis    │
                            │ (Speed, Hesitation, Streaks)│
                            └──────────────┬──────────────┘
                                           │
                                           ▼
                            ┌─────────────────────────────┐
                            │ Shared Blackboard & State   │
                            │ (Memory, Metrics, Context)  │
                            └──────────────┬──────────────┘
                                           │
            ┌──────────────────────────────┼──────────────────────────────┐
            ▼                              ▼                              ▼
 ┌─────────────────────┐       ┌──────────────────────┐       ┌────────────────────────┐
 │ Agent 2: Knowledge  │       │  Agent 3: Emotion    │       │  Agent 5: Challenge &  │
 │ (BKT/Elo Mastery)   │       │  (Affective State)   │       │  Difficulty Calibrator │
 └──────────┬──────────┘       └──────────┬───────────┘       └───────────┬────────────┘
            │                             │                               │
            └─────────────────────────────┼───────────────────────────────┘
                                          │
                                          ▼
                            ┌─────────────────────────────┐
                            │ Agent 4: Story & NPC Agent  │
                            │ (3 Branches, Dynamic Tone)  │
                            └──────────────┬──────────────┘
                                           │
                                           ▼
                                 GAME WORLD & DASHBOARD
```

### The 5 Autonomous AI Agents:
1. **Agent 1 — Player Analysis Agent**:
   - Tracks response latency (`response_time_ms`), error streaks, answer velocity, and hesitation indices.
   - Dispatches parsed behavioral signatures to the shared blackboard.
2. **Agent 2 — Learning / Knowledge Agent**:
   - Maintains multi-topic mastery (Algebra, Geometry, Logic, Science, Cryptography).
   - Applies Bayesian Knowledge Tracing (BKT) and Elo rating updates.
   - Identifies strongest and weakest concepts.
3. **Agent 3 — Emotion / Engagement Agent**:
   - Evaluates interaction signals to estimate real-time gameplay states: `Engaged`, `Confused`, `Frustrated`, `Bored`, `Confident`.
   - Computes confidence percentages and triggers intervention recommendations.
4. **Agent 4 — Story & NPC Agent**:
   - Controls 3 major non-linear storyline branches:
     - **The Scholar's Path (Library)**: Mathematical proofs, geometry, and ancient codices.
     - **The Vanguard's Trial (Arena)**: Tactical mechanics, ballistics, and velocity physics.
     - **The Mystic's Synthesis (Sky Temple)**: Cryptographic ciphers and celestial logic runes.
   - Dynamically shifts NPC attitudes (supportive mentor when frustrated, challenging intellectual when confident).
5. **Agent 5 — Challenge & Difficulty Agent**:
   - Curates and generates educational questions across 4 difficulty tiers (`Easy`, `Medium`, `Hard`, `Expert`).
   - Generates hints and step-by-step explanations.
   - Contains a rich procedural generator with randomized math parameters and optional LLM API integration (`GEMINI_API_KEY`, `OPENAI_API_KEY`).

---

## 🎮 Game World & Features

- **4 Explorable Locations**:
  - *Village of Oakhaven* (Elder Sophia)
  - *Alexandrian Archive / Library* (Scholar Theron)
  - *Vanguard Arena / Training Ground* (Master Kael)
  - *Aetheria Sky Temple* (Guardian Lyra)
- **Fluid 2D Canvas Controls**:
  - Move with `WASD` / Arrow keys or click anywhere on the canvas to move.
  - Press `[E]` or click on an NPC to initiate conversation.
- **Voice Interaction (STT & TTS)**:
  - Speak questions to NPCs or answer challenges using browser speech recognition.
  - Listen to NPC responses with custom voice pitches and speech synthesis.
- **Real-Time Agent Dashboard**:
  - Live agent status cards with internal decision logs.
  - Real-time agent communication stream.
  - Story branch flowchart.
  - One-click simulation dock for instant evaluator demonstration.
- **Lightweight Multiplayer Room**:
  - Live player presence (see other players moving with cyan avatars and nametags).
  - Shared challenge competition with real-time scoreboards.
- **Long-Term Memory**:
  - Persisted SQLite database (`lost_kingdom.db`) storing sessions, past mistakes, NPC memories, and topic mastery across reloads.

---

## 🚀 Quickstart & Setup

### Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Modern web browser (Chrome, Edge, Firefox, Brave)

### Installation
```bash
# Clone or navigate to the project directory
cd "c:\Users\DELL\OneDrive\Pictures\lost kingdom 2"

# Install dependencies
python -m pip install -r requirements.txt
```

### Running the Game Server
```bash
python app.py
```
Access the game in your browser at:
👉 **`http://127.0.0.1:5000`**

### Running Automated Tests
```bash
python -m unittest discover -s tests
```

---

## 🎯 5-Minute Evaluator Demonstration Walkthrough

### Step 1: Exploration
- Enter `http://127.0.0.1:5000`. Observe the 2D world with 4 zones, animated torches, water fountains, and player avatar.
- Move towards **Elder Sophia** in the Village and press `[E]`. Notice her welcoming dialogue and the adaptive tone badge.

### Step 2: Autonomous Adaptation Loop (Demonstrating Adaptation)
1. Click **"Take Learning Challenge"**.
2. Intentionally pick an incorrect option with slight hesitation or click **"Need a Hint"**.
3. Submit a second incorrect answer.
4. **Observe the immediate adaptation**:
   - The HUD pill shifts from `MEDIUM` to `EASY`.
   - The Affective state badge shifts to `⚠️ Frustrated` or `❓ Confused`.
   - Elder Sophia's dialogue dynamically switches to an encouraging, patient mentor tone.
   - The next challenge generated is a simplified scaffolded question.

### Step 3: Mastery & Branch Unlock
1. Answer questions correctly at a brisk pace.
2. The Affective state shifts to `🔥 Confident`.
3. Difficulty automatically scales back to `MEDIUM` and `HARD`.
4. As overall mastery exceeds 45%, **The Scholar's Path** story branch unlocks, activating new quests at the Library!

### Step 4: Open the Multi-Agent Dashboard
1. Click the **"🤖 Agent Dashboard"** button in the top navigation bar.
2. Inspect the **5 Live Agent Cards** showing internal statuses, last actions, and confidence gauges.
3. Review the **Real-Time Activity Stream** showing inter-agent communication timestamps.
4. Test the **Simulation Dock**:
   - Click `⚠️ Trigger Frustration Streak` to see the agents react instantly.
   - Click `🔥 Trigger Mastery Streak` to observe difficulty increase and branch promotion.
   - Click `🌿 Reset Memory` to restore baseline state.

### Step 5: Long-Term Memory Verification
1. Refresh the web page.
2. Notice the welcome back notification: previously earned topic masteries, completed challenges, and narrative choices are automatically restored from the SQLite database!

---

## 📂 Project Structure

```text
lost kingdom 2/
├── app.py                      # Flask & SocketIO application entry point
├── config.py                   # Configuration and environment variables
├── models.py                   # SQLAlchemy database schemas (Player, Knowledge, Story, Logs)
├── requirements.txt            # Python dependencies
├── README.md                   # Complete documentation and demo guide
├── agents/
│   ├── base_agent.py           # Base agent lifecycle and telemetry class
│   ├── player_analysis_agent.py# Tracks speed, hesitation, and error streaks
│   ├── knowledge_agent.py      # BKT / Elo topic mastery and difficulty recommender
│   ├── emotion_agent.py        # Affective gameplay state classifier (Engaged, Confused, etc.)
│   ├── story_npc_agent.py      # Narrative branches, quest manager, and adaptive dialogue
│   ├── challenge_agent.py      # Question generation, validation, and difficulty tuning
│   └── orchestrator.py         # Multi-agent blackboard orchestrator & event bus
├── services/
│   └── llm_service.py          # Procedural math/logic generator & Gemini/OpenAI API bridge
├── routes/
│   ├── api.py                  # REST API endpoints for player, challenges, and simulation
│   └── sockets.py              # Socket.IO handlers for multiplayer & real-time telemetry
├── static/
│   ├── css/
│   │   ├── style.css           # Dark-fantasy glassmorphism design system & HUD
│   │   └── dashboard.css       # Multi-agent telemetry cards & activity console
│   └── js/
│       ├── audio.js            # Web Audio API procedural sound engine
│       ├── voice.js            # Web Speech STT and TTS engine
│       ├── world.js            # 2D Canvas zones, props, and NPC rendering
│       ├── game.js             # Player controller, keyboard/click navigation, loop
│       ├── ui.js               # Dialogue modals, challenge flow, and mastery HUD
│       ├── dashboard.js        # Agent telemetry command center & simulation triggers
│       └── multiplayer.js      # Real-time room presence and co-op quiz
├── templates/
│   └── index.html              # Master responsive HTML5 layout
└── tests/
    └── test_agents.py          # Automated test suite for multi-agent loops & persistence
```
