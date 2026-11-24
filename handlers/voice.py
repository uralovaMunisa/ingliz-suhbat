from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import ContextTypes

from db.database import Database
from handlers.keyboards import get_correction_keyboard
from config import CHAT_HISTORY_LIMIT


async def voice_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message:
        return

    voice = update.message.voice or update.message.audio
    if not voice:
        return

    user_id = update.effective_user.id
    db: Database = context.bot_data["db"]
    gemini = context.bot_data["gemini"]
    rate_limiter = context.bot_data["rate_limiter"]

    # 1. Rate limiting check
    if not rate_limiter.is_allowed(user_id):
        wait_sec = rate_limiter.remaining_seconds(user_id)
        await update.message.reply_text(
            f"⏳ You are sending voice messages very quickly! Please wait {wait_sec} seconds before sending another."
        )
        return

    user = await db.get_or_create_user(
        user_id,
        update.effective_user.username,
        update.effective_user.first_name
    )

    # Send recording/typing indicator
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.RECORD_VOICE)
    except Exception:
        pass

    try:
        # Download voice audio file into memory
        tg_file = await context.bot.get_file(voice.file_id)
        audio_bytearray = await tg_file.download_as_bytearray()
        audio_bytes = bytes(audio_bytearray)
        mime_type = getattr(voice, "mime_type", None) or "audio/ogg"

        history = await db.get_recent_chat_history(user_id, limit=CHAT_HISTORY_LIMIT)
        result = await gemini.transcribe_and_reply_voice(user, history, audio_bytes, mime_type=mime_type)

        reply_text = result["text"]
        mistakes = result["mistakes"]
        vocab = result["vocabulary"]
        has_corrections = result["has_corrections"]

        # Store mistakes and get first mistake id
        first_mistake_id = None
        for m in mistakes:
            m_id = await db.log_mistake(user_id, m["original"], m["corrected"], m["explanation"])
            if first_mistake_id is None:
                first_mistake_id = m_id

        if vocab:
            await db.log_vocabulary(user_id, vocab["phrase"], vocab["definition"], vocab.get("example", ""))

        # Log to chat history
        await db.add_chat_message(user_id, "user", "[Voice Message]")
        await db.add_chat_message(user_id, "model", reply_text)

        reply_markup = None
        if has_corrections and first_mistake_id:
            reply_markup = get_correction_keyboard(first_mistake_id)

        try:
            await update.message.reply_text(reply_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await update.message.reply_text(reply_text, reply_markup=reply_markup)

    except Exception as e:
        await update.message.reply_text(
            f"Oops! I couldn't process your voice message. Error: {str(e)}\nCould you try typing your message or sending another voice clip?"
        )

