import os
import sys
import json
import base64
import asyncio
import mimetypes
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import config
from db.database import Database
from services.gemini_service import GeminiService
from services.rate_limiter import RateLimiter

db = Database(config.DATABASE_PATH)
gemini = GeminiService(config.GEMINI_API_KEY, config.MODEL_NAME)
rate_limiter = RateLimiter(config.RATE_LIMIT_COUNT, config.RATE_LIMIT_WINDOW_SECONDS)

# Ensure DB initialized
asyncio.run(db.init_db())

FRONTEND_DIST = root_dir / "frontend" / "dist"


class EmmaRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, data: dict):
        response_bytes = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(response_bytes)

    def _serve_file(self, file_path: Path):
        if not file_path.is_file():
            self.send_error(404, "File Not Found")
            return

        content_type, _ = mimetypes.guess_type(str(file_path))
        content_type = content_type or "application/octet-stream"

        with open(file_path, "rb") as f:
            data = f.read()

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        try:
            parsed = urllib.parse.urlparse(self.path)

            if parsed.path == "/api/user":
                params = urllib.parse.parse_qs(parsed.query)
                user_id = int(params.get("user_id", [1001])[0])
                user = asyncio.run(db.get_or_create_user(user_id, "browser_user", "Friend"))
                self._send_json(200, {"user": user})
                return

            elif parsed.path == "/api/vocabulary":
                params = urllib.parse.parse_qs(parsed.query)
                user_id = int(params.get("user_id", [1001])[0])
                vocab = asyncio.run(db.get_recent_vocabulary(user_id, limit=100))
                self._send_json(200, {"vocabulary": vocab})
                return

            elif parsed.path == "/api/mistakes":
                params = urllib.parse.parse_qs(parsed.query)
                user_id = int(params.get("user_id", [1001])[0])
                mistakes = asyncio.run(db.get_recent_mistakes(user_id, limit=50))
                self._send_json(200, {"mistakes": mistakes})
                return

            elif parsed.path == "/api/config":
                self._send_json(200, {
                    "has_key": gemini.is_configured(),
                    "model": gemini.model_name
                })
                return

            # Serve React frontend static files
            if FRONTEND_DIST.exists():
                relative_path = parsed.path.lstrip("/")
                target_file = FRONTEND_DIST / relative_path

                if not relative_path or parsed.path == "/":
                    target_file = FRONTEND_DIST / "index.html"

                if target_file.is_file():
                    self._serve_file(target_file)
                else:
                    self._serve_file(FRONTEND_DIST / "index.html")
            else:
                self.send_error(404, "Frontend dist not built. Run 'npm run build' inside frontend/")
        except Exception as e:
            self._send_json(500, {"error": str(e)})

    def do_POST(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            payload = json.loads(post_data.decode("utf-8")) if post_data else {}

            user_id = payload.get("user_id", 1001)
            user = asyncio.run(db.get_or_create_user(user_id, "browser_user", "Friend"))

            if parsed.path == "/api/set_key":
                new_key = payload.get("api_key", "").strip()
                if new_key:
                    gemini.set_api_key(new_key)
                    # Persist to .env
                    env_path = root_dir / ".env"
                    env_lines = []
                    if env_path.exists():
                        with open(env_path, "r", encoding="utf-8") as f:
                            env_lines = f.readlines()
                    updated = False
                    new_lines = []
                    for line in env_lines:
                        if line.startswith("GEMINI_API_KEY="):
                            new_lines.append(f"GEMINI_API_KEY={new_key}\n")
                            updated = True
                        else:
                            new_lines.append(line)
                    if not updated:
                        new_lines.append(f"GEMINI_API_KEY={new_key}\n")
                    with open(env_path, "w", encoding="utf-8") as f:
                        f.writelines(new_lines)

                    self._send_json(200, {"success": True, "has_key": gemini.is_configured()})
                else:
                    self._send_json(400, {"error": "Invalid API key"})
                return

            if parsed.path == "/api/chat":
                msg = payload.get("message", "").strip()

                # Handle interactive level buttons
                if msg.startswith("level:"):
                    lvl = msg.split(":", 1)[1]
                    asyncio.run(db.update_user(user_id, level=lvl))
                    self._send_json(200, {
                        "type": "interactive",
                        "text": f"Awesome! Level set to **{lvl}** 🎯\n\nNow, what is your main English learning goal?",
                        "buttons": [
                            {"text": "🗣 Daily Conversation", "action": "selectGoal('Daily conversation')"},
                            {"text": "💼 Work & Career", "action": "selectGoal('Work & Career')"},
                            {"text": "✈️ Travel", "action": "selectGoal('Travel')"},
                            {"text": "🎓 IELTS & Exams", "action": "selectGoal('IELTS & Exams')"}
                        ]
                    })
                    return

                # Handle interactive goal buttons
                if msg.startswith("goal:"):
                    g = msg.split(":", 1)[1]
                    asyncio.run(db.update_user(user_id, goal=g))
                    self._send_json(200, {
                        "type": "regular",
                        "text": f"Great! Your goal is set to **{g}**. Let's start practicing! How was your weekend? What did you do?"
                    })
                    return

                # Handle interactive topic buttons
                if msg.startswith("topic:"):
                    t = msg.split(":", 1)[1]
                    topic_prompts = {
                        "hobbies": "Hobbies make life interesting! 🎨 What is one hobby you really enjoy doing in your free time?",
                        "travel": "I love traveling! ✈️ If you could visit any country in the world right now, where would you go and why?",
                        "entertainment": "Movies and music bring so much joy! 🎬 Have you watched any good movies or listened to great music recently?",
                        "career": "Setting ambitious goals is inspiring! 🚀 What is a personal or career goal you are working toward right now?"
                    }
                    starter = topic_prompts.get(t, "Tell me about your favorite hobbies!")
                    self._send_json(200, {"type": "regular", "text": starter})
                    return

                # Handle special slash commands
                if msg == "/start":
                    self._send_json(200, {
                        "type": "interactive",
                        "text": "Hello! 👋 I'm **Emma**, your English conversation tutor.\n\nPlease select your English level below:",
                        "buttons": [
                            {"text": "A1 - Beginner 🟢", "action": "selectLevel('A1')"},
                            {"text": "A2 - Elementary 🟡", "action": "selectLevel('A2')"},
                            {"text": "B1 - Intermediate 🟠", "action": "selectLevel('B1')"},
                            {"text": "B2 - Upper-Int 🔵", "action": "selectLevel('B2')"},
                            {"text": "C1 - Advanced 🟣", "action": "selectLevel('C1')"}
                        ]
                    })
                    return

                if msg == "/level":
                    self._send_json(200, {
                        "type": "interactive",
                        "text": "📊 **Choose your English level:**",
                        "buttons": [
                            {"text": "A1 - Beginner 🟢", "action": "selectLevel('A1')"},
                            {"text": "A2 - Elementary 🟡", "action": "selectLevel('A2')"},
                            {"text": "B1 - Intermediate 🟠", "action": "selectLevel('B1')"},
                            {"text": "B2 - Upper-Int 🔵", "action": "selectLevel('B2')"},
                            {"text": "C1 - Advanced 🟣", "action": "selectLevel('C1')"}
                        ]
                    })
                    return

                if msg == "/topic":
                    self._send_json(200, {
                        "type": "interactive",
                        "text": "💡 **Choose a conversation topic to explore:**",
                        "buttons": [
                            {"text": "☕ Hobbies & Free Time", "action": "selectTopic('hobbies')"},
                            {"text": "✈️ Travel Memories", "action": "selectTopic('travel')"},
                            {"text": "🎬 Movies & Music", "action": "selectTopic('entertainment')"},
                            {"text": "🚀 Future Goals", "action": "selectTopic('career')"}
                        ]
                    })
                    return

                if msg == "/strict":
                    asyncio.run(db.update_user(user_id, correction_mode="strict"))
                    self._send_json(200, {"type": "regular", "text": "🎯 **Strict Mode Activated!** I will now correct every mistake, including punctuation and capitalization."})
                    return

                if msg == "/relax":
                    asyncio.run(db.update_user(user_id, correction_mode="relax"))
                    self._send_json(200, {"type": "regular", "text": "☕ **Relaxed Mode Activated!** I will only point out major mistakes so you can focus on fluency."})
                    return

                if msg == "/reset":
                    asyncio.run(db.clear_chat_history(user_id))
                    asyncio.run(db.reset_message_count(user_id))
                    self._send_json(200, {"type": "regular", "text": "🧹 **Conversation memory cleared!** What would you like to practice today?"})
                    return

                if msg == "/summary":
                    mistakes = asyncio.run(db.get_recent_mistakes(user_id, limit=5))
                    vocab = asyncio.run(db.get_recent_vocabulary(user_id, limit=5))
                    text_lines = [
                        f"📋 **Learning Summary for {user.get('name', 'Friend')}**",
                        f"• Level: {user.get('level', 'B1')}",
                        f"• Goal: {user.get('goal', 'Daily conversation')}",
                        f"• Mode: {user.get('correction_mode', 'standard').capitalize()}\n"
                    ]
                    if mistakes:
                        text_lines.append("✏️ **Recent Mistakes:**")
                        for m in mistakes:
                            text_lines.append(f"• ❌ {m['original_text']} → ✅ {m['corrected_text']}\n  💡 {m['explanation']}")
                    else:
                        text_lines.append("✏️ No recent mistakes recorded! 👏")
                    if vocab:
                        text_lines.append("\n📚 **New Vocabulary:**")
                        for v in vocab:
                            text_lines.append(f"• **{v['phrase']}**: {v['definition']}")
                    self._send_json(200, {"type": "regular", "text": "\n".join(text_lines)})
                    return

                if msg == "/quiz":
                    mistakes = asyncio.run(db.get_recent_mistakes(user_id, limit=10))
                    quiz_text = asyncio.run(gemini.generate_quiz(user, mistakes))
                    self._send_json(200, {"type": "regular", "text": quiz_text})
                    return

                if msg == "/help":
                    help_text = (
                        "🤖 **Emma Commands & Guide**\n\n"
                        "• /start - Restart onboarding & choose level\n"
                        "• /level - Switch your English level (A1-C1)\n"
                        "• /topic - Choose from 3 conversation topics\n"
                        "• /quiz - 5-question review quiz on your mistakes\n"
                        "• /summary - View your mistakes and new words summary\n"
                        "• /strict - Strict mode (correct every mistake)\n"
                        "• /relax - Relaxed mode (only major mistakes)\n"
                        "• /reset - Clear conversation history\n"
                        "• /help - Show this guide\n\n"
                        "🎙️ You can also click the microphone button to practice speaking!"
                    )
                    self._send_json(200, {"type": "regular", "text": help_text})
                    return

                # Regular conversation
                count = asyncio.run(db.increment_message_count(user_id))
                trigger_exercise = (count % 6 == 0)
                history = asyncio.run(db.get_recent_chat_history(user_id, limit=config.CHAT_HISTORY_LIMIT))

                result = asyncio.run(gemini.generate_reply(user, history, msg, trigger_exercise=trigger_exercise))

                # Store mistakes & vocab
                for m in result.get("mistakes", []):
                    asyncio.run(db.log_mistake(user_id, m["original"], m["corrected"], m["explanation"]))

                v = result.get("vocabulary")
                if v:
                    asyncio.run(db.log_vocabulary(user_id, v["phrase"], v["definition"], v.get("example", "")))

                asyncio.run(db.add_chat_message(user_id, "user", msg))
                asyncio.run(db.add_chat_message(user_id, "model", result.get("text", "")))

                self._send_json(200, {
                    "type": "regular",
                    "text": result.get("text", ""),
                    "mistakes": result.get("mistakes", []),
                    "vocabulary": result.get("vocabulary"),
                    "has_corrections": result.get("has_corrections", False)
                })

            elif parsed.path == "/api/voice":
                audio_b64 = payload.get("audio_base64", "")
                audio_bytes = base64.b64decode(audio_b64)
                mime_type = payload.get("mime_type", "audio/webm")

                history = asyncio.run(db.get_recent_chat_history(user_id, limit=config.CHAT_HISTORY_LIMIT))
                result = asyncio.run(gemini.transcribe_and_reply_voice(user, history, audio_bytes, mime_type=mime_type))

                for m in result.get("mistakes", []):
                    asyncio.run(db.log_mistake(user_id, m["original"], m["corrected"], m["explanation"]))

                v = result.get("vocabulary")
                if v:
                    asyncio.run(db.log_vocabulary(user_id, v["phrase"], v["definition"], v.get("example", "")))

                asyncio.run(db.add_chat_message(user_id, "user", "[Voice Message]"))
                asyncio.run(db.add_chat_message(user_id, "model", result.get("text", "")))

                self._send_json(200, {
                    "type": "regular",
                    "text": result.get("text", ""),
                    "mistakes": result.get("mistakes", []),
                    "vocabulary": result.get("vocabulary"),
                    "has_corrections": result.get("has_corrections", False)
                })

            elif parsed.path == "/api/translate_uz":
                text_to_translate = payload.get("text", "")
                translation = asyncio.run(gemini.translate_to_uzbek(text_to_translate))
                self._send_json(200, {"translation": translation})
            else:
                self.send_error(404, "Not Found")
        except Exception as e:
            self._send_json(500, {"error": str(e)})


def run_web_server(port=8000):
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, EmmaRequestHandler)
    print(f"Emma React Web Server running at http://127.0.0.1:{port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Stopping server...")
        httpd.server_close()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    run_web_server(port)
