# 👩‍🏫 Emma — AI English Conversation Tutor & Bot

Emma is a friendly, patient English conversation partner and tutor designed to help learners improve their English naturally. Users chat with Emma in English, and she converses naturally, gently corrects mistakes, explains grammar rules, teaches vocabulary, and adapts to the learner's level (A1 to C1).

Available as both a **Telegram Bot** and a **Modern React + Tailwind CSS Web Application**.

---

## 🌟 Key Features

1. **Modern React 18 + Tailwind CSS Web App**
   - Built with Vite, React 18, Tailwind CSS, and Lucide Icons.
   - Interactive level selector (A1–C1 pills with CEFR indicators).
   - Real-time conversation stream with animated typing indicators.
   - Voice note recorder via browser HTML5 MediaRecorder.
   - One-click "🇺🇿 Explain in Uzbek" translation on every correction card.
   - Quick action shortcuts for Topics, Quizzes, Summaries, and Modes.

2. **Natural English Conversation**
   - Emma replies in short, engaging messages (2–5 sentences).
   - Always ends each message with **exactly ONE question** to keep the learner talking.
   - Never overwhelms or makes the learner feel self-conscious.

2. **Gentle Mistake Correction**
   - Automatically detects grammar, tense, preposition, and vocabulary mistakes.
   - Clean correction format:
     ```text
     ✏️ Correction:
     - ❌ wrong sentence → ✅ corrected sentence
     - 💡 Short explanation of the rule (1-2 sentences).
     ```
   - Only highlights the 1–3 most important mistakes. If there are no mistakes, gives encouraging praise (e.g., *"Perfect sentence! 👏"*).

