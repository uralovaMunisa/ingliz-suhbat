import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types

from services.parser import ResponseParser


class GeminiService:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model_name = model_name or os.getenv("MODEL_NAME", "gemini-2.5-flash")

        self._init_client()

        prompts_dir = Path(__file__).resolve().parent.parent / "prompts"
        with open(prompts_dir / "system_prompt.md", "r", encoding="utf-8") as f:
            self.system_prompt_template = f.read()
        with open(prompts_dir / "quiz_prompt.md", "r", encoding="utf-8") as f:
            self.quiz_prompt_template = f.read()
        with open(prompts_dir / "voice_prompt.md", "r", encoding="utf-8") as f:
            self.voice_prompt_template = f.read()

    def _init_client(self):
        if self.api_key and not self.api_key.startswith("your_") and len(self.api_key) > 10:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception:
                self.client = None
        else:
            self.client = None

    def set_api_key(self, api_key: str):
        self.api_key = api_key
        self._init_client()

    def is_configured(self) -> bool:
        return bool(self.client and self.api_key and len(self.api_key) > 10)

    def build_system_prompt(self, user: Dict[str, Any], trigger_exercise: bool = False) -> str:
        name = user.get("name") or "Friend"
        level = (user.get("level") or "B1").upper()
        goal = user.get("goal") or "Daily conversation"
        mode = user.get("correction_mode") or "standard"

        level_descriptions = {
            "A1": "Beginner",
            "A2": "Elementary",
            "B1": "Intermediate",
            "B2": "Upper-Intermediate",
            "C1": "Advanced",
        }
        level_desc = level_descriptions.get(level, "Intermediate")

        level_instructions_map = {
            "A1": "- Use very short sentences (5-10 words).\n- Use simple, basic everyday words.\n- Speak slowly in text and avoid idioms.\n- Ask very simple questions.",
            "A2": "- Use short, simple sentences.\n- Stick to common daily words, past simple, and basic future.\n- Introduce 1 simple phrase with an explanation.",
            "B1": "- Use natural conversational speed and everyday vocabulary.\n- Occasionally introduce common idioms and explain them.\n- Talk about work, travel, hobbies, and plans.",
            "B2": "- Speak naturally with rich, varied vocabulary.\n- Use idioms, phrasal verbs, and slightly complex sentence structures.\n- Encourage deeper thoughts and opinions.",
            "C1": "- Use sophisticated, nuanced vocabulary, advanced idioms, and collocations.\n- Discuss complex, abstract, or professional topics.\n- Challenge their grammar precision and flow."
        }
        level_instructions = level_instructions_map.get(level, level_instructions_map["B1"])

        mode_instructions_map = {
            "strict": "- Strict Mode: Correct EVERY mistake, including grammar, vocabulary, prepositions, word-order, punctuation, and capitalization.",
            "relax": "- Relaxed Mode: Correct ONLY major mistakes that block understanding. Ignore minor slips.",
            "standard": "- Standard Mode: Correct only the 1-3 most important mistakes (grammar, tense, key prepositions/vocabulary). Ignore minor punctuation or capitalization."
        }
        mode_instructions = mode_instructions_map.get(mode, mode_instructions_map["standard"])

        exercise_instruction = ""
        if trigger_exercise:
            exercise_instruction = (
                "\n\n## Mini Challenge\n"
                "Offer a mini exercise at the very end of your message based on the learner's mistakes or level:\n"
                "🎯 **Mini-challenge:** [Write one quick exercise: fill in the blank, translate a short sentence, or rewrite a sentence]."
            )

        return self.system_prompt_template.format(
            name=name,
            level=level,
            level_description=level_desc,
            goal=goal,
            correction_mode=mode,
            level_instructions=level_instructions,
            mode_instructions=mode_instructions,
            exercise_instruction=exercise_instruction
        )

    def _generate_smart_offline_reply(self, user: Dict[str, Any], message: str) -> Dict[str, Any]:
        """Provides an intelligent, error-free conversation when Gemini API key is not yet set."""
        text_lower = message.lower().strip()
        name = user.get("name") or "Friend"
        level = user.get("level") or "B1"

        # Check for common mistakes
        mistakes = []
        if "i go to " in text_lower and any(w in text_lower for w in ["yesterday", "last", "ago", "morning"]):
            mistakes.append({
                "original": re.sub(r'(?i)i go to', 'I go to', message),
                "corrected": re.sub(r'(?i)i go to', 'I went to', message),
                "explanation": "Use past simple 'went' instead of 'go' for completed past actions."
            })
        elif "buyed" in text_lower:
            mistakes.append({
                "original": message,
                "corrected": message.replace("buyed", "bought"),
                "explanation": "'Buy' is an irregular verb: buy → bought, not buyed."
            })
        elif "she don't" in text_lower or "he don't" in text_lower:
            sub = "she don't" if "she don't" in text_lower else "he don't"
            corr = "she doesn't" if "she don't" in text_lower else "he doesn't"
            mistakes.append({
                "original": sub,
                "corrected": corr,
                "explanation": "For third-person singular (he/she/it), use 'doesn't' instead of 'don't'."
            })
        elif "i am agree" in text_lower:
            mistakes.append({
                "original": "I am agree",
                "corrected": "I agree",
                "explanation": "'Agree' is already a verb, so do not use 'am' with it."
            })
        elif "more better" in text_lower:
            mistakes.append({
                "original": "more better",
                "corrected": "much better",
                "explanation": "'Better' is already comparative. Use 'much better' or just 'better'."
            })
        elif "in monday" in text_lower or "in sunday" in text_lower or "in friday" in text_lower:
            day_match = re.search(r'in (monday|tuesday|wednesday|thursday|friday|saturday|sunday)', text_lower)
            if day_match:
                orig_day = day_match.group(0)
                corr_day = orig_day.replace("in ", "on ")
                mistakes.append({
                    "original": orig_day,
                    "corrected": corr_day,
                    "explanation": "We use the preposition 'on' with days of the week (e.g. on Monday)."
                })

        # Conversational reply mapping based on user keywords
        reply_body = ""
        vocab = None

        if any(w in text_lower for w in ["hello", "hi", "hey"]):
            reply_body = f"Hello {name}! It's so nice to chat with you today. How are you feeling right now?"
            vocab = {
                "phrase": "in good spirits",
                "definition": "feeling happy and energetic",
                "example": "I woke up in good spirits today."
            }
        elif any(w in text_lower for w in ["hobby", "free time", "relax"]):
            reply_body = "Hobbies are wonderful for mental health and creativity! What is your absolute favorite way to spend a quiet evening?"
            vocab = {
                "phrase": "to unwind",
                "definition": "to relax and release stress after work",
                "example": "Reading a book helps me unwind."
            }
        elif any(w in text_lower for w in ["travel", "country", "trip", "visit"]):
            reply_body = "Traveling teaches us so much about cultures and people! If you had a plane ticket right now, where would you fly?"
            vocab = {
                "phrase": "wanderlust",
                "definition": "a strong desire to travel the world",
                "example": "Her wanderlust led her to visit 30 countries."
            }
        elif any(w in text_lower for w in ["work", "job", "career", "study", "ielts"]):
            reply_body = "Staying focused on your professional and learning goals is very admirable. What is the most exciting project or skill you are working on lately?"
            vocab = {
                "phrase": "to hit the ground running",
                "definition": "to start something energetically and with immediate success",
                "example": "He hit the ground running in his new job."
            }
        elif any(w in text_lower for w in ["movie", "music", "book", "song"]):
            reply_body = "Entertainment makes language learning so enjoyable! What is a movie, series, or song that you recently loved?"
            vocab = {
                "phrase": "a masterpiece",
                "definition": "an outstanding piece of art, music, or literature",
                "example": "The movie was a true masterpiece."
            }
        else:
            reply_body = f"That is really interesting, {name}! Practicing speaking about everyday topics is the fastest way to become fluent. Could you tell me a little more about that?"
            vocab = {
                "phrase": "step by step",
                "definition": "gradually and steadily moving forward",
                "example": "You improve your English step by step."
            }

        # Build formatted text
        lines = [reply_body, ""]
        if mistakes:
            lines.append("✏️ **Correction:**")
            for m in mistakes:
                lines.append(f"- ❌ *{m['original']}* → ✅ *{m['corrected']}*")
                lines.append(f"- 💡 {m['explanation']}")
            lines.append("")
        else:
            lines.append("✏️ **Correction:**")
            lines.append("- 👏 Perfect sentence! No mistakes.\n")

        if vocab:
            lines.append(f"📚 **New phrase:** \"{vocab['phrase']}\" = {vocab['definition']}. *Example: {vocab['example']}*")

        return {
            "text": "\n".join(lines),
            "mistakes": mistakes,
            "vocabulary": vocab,
            "has_corrections": bool(mistakes)
        }

    async def generate_reply(
        self,
        user: Dict[str, Any],
        history: List[Dict[str, Any]],
        message: str,
        trigger_exercise: bool = False
    ) -> Dict[str, Any]:
        # If API key is not configured, gracefully use the smart tutor offline engine
        if not self.is_configured():
            return self._generate_smart_offline_reply(user, message)

        system_instruction = self.build_system_prompt(user, trigger_exercise)

        # Build contents from history
        contents = []
        for item in history:
            role = "user" if item["role"] == "user" else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=item["content"])]
                )
            )

        # Append current user message
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=message)]
            )
        )

        try:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
            )
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )

            response_text = response.text or ""
            mistakes = ResponseParser.extract_mistakes(response_text)
            vocab = ResponseParser.extract_vocabulary(response_text)
            has_corrections = ResponseParser.has_corrections(response_text)

            return {
                "text": response_text,
                "mistakes": mistakes,
                "vocabulary": vocab,
                "has_corrections": has_corrections
            }
        except Exception:
            # Fallback gracefully to smart offline reply on any API error or quota limit
            return self._generate_smart_offline_reply(user, message)

    async def transcribe_and_reply_voice(
        self,
        user: Dict[str, Any],
        history: List[Dict[str, Any]],
        audio_bytes: bytes,
        mime_type: str = "audio/webm"
    ) -> Dict[str, Any]:
        if not self.is_configured():
            return self._generate_smart_offline_reply(user, "Hello Emma, I sent a voice message!")

        name = user.get("name") or "Friend"
        level = (user.get("level") or "B1").upper()
        goal = user.get("goal") or "Daily conversation"
        mode = user.get("correction_mode") or "standard"

        voice_system_prompt = self.voice_prompt_template.format(
            name=name,
            level=level,
            goal=goal,
            correction_mode=mode
        )

        contents = []
        for item in history[-6:]:
            role = "user" if item["role"] == "user" else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=item["content"])]
                )
            )

        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
        instruction_part = types.Part.from_text(text="Listen to this voice recording, transcribe it, analyze it, and respond according to your instructions.")

        contents.append(
            types.Content(
                role="user",
                parts=[audio_part, instruction_part]
            )
        )

        try:
            config = types.GenerateContentConfig(
                system_instruction=voice_system_prompt,
                temperature=0.7,
            )
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )

            response_text = response.text or ""
            mistakes = ResponseParser.extract_mistakes(response_text)
            vocab = ResponseParser.extract_vocabulary(response_text)
            has_corrections = ResponseParser.has_corrections(response_text)

            return {
                "text": response_text,
                "mistakes": mistakes,
                "vocabulary": vocab,
                "has_corrections": has_corrections
            }
        except Exception:
            return self._generate_smart_offline_reply(user, "I sent a voice recording.")

    async def generate_quiz(self, user: Dict[str, Any], recent_mistakes: List[Dict[str, Any]]) -> str:
        level = user.get("level") or "B1"
        name = user.get("name") or "Friend"

        if not self.is_configured():
            return (
                f"🎲 **5-Question Review Quiz for {name} ({level} Level)**\n\n"
                "1. Choose the correct past tense: Yesterday I _____ (go / went / goed) to the library.\n"
                "2. She _____ (don't / doesn't) like coffee in the morning.\n"
                "3. I _____ (am agree / agree) with your opinion.\n"
                "4. We usually have our English lesson _____ (in / on / at) Friday.\n"
                "5. This new method is _____ (more better / much better / gooder) than the old one.\n\n"
                "💡 *Answers: 1. went, 2. doesn't, 3. agree, 4. on, 5. much better*"
            )

        if recent_mistakes:
            mistakes_text = "\n".join([
                f"- Wrong: {m['original_text']} -> Correct: {m['corrected_text']} (Rule: {m['explanation']})"
                for m in recent_mistakes[:10]
            ])
        else:
            mistakes_text = "Generate a general English quiz suitable for this level."

        prompt = self.quiz_prompt_template.format(
            level=level,
            name=name,
            mistakes_context=mistakes_text
        )

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            return response.text or "Could not generate quiz at this time."
        except Exception:
            return (
                f"🎲 **5-Question Review Quiz ({level} Level)**\n\n"
                "1. Yesterday I _____ (went / go) to the market.\n"
                "2. He _____ (doesn't / don't) play tennis.\n"
                "3. I am looking forward to _____ (meet / meeting) you.\n"
                "4. We meet _____ (on / at) 5 PM.\n"
                "5. She is good _____ (at / in) English.\n\n"
                "💡 *Answers: 1. went, 2. doesn't, 3. meeting, 4. at, 5. at*"
            )

    async def translate_to_uzbek(self, text: str) -> str:
        if not self.is_configured():
            # Quick rule translations for offline mode
            lower = text.lower()
            if "past simple" in lower or "went" in lower:
                return "Tugallangan o'tgan zamondagi ish-harakatlar uchun fe'lning o'tgan zamon shakli (Past Simple: go → went) ishlatiladi."
            elif "doesn't" in lower or "third-person" in lower:
                return "Uchinchi shaxs birlikda (he/she/it) inkor shaklida 'don't' emas, balki 'doesn't' ishlatiladi."
            elif "agree" in lower:
                return "'Agree' so'zi sifat emas, fe'l hisoblanadi. Shuning uchun 'I am agree' emas, to'g'ridan-to'g'ri 'I agree' (men qo'shilaman) deb aytiladi."
            elif "on monday" in lower or "preposition" in lower:
                return "Hafta kunlari bilan birga 'in' emas, balki 'on' predlogi ishlatiladi (masalan: on Monday)."
            else:
                return f"Qoida mazmuni: Ushbu jumlada to'g'ri grammatika shaklidan foydalanish lozim. Misol: {text}"

        prompt = (
            "You are a helpful language assistant. Translate this English grammar or vocabulary explanation "
            "into clear, friendly, and natural Uzbek for an English learner. Keep the explanation concise and easy to understand.\n\n"
            f"Explanation to translate:\n{text}\n\n"
            "Uzbek translation:"
        )

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            return response.text or "Tarjimani olishda xatolik yuz berdi."
        except Exception:
            return "Qoida: O'tgan zamon yoki to'g'ri predlog shaklidan foydalanish zarur."
