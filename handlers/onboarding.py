from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from db.database import Database
from handlers.keyboards import get_level_keyboard


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message:
        return

    db: Database = context.bot_data["db"]
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name

    user = await db.get_or_create_user(user_id, username, first_name)
    await db.update_user(user_id, onboarding_state="awaiting_name")

    greeting = (
        "Hello! 👋 I'm **Emma**, your personal English conversation tutor.\n\n"
        "I'm here to help you practice English naturally, gently correct your mistakes, "
        "and teach you useful words along the way.\n\n"
        "To get started, **what is your name or what should I call you?**\n"
        "(Just reply with your name 👇)"
    )

    try:
        await update.message.reply_text(greeting, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await update.message.reply_text(greeting)

