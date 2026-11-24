from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import ContextTypes

from db.database import Database
from handlers.keyboards import get_level_keyboard, get_goal_keyboard, get_correction_keyboard
from config import CHAT_HISTORY_LIMIT


async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    text = update.message.text.strip()
    db: Database = context.bot_data["db"]
    gemini = context.bot_data["gemini"]
    rate_limiter = context.bot_data["rate_limiter"]

    # 1. Rate limiting check
    if not rate_limiter.is_allowed(user_id):
        wait_sec = rate_limiter.remaining_seconds(user_id)
        await update.message.reply_text(
            f"⏳ You are sending messages very quickly! Please wait {wait_sec} seconds before sending another message."
        )
        return

    user = await db.get_or_create_user(
        user_id,
        update.effective_user.username,
        update.effective_user.first_name
    )

    # 2. Check Onboarding Flow
    state = user.get("onboarding_state")
    if state == "awaiting_name":
        # The user provided their preferred name
        preferred_name = text.strip()
        await db.update_user(user_id, name=preferred_name, onboarding_state="awaiting_level")
        prompt = (
            f"It's so wonderful to meet you, **{preferred_name}**! 😊\n\n"
            "Now, could you tell me your current English level?\n"
            "Choose an option below 👇"
        )
        try:
            await update.message.reply_text(prompt, reply_markup=get_level_keyboard(), parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await update.message.reply_text(prompt, reply_markup=get_level_keyboard())
        return

    elif state == "awaiting_level":
        await update.message.reply_text(
            "Please select your English level from the buttons above! ☝️",
            reply_markup=get_level_keyboard()
        )
        return

    elif state == "awaiting_goal":
        await update.message.reply_text(
            "Please select your main English learning goal from the buttons above! ☝️",
            reply_markup=get_goal_keyboard()
        )
        return

    # 3. Regular Conversation Flow
    # Send typing indicator while generating response
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    except Exception:
        pass

    # Message counter for mini-challenges (every 5-7 messages)
    count = await db.increment_message_count(user_id)
    trigger_exercise = (count % 6 == 0)

    # Retrieve context
    history = await db.get_recent_chat_history(user_id, limit=CHAT_HISTORY_LIMIT)

    # Call Gemini service
    result = await gemini.generate_reply(user, history, text, trigger_exercise=trigger_exercise)
    reply_text = result["text"]
    mistakes = result["mistakes"]
    vocab = result["vocabulary"]
    has_corrections = result["has_corrections"]

    # Store mistakes in DB and record the first ID for the Uzbek explanation button
    first_mistake_id = None
    for m in mistakes:
        m_id = await db.log_mistake(user_id, m["original"], m["corrected"], m["explanation"])
        if first_mistake_id is None:
            first_mistake_id = m_id

    # Store vocabulary in DB
    if vocab:
        await db.log_vocabulary(user_id, vocab["phrase"], vocab["definition"], vocab.get("example", ""))

    # Save user and model messages in history
    await db.add_chat_message(user_id, "user", text)
    await db.add_chat_message(user_id, "model", reply_text)

    # Prepare markup if mistakes were identified
    reply_markup = None
    if has_corrections and first_mistake_id:
        reply_markup = get_correction_keyboard(first_mistake_id)

    # Send response safely
    try:
        await update.message.reply_text(
            reply_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception:
        # Fallback to plain text if Markdown parsing fails
        await update.message.reply_text(
            reply_text,
            reply_markup=reply_markup
        )