3. **"Explain in Uzbek" (O'zbekcha tushuntirish)**
   - Includes an inline button `[🇺🇿 Explain in Uzbek / O'zbekcha tushuntirish]` under corrections.
   - Clicking it provides an instant, friendly explanation of the grammar rule in Uzbek.

4. **Vocabulary & Teaching**
   - Occasionally introduces `📚 New word/phrase` with simple definitions and examples.
   - Offers a mini-challenge / exercise every 5–7 messages based on recent mistakes.

5. **Voice Messages & Audio Input**
   - Learners can send voice messages!
   - Emma transcribes the speech, provides speaking/pronunciation tips, converses naturally, and provides grammar feedback.

6. **Adaptive Levels & Goals**
   - Levels: **A1** (Beginner), **A2** (Elementary), **B1** (Intermediate), **B2** (Upper-Intermediate), **C1** (Advanced).
   - Goals: Daily Conversation, Work & Career, Travel, IELTS / Exam Prep.
   - Correction Modes: `/standard`, `/strict`, `/relax`.

7. **Browser Web UI & Telegram Bot**
   - Both interfaces share the exact same database, memory, and Gemini engine.

---

## 📁 Project Structure

```text
├── bot/
│   ├── __init__.py
│   └── main.py              # Telegram bot runner & command configuration
├── handlers/
│   ├── __init__.py
│   ├── onboarding.py        # /start onboarding flow
│   ├── commands.py          # /level, /topic, /quiz, /summary, /strict, etc.
│   ├── callbacks.py         # Inline button handlers & Uzbek explanation
│   ├── chat.py              # Text message processing & reply pipeline
│   ├── voice.py             # Voice message transcription & feedback
│   └── keyboards.py         # Inline keyboards (levels, goals, topics)
├── services/
│   ├── __init__.py
│   ├── gemini_service.py    # Google GenAI SDK integration & prompt rendering
│   ├── parser.py            # Extraction of ❌/✅/💡 and 📚 vocabulary
│   └── rate_limiter.py      # Sliding window rate limiter
├── db/
│   ├── __init__.py
│   └── database.py          # SQLite manager (users, history, mistakes, vocab)
├── prompts/
│   ├── system_prompt.md     # Dynamic system prompt for Emma
│   ├── quiz_prompt.md       # 5-question personalized quiz generator
│   └── voice_prompt.md      # Voice transcription & speaking analysis
├── tests/
│   ├── test_database.py     # Database CRUD and history tests
│   ├── test_parser.py       # Correction & vocabulary parsing tests
│   ├── test_rate_limiter.py # Rate limiter sliding window tests
│   └── test_system_prompt.py# Dynamic system prompt compilation tests
├── web_app.py               # Modern Browser Web Interface for Emma
├── main.py                  # Telegram bot entrypoint
├── requirements.txt         # Dependencies
├── Dockerfile               # Production Docker container
├── .env.example             # Example environment variables
└── README.md                # Documentation
```

---

## 🤖 Bot Commands

| Command | Description | Uzbek Description |
|---|---|---|
| `/start` | Start or restart onboarding | Qayta boshlash va sozlash |
| `/level` | Select English level (A1–C1) | Darajani tanlash |
| `/topic` | Suggest 3 conversation topics | Suhbat mavzularini tanlash |
| `/quiz` | 5-question quiz on recent mistakes | Xatolar asosida mini-test |
| `/summary` | View mistakes and vocabulary learned | Xatolar va yangi so'zlar hisoboti |
| `/strict` | Strict mode (corrects all slips & punctuation) | Qattiqqo'l rejim |
| `/relax` | Relaxed mode (corrects only major errors) | Erkin suhbat rejimi |
| `/reset` | Clear chat history & memory | Suhbat xotirasini tozalash |
| `/help` | List commands with Uzbek explanations | Yordam qo'llanmasi |

---

## 🚀 Step-by-Step Setup

### 1. Prerequisites
- Python 3.11+
- Git

### 2. Clone and install dependencies
```bash
git clone <your-repository-url>
cd "ingliz suhbatdosh"

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.\.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Get your API Keys

#### A. Telegram Bot Token
1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Send `/newbot` and follow the instructions to name your bot (e.g. `EmmaEnglishTutorBot`).
3. Copy the HTTP API token provided by BotFather.

#### B. Google Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Sign in with your Google account.
3. Click **"Get API key"** and create a new API key.
4. Copy the key.

### 4. Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and fill in your keys:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstuVWXyz
GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere
MODEL_NAME=gemini-2.5-flash
PORT=8000
```

---

## 💻 Running the Application

### Option A: Run in your Web Browser (React + Tailwind CSS)
To talk to Emma directly in your browser:
```bash
python web_app.py
```
Then open:
👉 **`http://localhost:8000`** in Google Chrome or any browser.

#### For Frontend Developers (Hot-Reload with Vite):
```bash
# Terminal 1: Start backend server
python web_app.py

# Terminal 2: Start Vite React Dev Server
cd frontend
npm run dev
```
Open 👉 **`http://localhost:5173`** for instant hot-reloading.

Features in browser:
- Full interactive chat with Emma
- Clickable level & goal buttons
- Quick command shortcuts
- "Explain in Uzbek" buttons
- Voice recording via browser microphone

### Option B: Run the Telegram Bot
```bash
python main.py
```
Open Telegram, find your bot, and send `/start`!

---

## 🧪 Running Unit Tests

Run the test suite with pytest:
```bash
pytest -v
```

All 8 tests verify:
- Database creation, user settings, chat history, mistakes, and vocabulary logging.
- Parsing of ❌/✅/💡 corrections and 📚 vocabulary cards.
- Sliding-window rate limiter per user.
- Dynamic system prompt generation for various CEFR levels and correction modes.

---

## 🐳 Docker Deployment

### 1. Build Docker image
```bash
docker build -t emma-bot .
```

### 2. Run Telegram Bot with Docker
```bash
docker run -d --name emma-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  --restart unless-stopped \
  emma-bot
```

### 3. Run Web App with Docker
```bash
docker run -d --name emma-web \
  --env-file .env \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  --restart unless-stopped \
  emma-bot python web_app.py
```

---

## ☁️ Cloud Deployment (VPS, Railway, Render)

### Deploying on a Linux VPS (Ubuntu/Debian)
1. SSH into your VPS:
   ```bash
   ssh user@your-server-ip
   ```
2. Clone repo and set up Python:
   ```bash
   git clone <repo> && cd <repo>
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env # Edit with your keys
   ```
3. Set up a systemd service:
   Create `/etc/systemd/system/emma-bot.service`:
   ```ini
   [Unit]
   Description=Emma English Tutor Telegram Bot
   After=network.target

   [Service]
   Type=simple
   User=root
   WorkingDirectory=/path/to/ingliz suhbatdosh
   ExecStart=/path/to/ingliz suhbatdosh/.venv/bin/python main.py
   Restart=always
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```
4. Start and enable service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable emma-bot
   sudo systemctl start emma-bot
   ```

### Deploying on Railway
1. Push your repository to GitHub.
2. Log in to [Railway.app](https://railway.app/) and click **"New Project"** -> **"Deploy from GitHub repo"**.
3. Under **Variables**, add:
   - `TELEGRAM_BOT_TOKEN`
   - `GEMINI_API_KEY`
   - `MODEL_NAME` (`gemini-2.5-flash`)
4. Railway will automatically detect the Dockerfile or `requirements.txt` and launch Emma!

### Deploying on Render
1. Create a new **Background Worker** on [Render.com](https://render.com/).
2. Connect your repository.
3. Build Command: `pip install -r requirements.txt`.
4. Start Command: `python main.py`.
5. Add Environment Variables (`TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`).
6. Click **Deploy**.

