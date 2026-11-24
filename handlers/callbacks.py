from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from db.database import Database
from handlers.keyboards import get_goal_keyboard


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.data or not update.effective_user:
        return

    await query.answer()
    data = query.data
    user_id = update.effective_user.id
    db: Database = context.bot_data["db"]
    gemini = context.bot_data["gemini"]

    # 1. Level Selection
    if data.startswith("level:"):
        level = data.split(":", 1)[1]
        user = await db.get_user(user_id) or {}
        await db.update_user(user_id, level=level)

        if user.get("onboarding_state") == "awaiting_level":
            await db.update_user(user_id, onboarding_state="awaiting_goal")
            text = (
                f"Awesome! Level set to **{level}** 🎯\n\n"
                "Now, **what is your main English learning goal?**\n"
                "Please choose one below 👇"
            )
            try:
                await query.edit_message_text(text, reply_markup=get_goal_keyboard(), parse_mode=ParseMode.MARKDOWN)
            except Exception:
                await query.edit_message_text(text, reply_markup=get_goal_keyboard())
        else:
            msg = f"✅ Your English level has been updated to **{level}**! Let's continue practicing."
            try:
                await query.edit_message_text(msg, parse_mode=ParseMode.MARKDOWN)
            except Exception:
                await query.edit_message_text(msg)

    # 2. Goal Selection
    elif data.startswith("goal:"):
        goal = data.split(":", 1)[1]
        user = await db.get_user(user_id) or {}
        name = user.get("name") or "Friend"
        level = user.get("level") or "B1"
        await db.update_user(user_id, goal=goal, onboarding_state="completed")

        welcome_text = (
            f"Wonderful, {name}! 🎉\n\n"
            f"Your profile is ready:\n"
            f"• Level: **{level}**\n"
            f"• Goal: **{goal}**\n\n"
            f"I am ready whenever you are! You can type anything or ask me any question. "
            f"To get us started, **how has your day been going so far?**"
        )
        try:
            await query.edit_message_text(welcome_text, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await query.edit_message_text(welcome_text)

    # 3. Topic Selection
    elif data.startswith("topic:"):
        topic_key = data.split(":", 1)[1]
        topic_starters = {
            "hobbies": "Hobbies are a great way to unwind! 🎨 What is one hobby you really enjoy doing in your free time?",
            "travel": "I love traveling! ✈️ If you could visit any country in the world right now, where would you go and why?",
            "entertainment": "Movies and music bring so much joy! 🎬 Have you watched any good movies or listened to great music recently?",
            "career": "Setting ambitious goals is inspiring! 🚀 What is a personal or career goal you are working toward right now?"
        }
        starter_question = topic_starters.get(
            topic_key,
            "That's an interesting topic! What thoughts come to your mind first?"
        )
        await db.add_chat_message(user_id, "model", starter_question)
        try:
            await query.edit_message_text(starter_question, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await query.edit_message_text(starter_question)

    # 4. Uzbek Explanation
    elif data.startswith("uz_exp:"):
        mistake_id_str = data.split(":", 1)[1]
        try:
            mistake_id = int(mistake_id_str)
        except ValueError:
            mistake_id = 0

        explanation_uz = ""
        if mistake_id > 0:
            mistake = await db.get_mistake(mistake_id)
            if mistake:
                if mistake.get("explanation_uz"):
                    explanation_uz = mistake["explanation_uz"]
                else:
                    exp_en = mistake.get("explanation") or f"Original: {mistake.get('original_text')} -> Correct: {mistake.get('corrected_text')}"
                    explanation_uz = await gemini.translate_to_uzbek(exp_en)
                    await db.update_mistake_uzbek(mistake_id, explanation_uz)

        if not explanation_uz:
            explanation_uz = "Ushbu xato bo'yicha tushuntirish topilmadi."

        response_msg = (
            f"🇺🇿 **O'zbekcha tushuntirish:**\n\n"
            f"{explanation_uz}"
        )
        try:
            await query.message.reply_text(response_msg, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await query.message.reply_text(response_msg)

